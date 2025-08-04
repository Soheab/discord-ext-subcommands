from __future__ import annotations
from typing import Any, Callable, Coroutine, Literal, TypeVar, overload
from collections import defaultdict
import logging

import discord
from discord import app_commands
from discord.ext import commands

Command = app_commands.Command[Any, ..., Any] | commands.Command[Any, ..., Any] | commands.HybridCommand[Any, ..., Any]
CommandGroup = app_commands.Group | commands.Group[Any, ..., Any] | commands.HybridGroup[Any, ..., Any]

_log = logging.getLogger("discord.ext.subcommands")

CommandT = TypeVar("CommandT", bound=Command)


class _Subcommand[
    CommandT: commands.Command[Any, ..., Any]
    | app_commands.Command[Any, ..., Any]
    | app_commands.Group
    | commands.Group[Any, ..., Any],
    GroupT: commands.Group[Any, ..., Any] | app_commands.Group | None,
]:
    """
    Internal representation of a subcommand.

    Parameters
    ----------
    group_name : str
        The name of the group this subcommand belongs to.
    command : CommandT
        The command object.
    """

    def __init__(
        self,
        group_name: str,
        command: CommandT,
    ) -> None:
        self.group_name: str = group_name
        self._command: CommandT = command
        self._group: GroupT = None  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def _determine_command_type(self) -> str:
        if isinstance(self._command, app_commands.Command):
            return "app command"
        elif isinstance(self._command, commands.Command):
            return "command"
        elif isinstance(self._command, (app_commands.Group, commands.Group)):
            return "group"
        return "unknown"

    @property
    def _determine_command_group(self) -> str:
        if isinstance(self._command, app_commands.Command):
            return "App command group"
        elif isinstance(self._command, commands.Command):
            return "Command group"
        elif isinstance(self._command, (app_commands.Group, commands.Group)):
            return "Group"
        return "unknown"


def subcommand(
    group_name: str,
    /,
) -> Callable[[CommandT], CommandT]:
    """
    Decorator to mark a command as a subcommand of a group that is defined elsewhere.

    This decorator allows you to attach a command to an existing group by specifying the group's name.
    It can be used with both prefix (& hybrid) commands and app commands.

    Parameters
    ----------
    group_name : str
        The name of the group to attach the subcommand to.

    Raises
    ------
    TypeError
        If `group_name` is not a string.
    ValueError
        If the command is already a subcommand.
    """

    def decorator(command: CommandT) -> CommandT:
        if not isinstance(command, (commands.Command, app_commands.Command, commands.Group, app_commands.Group)):
            raise TypeError(
                "@subcommand() must be used on a command. For example, use @commands.command() or @app_commands.command() below @subcommand()"
            )

        if not isinstance(group_name, str):
            raise TypeError("Group name must be a string.")
        if command.parent:
            raise ValueError("Command is already a subcommand.")
        command.callback.__subcommand__ = _Subcommand(group_name, command)  # pyright: ignore[reportFunctionMemberAccess]
        return command

    return decorator


