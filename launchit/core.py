"""
Basic functionality to launch files and commands.
"""
from itertools import chain
import os
import shlex
import subprocess
import sys

### Exceptions ###

class LaunchError(Exception):
    """
    Used to indicate that a given file or command could not be launched.
    """
    pass

class XDGOpenError(Exception):
    """
    Used to indicate that the command "xdg-open" could not be invoked.
    """
    pass

### Constants ###

# Encoding used when unicode/bytes must be converted to strings
ENCODING = 'utf-8'

# Readable helper when checking exit code 
EXIT_SUCCESS = 0

### Compatibility stuff ###

if sys.version_info >= (3,0):
    basestring = (str, bytes)
    def _to_native_string(obj):
        return obj.decode(ENCODING) if isinstance(obj, bytes) else str(obj)
else:
    def _to_native_string(obj):
        return obj.encode(ENCODING) if isinstance(obj, unicode) else str(obj)

### High-level functions ###

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
        names = set(chain.from_iterable(map(os.listdir, dirnames)))
    if os.path.basename(fragment):
        names = (name for name in names if fragment in name)
    return sorted(names)

def launch(cmdline, skip_xdg_open=False):
    """
    Analyze given command-line string and make the most reasonable kind of
    invocation on it.

    When a command is detected (first argument refers to existing application
    name in one of the directories defined by the PATH environment variable),
    it will be executed. Otherwise, if `cmdline` consists of exactly one
    argument, that argument is interpreted as a path name, which is then meant
    to be launched with the user's preferred application using "xdg-open". If
    that step failed or if `cmdline` contains more than one argument, then the
    arguments are treated as something that should be executed inside the
    current directory. To do so, the first argument will be converted to an
    absolute path name and then be invoked if possible. In case that finally
    none of this succeeded, a `LaunchError` will be raised.

    Note that "xdg-open" detection may be skipped in order to force the
    execution of scripts. Users may also want to quote path names, which
    contain whitespace characters. Furthermore, "~" and "~home" in a path
    are understood and expanded to the user's home directory. It sometimes
    might be useful to specify a directory component to avoid name clashes,
    e.g. things like "./test" instead of "test", but beware that "./test.py"
    will not necessarily execute the script (as noted above).
    """
    args = parse_commandline(cmdline)
    if not args:
        raise ValueError('Got no arguments, so nothing is launched')
    # Trial and error through the kinds of invocation
    success = False
    if is_command(args[0]):
        subprocess.call(args)
        success = True
    if not success and not skip_xdg_open and len(args) == 1:
        with open(os.devnull, 'w') as null:
            success = xdg_open(args[0], null, null) == EXIT_SUCCESS
    if not success and is_executable_file(args[0]):
        args[0] = os.path.abspath(args[0])
        subprocess.call(args)
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

def get_path_dirs():
    """
    Parse the environment variable PATH and return a list of all names
    that refer to an existing directory. An empty list will be returned
    if no suitable name could be obtained.
    """
    names = os.getenv('PATH', '').split(os.pathsep)
    return [name for name in names if os.path.isdir(name)]

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
    cmdline = _to_native_string(cmdline)
    return [os.path.expanduser(arg) for arg in shlex.split(cmdline)]

def is_command(filename):
    """
    Return True if given filename exists in at least one of the directories
    defined inside the environment variable PATH, otherwise False. If
    filename contains a path seperator, False will be returned, too.
    """
    if os.path.dirname(filename) or not filename:
        return False
    for dirname in get_path_dirs():
        path = os.path.join(dirname, filename)
        if os.path.exists(path):
            return True
    return False

def xdg_open(path, output_dest=None, error_dest=None):
    """
    Run the command "xdg-open" with given path and return its exit code.

    If redirection of output is needed, a file descriptor or a file object
    may be passed as a destination for the desired stream. The default
    value None means using the file descriptor of the parent process.

    Note that this function of course requires the "xdg-open" tool to be
    installed on the user's system in order to work. When unable to call
    it, a `XDGOpenError` is raised.
    """
    # TODO: Make detection work on non-linux systems (with no xdg-open)
    try:
        exit_code = subprocess.call(['xdg-open', path],
                                    stdout=output_dest,
                                    stderr=error_dest)
    except OSError:
        raise XDGOpenError('Unable to run xdg-open')
    return exit_code

def is_executable_file(path):
    """
    Return True if given path refers to a non-empty executable file,
    otherwise False.
    """
    return (os.access(path, os.X_OK) and
            os.path.isfile(path) and
            os.path.getsize(path) > 0)
