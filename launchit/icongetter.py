"""
Detect suitable command icons.
"""
# Stdlib
import glob
import os
import warnings

# 3rd party
import xdg.IconTheme
import xdg.Menu
import xdg.Mime

# Launchit package
from . import settings
from ._stringutils import convert, keep_string_type
from .core import get_command_path, get_trimmed, parse_commandline

ICON_RUN = 'system-run'

@keep_string_type
def get_icon_path(icon_name, size=48, theme=None):
    """
    Return a path, which refers to an icon file with the given name 
    regarding to given `size` and `theme`. Return `None` if no icon
    path could be obtained.

    Note that `theme` may be set to `None`. It is then retrieved via 
    launchit's internal config dict (`settings.config['theme-name']`).
    """
    if os.path.isabs(icon_name):
        # Work around strange PyXDG behavior, 
        # which would return an absolute path
        # unchanged (for whatever reason)
        return None
    if theme is None:
        theme = settings.config['icon-theme']
    return xdg.IconTheme.getIconPath(icon_name, size, theme)

@keep_string_type
def guess_icon_name(command, split_args=True, theme=None, fallback=ICON_RUN):
    """
    Return a suitable icon name for the given `command`. 

    If the command appears in one of the user's menu entries, then 
    return the icon name for that entry. Otherwise return a generic 
    icon name depending on the MIME-type of `command`. In case that 
    no association could be made, `fallback` will be returned instead.

    If `split_args` is `True`, then POSIX-like shell-parsing is done
    in order to split `command` into arguments. The resulting first 
    argument will be used to guess the icon name.

    Note that any resulting icon name is checked, whether it exists 
    in the given `theme` by calling `get_icon_path()` on it. If the
    theme does not contain the name, the next "namegetter" is used
    (keeping the order as described above). Only the `fallback` icon 
    itself (as the last resort) is returned without any checks.
    """
    if not command:
        return fallback
    if split_args:
        args = parse_commandline(command)
        if not args:
            return fallback
        else:
            command = args[0]
    cmd_path = get_command_path(command) or command
    for namegetter in (guess_starter_icon, get_mimetype_name):
        name = namegetter(cmd_path)
        if name and get_icon_path(name, theme=theme):
            return name
    return fallback

@keep_string_type
def guess_starter_icon(command, use_cache=True):
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
    try:
        icon = icons[get_trimmed(command)]
    except KeyError:
        return None
    return icon

@keep_string_type
def get_mimetype_name(filename):
    """
    Return an icon name corresponding to the given `filename`s MIME-type. 
    Return `None` if no MIME-type could be determined. 

    Note that this just returns a name in the form `mediatype-subtype`.
    It does not check whether there really *is* an existing icon with 
    that name in any icon theme. A caller might want to check this on 
    its own for the desired theme.
    """
    if not os.path.exists(filename):
        # PyXDG would return text/plain
        return None
    mimetype = xdg.Mime.get_type(filename)
    return '-'.join((mimetype.media, mimetype.subtype))

# Low-level stuff

icon_cache = {}

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
            exec_ = convert(entry.getExec(), str)
            cmd = parse_commandline(exec_)[0]
            icon = convert(entry.getIcon(), str)
            yield (get_trimmed(cmd), icon)

# PyXDG-related helper functions

def iter_menu_files():
    """
    Iterate through the user's `.menu`-files and yield a `xdg.Menu.Menu` 
    object for each file to provide its entries as a parsed structure.
    """
    menu_dir = settings.config['menu-dir']
    menu_files = os.path.join(menu_dir, '*.menu')
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