class MultiFilesSubcommandsManager:
    """Class to manage subcommands across multiple cogs.

    Parameters
    ----------
    bot: commands.Bot
        The bot instance.
    copy_group_error_handler: bool
        Whether to copy the error handler from the group to the subcommand.
        The library does this automatically for app commands. So this only applies to prefix/hybrid commands.

        Defaults to ``False``.
    check_group_type: bool
        Whether to check the group type when adding subcommands.
        Setting this to True will ensure that the subcommand is added to the
        correct group type or else a TypeError will be raised.

        Setting this to False (default) will not add the subcommand to group
        and no error will be raised, unless :meth:`~MultiFilesSubcommandsManager.raise_for_remaining_commands`
        is called.

        Defaults to ``False``.
    """

    __slots__: tuple[str, ...] = (
        "__bot",
        "__original_cog_add",
        "__original_cog_remove",
        "__commands",
        "_not_found",
        "_copy_group_error_handler",
        "_check_group_type",
    )

    def __init__(
        self,
        bot: commands.Bot,
        *,
        copy_group_error_handler: bool = False,
        check_group_type: bool = False,
    ) -> None:
        if not isinstance(bot, commands.Bot):
            raise TypeError(f"bot must be an instance of commands.Bot, not {type(bot).__name__!r}.")

        self.__bot = bot
        self._copy_group_error_handler = copy_group_error_handler
        self._check_group_type = check_group_type
        print(
            f"MultiFilesSubcommandsManager initialized with copy_group_error_handler={self._copy_group_error_handler!r}."
        )
        self.__original_cog_add: Callable[..., Coroutine[Any, Any, None]] = self.__bot.add_cog
        self.__original_cog_remove: Callable[..., Coroutine[Any, Any, commands.Cog | None]] = self.__bot.remove_cog
        self.__bot.add_cog = self.__cog_add
        self.__bot.remove_cog = self.__cog_remove
        self.__commands: dict[str, dict[str, _Subcommand]] = defaultdict(dict)
        self._not_found: dict[str, dict[str, _Subcommand]] = defaultdict(dict)

    def remove(self) -> None:
        for _commands in self.__commands.values():
            for subcommand in _commands.values():
                if not subcommand._group:
                    continue
                if isinstance(subcommand._command, (app_commands.Command, app_commands.Group)):
                    self.__handle_app_command("REMOVE", subcommand=subcommand, group=subcommand._group)  # pyright: ignore[reportArgumentType]
                else:
                    self.__handle_prefix_hybrid_command("REMOVE", subcommand=subcommand, group=subcommand._group)  # pyright: ignore[reportArgumentType]

        self.__commands.clear()
        self._not_found.clear()
        self.__bot.remove_cog = self.__original_cog_remove  # pyright: ignore[reportAttributeAccessIssue]
        self.__bot.add_cog = self.__original_cog_add  # pyright: ignore[reportAttributeAccessIssue]

    def raise_for_remaining_commands(self) -> None:
        """Raises an error for any subcommands that could not be attached to a group.

        Raises
        ------
        RuntimeError
            If any subcommands remain unattached.
        """
        if not self._not_found:
            return

        from difflib import get_close_matches

        for cog, subcommands in self._not_found.items():
            for name, subcommand in subcommands.items():
                if not subcommand._group:
                    commands_names = [c.qualified_name for c in self.__get_groups(subcommand._command)]
                    didyoumean = get_close_matches(name, commands_names, n=1, cutoff=0.0)
                    msg = (
                        f"{subcommand._determine_command_group} {subcommand.group_name!r} for {subcommand._determine_command_type} "
                        f"{name!r} in cog {cog!r} was not found."
                    )
                    if didyoumean:
                        msg += f" Did you mean {didyoumean[0]!r}?"
                    raise RuntimeError(msg)

    def __get_subcommand(self, command: Command | CommandGroup) -> _Subcommand | None:
        # Retrieves the _Subcommand instance from a command if present.
        try:
            sub = command.callback.__subcommand__  # pyright: ignore[reportFunctionMemberAccess, reportAttributeAccessIssue]
        except AttributeError:
            return None
        else:
            sub._command = command
            return sub

    def __get_groups(self, command: Command | CommandGroup, check_command_type: bool = True) -> list[CommandGroup]:
        if not check_command_type:
            tree_commands = [
                c
                for c in self.__bot.tree.walk_commands(type=discord.AppCommandType.chat_input)
                if isinstance(c, app_commands.Group)
            ]
            prefix_commands = [
                c for c in self.__bot.walk_commands() if isinstance(c, (commands.Group, commands.HybridGroup))
            ]
            return tree_commands + prefix_commands

        # Retrieves all command groups relevant to the command type.
        if isinstance(command, (app_commands.Command, app_commands.Group)):
            return [
                c
                for c in self.__bot.tree.walk_commands(type=discord.AppCommandType.chat_input)
                if isinstance(c, app_commands.Group)
            ]
        return [c for c in self.__bot.walk_commands() if isinstance(c, (commands.Group, commands.HybridGroup))]

    def __find_group(
        self, subcommand: _Subcommand
    ) -> app_commands.Group | commands.Group[Any, ..., Any] | commands.HybridGroup[Any, ..., Any] | None:
        # Finds the given group
        name = subcommand.group_name
        command = subcommand._command
        group = discord.utils.get(
            self.__get_groups(command, check_command_type=not self._check_group_type),
            qualified_name=name,
        )
        if not group:
            return None

        if not isinstance(group, (app_commands.Group, commands.Group, commands.HybridGroup)):
            raise TypeError(
                f"Group {name!r} for command {command.qualified_name!r} is not a group command. It's a {type(group)!r}."
            )

        if isinstance(group, app_commands.Group) and not isinstance(
            command, (app_commands.Command, app_commands.Group)
        ):
            raise TypeError(f"Cannot add {type(subcommand._command)!r} to a {type(group)!r}.")

        if isinstance(group, commands.HybridGroup) and not isinstance(
            command, (commands.HybridCommand, commands.HybridGroup)
        ):
            raise TypeError(f"Cannot add {type(subcommand._command)!r} to a {type(group)!r}.")
        if isinstance(group, commands.Group) and not isinstance(command, (commands.Command, commands.Group)):
            raise TypeError(f"Cannot add {type(subcommand._command)!r} to a {type(group)!r}.")

        return group

    async def __cog_add(self, cog: commands.Cog, *args: Any, **kwargs: Any) -> None:
        # Call original cog add
        await self.__original_cog_add(cog, *args, **kwargs)

        # Get all subcommands
        for command in list(cog.walk_commands()) + list(cog.walk_app_commands()):
            if subcommand := self.__get_subcommand(command):
                self.__commands[cog.qualified_name][command.name] = subcommand
                self._not_found[cog.qualified_name][command.name] = subcommand

        # Handle all subcommands
        self.__handle_commands()

    async def __cog_remove(self, name: str, *args: Any, **kwargs: Any) -> None:
        # Call original cog remove
        await self.__original_cog_remove(name, *args, **kwargs)

        # Get all subcommands for this cog, if any
        try:
            commands = self.__commands[name]
        except KeyError:
            pass
        else:
            # Handle all subcommands
            for _, subcommand in commands.items():
                if isinstance(subcommand._command, (app_commands.Command, app_commands.Group)):
                    self.__handle_app_command("REMOVE", subcommand)
                else:
                    self.__handle_prefix_hybrid_command("REMOVE", subcommand=subcommand)

            # Remove the cog from the commands registry
            del self.__commands[name]
            self._not_found.pop(name, None)

    @overload
    def __handle_prefix_hybrid_command(
        self,
        action: Literal["ADD"],
        /,
        subcommand: _Subcommand[
            commands.Command[Any, ..., Any] | commands.Group[Any, ..., Any], commands.Group[Any, ..., Any]
        ],
        *,
        group: commands.Group[Any, ..., Any],
    ) -> None: ...

    @overload
    def __handle_prefix_hybrid_command(
        self,
        action: Literal["REMOVE"],
        /,
        subcommand: _Subcommand[
            commands.Command[Any, ..., Any] | commands.Group[Any, ..., Any], commands.Group[Any, ..., Any]
        ],
    ) -> None: ...

    def __handle_prefix_hybrid_command(
        self,
        action: Literal["ADD", "REMOVE"],
        /,
        subcommand: _Subcommand[
            commands.Command[Any, ..., Any] | commands.Group[Any, ..., Any], commands.Group[Any, ..., Any]
        ],
        *,
        group: commands.Group[Any, ..., Any] | None = None,
    ) -> None:
        if action == "ADD":
            if subcommand._command.parent:
                msg = (
                    f"Command {subcommand._command.name!r} is already a subcommand on group: "
                    f"{subcommand._command.parent.qualified_name!r}."  # pyright: ignore[reportAttributeAccessIssue]
                )
                raise ValueError(msg)
            if not group:
                raise ValueError(f"Group is required when action is {action!r}.")
            subcommand._group = group
            self.__bot.remove_command(subcommand._command.name)
            subcommand._group.add_command(subcommand._command)
            if self._copy_group_error_handler and group.has_error_handler():
                subcommand._command.error(group.on_error)
        else:
            if not subcommand._group:
                return
            subcommand._group.remove_command(subcommand._command.name)
            subcommand._group = None  # type: ignore

    @overload
    def __handle_app_command(
        self,
        action: Literal["ADD"],
        /,
        subcommand: _Subcommand[app_commands.Command[Any, ..., Any] | app_commands.Group, app_commands.Group],
        *,
        group: app_commands.Group,
    ) -> None: ...

    @overload
    def __handle_app_command(
        self,
        action: Literal["REMOVE"],
        /,
        subcommand: _Subcommand[app_commands.Command[Any, ..., Any] | app_commands.Group, app_commands.Group],
    ) -> None: ...

    def __handle_app_command(
        self,
        action: Literal["ADD", "REMOVE"],
        /,
        subcommand: _Subcommand[app_commands.Command[Any, ..., Any] | app_commands.Group, app_commands.Group],
        *,
        group: app_commands.Group | None = None,
    ) -> None:
        if action == "ADD":
            if subcommand._command.parent:
                raise ValueError(
                    f"Command {subcommand._command.name!r} is already a subcommand on group: "
                    f"{subcommand._command.parent.qualified_name!r}."
                )
            if not group:
                raise ValueError(f"Group is required when action is {action!r}.")
            subcommand._group = group
            self.__bot.tree.remove_command(subcommand._command.name)
            subcommand._group.add_command(subcommand._command)
        else:
            if not subcommand._group:
                print("Subcommand is not part of a group.", subcommand._command.name)
                return
            subcommand._group.remove_command(subcommand._command.name)
            subcommand._group = None  # type: ignore

    def __handle_commands(self) -> None:
        for cog_name, _commands in self._not_found.copy().items():
            for subcommand in _commands.copy().values():
                group = self.__find_group(subcommand)
                if not group:
                    continue
                if isinstance(subcommand._command, (app_commands.Command, app_commands.Group)):
                    self.__handle_app_command(
                        "ADD",
                        subcommand=subcommand,
                        group=group,  # pyright: ignore[reportArgumentType]
                    )
                else:
                    self.__handle_prefix_hybrid_command(
                        "ADD",
                        subcommand=subcommand,
                        group=group,  # pyright: ignore[reportArgumentType]
                    )
                del self._not_found[cog_name][subcommand._command.name]
            if not self._not_found.get(cog_name, {}):
                del self._not_found[cog_name]
