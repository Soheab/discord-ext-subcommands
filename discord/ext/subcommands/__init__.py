"""
discord-ext-subcommands

A Discord.py extension for organizing subcommands across multiple files and cogs.
"""

from .core import MultiFilesSubcommandsManager, subcommand

__version__ = "0.1.0"
__all__ = ["MultiFilesSubcommandsManager", "subcommand"]