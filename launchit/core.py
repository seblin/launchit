"""
Basic functionality to launch files and commands.
"""
from itertools import chain
import os
import shlex
import subprocess

# launchit package
from ._stringutils import altstring, basestring, convert, ENCODING
from . import settings

class LaunchError(Exception):
    """
    Used to indicate that a given file or command could not be launched.
    """
    pass

# Readable helper when checking exit code
EXIT_SUCCESS = 0

# The tool used to open a file in the "preferred way"
STARTER = settings.config['starter']

### High-level functions

def get_name_completions(fragment=''):
    """
    Return matching (path-)names based on given fragment.

    If fragment contains a path seperator, everything prior to the
    last seperator is interpreted as the directory whose contents
    should be taken. Otherwise the directories defined inside the
    PATH environment variable and the current directory are used
    instead for that. Furthermore, fragment will be used to filter
    only those names, which contain the fragment as a substring.
    An empty fragment will keep the names unfiltered.

    Note that the resulting list is sorted and possible duplicates
    will be removed. An empty list is returned, when no matching
    name was found. If fragment contains a preceding dirname, it
    is kept in original spelling when completed, although "~" and
    "~home" are internally expanded to the user's home directory.
    Non-existing dirnames are silently ignored.
    """
    dirname = os.path.dirname(fragment)
    if dirname:
        expanded = os.path.expanduser(dirname)
        if not os.path.isdir(expanded):
            return []
        names = (os.path.join(dirname, name) for name in os.listdir(expanded))
    else:
        dirnames = get_path_dirs() + [os.curdir]
        if isinstance(fragment, altstring):
            dirnames = (convert(dirname, altstring) for dirname in dirnames)
        names = set(chain.from_iterable(map(os.listdir, dirnames)))
    if os.path.basename(fragment):
        names = (name for name in names if fragment in name)
    return sorted(names)

def launch(cmdline, skip_starter=False):
    """
    Analyze given command-line string and make the most reasonable kind of
    invocation on it.

    When a command is detected (first argument refers to existing application
    name in one of the directories defined by the PATH environment variable),
    it will be executed. Otherwise, if `cmdline` consists of exactly one
    argument, that argument is interpreted as a path name, which is then meant
    to be launched with the user's preferred application by use of the function 
    `open_with_starter()`. If that step failed or if `cmdline` contains more 
    than one argument, then the arguments are treated as something that should 
    be executed inside the current directory. To do so, the first argument will 
    be converted to an absolute path name and then be invoked if possible. In 
    case that finally none of this succeeded, a `LaunchError` will be raised.

    Note that the "starter step" may be skipped in order to force the execution 
    of scripts (as most starters would open an editor instead). Users may also 
    want to quote path names, which contain whitespace characters. Furthermore, 
    "~" and "~home" in a path are understood and expanded to the user's home 
    directory. It sometimes might be useful to specify a directory component to 
    avoid name clashes, e.g. things like "./test" instead of "test", but beware 
    that "./test.py" will not necessarily execute the script (as noted above).
    """
    args = parse_commandline(cmdline)
    if not args:
        raise ValueError('Got no arguments, so nothing is launched')
    # Trial and error through the kinds of invocation
    success = False
    if is_command(args[0]):
        subprocess.Popen(args)
        success = True
    if not success and not skip_starter and len(args) == 1:
        success = open_with_starter(args[0], silent=True) == EXIT_SUCCESS
    if not success and is_executable_file(args[0]):
        args[0] = os.path.abspath(args[0])
        subprocess.Popen(args)
        success = True
    if not success:
        error = 'Unable to launch {0}'.format(' '.join(args))
        raise LaunchError(error)

def get_marked_completion(completion, fragment, start_mark, end_mark):
    """
    Replace each occurrence of given fragment with the fragment surrounded
    by start_mark and end_mark. A mark may be e.g. a HTML tag or a terminal
    escape sequence.
    """
    marked_fragment = start_mark + fragment + end_mark
    return completion.replace(fragment, marked_fragment)

### Low-level functions

def splitenv(varname):
    """
    Get the environment variable `varname`s contents and split them at their
    platform-dependent path separator (`:` on POSIX, `;` on Windows). Return 
    the result as a list, which may be empty if there is no content.
    """
    return os.getenv(varname, '').split(os.pathsep)

def get_path_dirs():
    """
    Parse the environment variable PATH and return a list of all names
    that refer to an existing directory. An empty list will be returned
    if no suitable name could be obtained.
    """
    return [name for name in splitenv('PATH') if os.path.isdir(name)]

def parse_commandline(cmdline):
    """
    Split given cmdline string into a list of arguments matching Unix-like
    shell behavior. Return an empty list if no arguments remain after that.
    Complain about syntax errors.

    Note that each "~" or "~home" at the start of an argument is understood
    and expanded to the user's home directory. Any other type of expansion
    is not supported.
    """
    if not isinstance(cmdline, basestring):
        raise TypeError('cmdline must be a string')
    # Work around shlex.split() limitations
    native_cmdline = convert(cmdline, str)
    args = [os.path.expanduser(arg) for arg in shlex.split(native_cmdline)]
    # Re-convert if needed
    if isinstance(cmdline, altstring):
        args = [convert(arg, altstring) for arg in args]
    return args

def get_trimmed(path):
    """
    Trim a path, if possible, meaning that if `path` is recognized as a 
    command, it is shortened to its basename. Otherwise `path` is returned
    unchanged. In the latter case `path` must not necessarily refer to an
    existing file, since no further checks are made on it.

    Note that this function expects the given path to be of a string-type. 
    If not, an exception is raised by one of its underlying functions.
    """
    if is_command(path):
        path = os.path.basename(path)
    return path

def is_command(name):
    """
    Return True if given name refers to an existing file in one of the
    directories defined inside the environment variable PATH, otherwise
    False. The given name may be a filename or an absolute path.
    """
    dirname, basename = os.path.split(name)
    if not basename:
        return False
    path_dirs = get_path_dirs()
    if dirname:
        if dirname in path_dirs:
            return os.path.isfile(name)
        else:
            return False
    else:
        for path_dir in path_dirs:
            path = os.path.join(path_dir, basename)
            if os.path.isfile(path):
                return True
    return False

def open_with_starter(path, silent=False):
    """
    Invoke pre-defined starter with given path and return its exit code.
    The `silent`-flag may be used to suppress the program's output. 

    Note that the starter is defined inside `launchit.settings.config`
    and may be changed, if needed.
    """
    args = [STARTER, path]
    if silent:
        with open(os.devnull, 'wb') as null:
            exit_code = subprocess.call(args, stdout=null, stderr=null)
    else:
        exit_code = subprocess.call(args)
    return exit_code

def is_executable_file(path):
    """
    Return True if given path refers to a non-empty executable file,
    otherwise False.
    """
    return (os.access(path, os.X_OK) and
            os.path.isfile(path) and
            os.path.getsize(path) > 0)
