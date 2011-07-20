"""
Tools to launch files and commands.

Some features:

- Make name completions based on given fragment
- Mark fragment inside a completion
- Guess suitable icon when dealing with a command or file
- Launch files with their associated application (images, scripts, ...)
- A GUI to conveniently benefit of those features
"""
__author__ = 'Sebastian Linke'
__license__ = 'MIT'
__version__ = '0.1-dev'

from . import core, gui, icongetter, settings
