"""
Configuration stuff.
"""
# Stdlib
import os
# 3rd party
from xdg.BaseDirectory import xdg_config_home
# Launchit package
from . import logger

# Default configuration
config = {
    'encoding': 'utf-8',
    'icon-theme': None,
    'menu-dir': '/etc/xdg/menus',
    'starter' : 'xdg-open',
}

CONFIG_FILENAME = 'launchit.conf'

def update_config(configuration={}):
    """
    Update default configuration with the result of `get_user_config()` and 
    after that with the given `configuration`-dictionary. 

    "Updating" means: If the same key exists in at least two dictionaries,
    then the latter one's value is used. Otherwise the key is just added.
    Thus, an empty dictionary will result in no change.
    """
    for cfg in (get_user_config(), configuration):
        config.update(cfg)

def get_user_config(filename=None):
    """
    Return the parsed contents of a configuration file, which is named with
    `filename`, as a dictionary, where the file is assumed to exist inside 
    the user's "standard" configuration directory. In case that no such file
    could be found, an empty dictionary will be returned. If `filename` is 
    `None`, the `CONFIG_FILENAME` is used.

    Note that a detailed explanation of the expected scheme inside the config
    file can be found in `iter_config_entries()`, while the config file's path 
    is retrieved by `get_config_path()`.
    """
    if filename is None:
        filename = CONFIG_FILENAME
    path = get_config_path(filename)
    if not os.path.exists(path):
        return {}
    logger.info('Found config file {0!r}'.format(path))
    return get_config_entries(path)

def get_config_path(filename=None):
    """
    Return a XDG-compliant path based on given `filename`. If `filename` is 
    `None`, the `CONFIG_FILENAME` will be used.
    """
    # TODO: Determinate the correct path on non-linux platforms, too
    if filename is None:
        filename = CONFIG_FILENAME
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
    Iterate over the given configuration lines, which may be either a file-like
    object or a list of strings and return a `(key, value)`-pair for each line.
    Parsing is done according to the following rules: 

    Each line must use the scheme `key: value` to define an item. If a line 
    contains multiple `:`-chars, then the first one disappears, as it is used 
    as the separator, while the other ones will remain inside the value entry,
    which consequently means that only one item per line can be defined. Lines
    are read until a `#` appears, since that is interpreted as the beginning of 
    a comment. Whitespace at the beginning or at the end of a line is ignored. 
    The same goes for whitespace between key/value and separator. Empty lines 
    are just ignored, while a line with non-whitespaced contents, which doesn't 
    contain the separator, is an error. Note that keys and values will always 
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
