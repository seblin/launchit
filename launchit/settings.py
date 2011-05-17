"""
Configuration stuff.
"""
# Stdlib
import os
# 3rd party
from xdg.BaseDirectory import xdg_config_home

def get_user_config(filename='launchit.conf'):
    """
    Return the parsed contents of a configuration file, which is named with
    `filename`, as a dictionary, where the file is assumed to exist inside 
    the user's "standard" configuration directory. In case that the file 
    does not exist there, an empty dictionary will be returned.
    """
    path = get_config_path(filename)
    if not os.path.exists(path):
        return {}
    return get_config_entries(path)

def get_config_path(filename):
    """
    Return a XDG-compliant path pointing to the place where the given 
    configuration file should be stored.
    """
    # TODO: Determinate the correct path on non-linux platforms, too
    if os.path.dirname(filename):
        raise ValueError('filename may not contain any path separator')
    return os.path.join(xdg_config_home, filename)

def get_config_entries(path):
    """
    Read a configuration file from the given path and return a dictionary, 
    which contains the file's entries. 
    """
    with open(path) as config_file:
        return dict(iter_config_entries(config_file))

def iter_config_entries(lines):
    """
    Iterate over `lines`, which might be a file-like object or a list of 
    strings and return a `(key, value)`-pair for each line. Parsing is done 
    according to the following rules: 

    Each line must use the scheme `key: value` to define an item. If a line 
    contains multiple `:`-chars, then the first one disappears, as it is used 
    as the separator, while the other ones will remain inside the value entry,
    which consequently means that only one item per line can be defined. Lines
    are read until a `#` appears, since that is interpreted as the beginning of 
    a comment. Whitespace at the beginning or at the end of a line is ignored. 
    The same goes for whitespace between key/value and separator. Empty lines 
    are ignored either, while lines with non-whitespaced contents, which don't 
    contain the separator, are an error. Note that keys and values will always 
    be strings.
    """
    for index, line in enumerate(lines):
        code = line.split('#')[0].strip()
        if code: 
            if not ':' in code:
                msg = 'Syntax error in line {0}: Expected a separator (`:`)'
                raise ValueError(msg.format(index + 1))
            key, value = code.split(':', 1)
            yield (key.strip(), value.strip())
