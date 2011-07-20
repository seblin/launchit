"""
Tools to launch files and commands.

Some features:

- Make name completions based on given fragment
- Mark fragment inside a completion
- Guess suitable icon when dealing with a command or file
- Launch files with their associated application (images, scripts, ...)
- A GUI to conveniently benefit of those features
"""
from . import core, gui, icongetter, settings
