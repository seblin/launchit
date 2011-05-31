"""
Detect a command's associated starter icon by analyzing the user's menu 
entries. Note that this module depends on PyXDG.
"""
# Stdlib
import glob
import os
import shlex
import warnings

# 3rd party
import xdg.Menu

# launchit package
from . import settings
from ._stringutils import (
    altstring, basestring, to_alternate_string, to_native_string)
from .core import is_command

# Directory that contains the desktop environment's `.menu`-files
MENU_DIR = settings.config['menu-dir']

icon_cache = {}

def get_starter_icon(command, use_cache=True):
    """
    Return the associated icon for a given command. This is done by 
    analyzing the starter entries of the user's menu files: If the 
    command appears inside an entry, its icon's file name is returned, 
    otherwise None is returned. The command may be given as a name 
    (`firefox`) or as a path (`/usr/bin/firefox`).

    Note that this function may take a while to analyze all menu 
    entries. To speed this up, the icon names are cached, unless 
    `use_cache` is False. In fact, using the cache means that the 
    function will look for contents inside that cache when invoked. 
    If it sees an empty cache (e.g. right after the module has been 
    initialized) the cache will be filled using the results of 
    `iter_command_icons()`. These cached results are used for any 
    later call. The cache may be rebuilt via `init_icon_cache()`, 
    if needed.
    """
    if not isinstance(command, basestring):
        raise TypeError('command must be a string')
    if use_cache:
        if not icon_cache:
            init_icon_cache()
        icons = icon_cache
    else:
        icons = dict(iter_command_icons())
    if is_command(command):
        command = os.path.basename(command)
    try:
        icon = icons[command]
    except KeyError:
        return None
    if isinstance(command, altstring):
        icon = to_alternate_string(icon)
    return icon

def init_icon_cache():
    """
    (Re-)Initialize the cache used to guess the icon for a given command.
    """
    icons = iter_command_icons()
    icon_cache.clear()
    icon_cache.update(icons)

def iter_command_icons():
    """
    Analyze the user's menu entries and return an iterator, which 
    contains the associated command and its icon file for each entry 
    as tuples in the form `(command, icon)`. Note that if a command 
    refers to an existing file inside one of the directories defined 
    by the environment variable PATH and if that command is given as 
    an absolute path, it will be shortened to its file name (e.g. 
    `/usr/bin/firefox` => `firefox`).
    """
    for menu in iter_menu_files():
        for entry in iter_desktop_entries(menu):
            exec_ = to_native_string(entry.getExec())
            cmd = shlex.split(exec_)[0]
            if is_command(cmd):
                cmd = os.path.basename(cmd)
            icon = to_native_string(entry.getIcon())
            yield (cmd, icon)

# PyXDG-related helper functions

def iter_menu_files():
    """
    Iterate through the `.menu`-files found in the globally defined 
    MENU_DIR and yield a `xdg.Menu.Menu` object for each file. Each 
    of those objects will then contain the `.menu`-file's entries in 
    a parsed structure.
    """
    menu_files = os.path.join(MENU_DIR, '*.menu')
    for menu_file in glob.glob(menu_files):
        with warnings.catch_warnings():
            # Suppress a warning that may occur, when parsing KDE entries
            warnings.filterwarnings('ignore', 'os.popen3() is deprecated')
            yield xdg.Menu.parse(menu_file)

def iter_desktop_entries(menu):
    """
    Walk through given `xdg.Menu.Menu` object and its submenus. 
    Yield any appearing desktop entry (i.e. a program starter). 
    Note that examination is done recursively: If the function 
    encounters a submenu, it will iterate through the entries of 
    that submenu before dealing with the entries, which remain 
    inside the parent menu.
    """
    for entry in menu.getEntries():
        if isinstance(entry, xdg.Menu.MenuEntry):
            yield entry.DesktopEntry
        elif isinstance(entry, xdg.Menu.Menu):
            # Entry is a submenu
            for desktop_entry in iter_desktop_entries(entry):
                yield desktop_entry
        # (Other types are ignored)
