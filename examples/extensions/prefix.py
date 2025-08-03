import discord
from discord.ext import commands

# import the extension
from discord.ext.subcommands import subcommand


class Groups(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # defining the group here
    # @bot user
    # commands for this group will be in userinfo.py
    @commands.group(invoke_without_command=True)
    async def user(self, ctx: commands.Context):
        await ctx.send(f"User command group. See `{ctx.prefix}user help` for more information.")

    # error handler for the user group for fun
    @user.error
    async def user_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(f"Member not found: {error.argument}")
        else:
            await ctx.send(f"An error occurred: {error}")

    # define one subcommand here for example sake
    # @bot user help
    @user.command(name="help")
    async def user_help(self, ctx: commands.Context):
        commands_list = [
            f"- `{ctx.prefix}{command.qualified_name} {command.signature}`" for command in self.user.commands
        ]
        await ctx.send(f"User help command. Available commands:\n{'\n'.join(commands_list)}")


class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # third subcommand of the user group
    # @bot user info
    @subcommand("user")
    @commands.command(name="info")
    async def user_info(self, ctx: commands.Context, user: discord.Member):
        print(
            self,
            self.user_info,
            ctx.command.has_error_handler() if ctx.command else None,
            ctx.command.parent if ctx.command else None,
            ctx.command,
        )
        await ctx.send(f"## User Info:\n- Name: {user.name}\n- ID: {user.id}\n- Created At: {user.created_at}")

    # fourth subcommand of the user group
    # @bot user avatar
    @subcommand("user")
    @commands.command(name="avatar")
    async def user_avatar(self, ctx: commands.Context, user: discord.Member):
        await ctx.send(f"## User Avatar:\n{user.display_avatar.url}")

    # define a subgroup for the user group for utility commands
    # @bot user utils
    # commands for this subgroup will be in utils.py
    @subcommand("user")
    @commands.group(name="utils")
    async def user_utils(self, ctx: commands.Context):
        await ctx.send("## User Utility Commands:")


class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # first subcommand of the user utils subgroup
    # @bot user utils whenjoin
    @subcommand("user utils")
    @commands.command(name="whenjoin")
    async def user_utils_whenjoin(self, ctx: commands.Context, user: discord.Member):
        await ctx.send(
            f"## User Join Date:\n{user.display_name} joined this server {discord.utils.format_dt(user.joined_at, 'R') if user.joined_at else 'at an unknown time...'}."
        )


# Add cogs to bot like normal, in any order.
async def setup(bot: commands.Bot):
    await bot.add_cog(Groups(bot))
    await bot.add_cog(Utilities(bot))
    await bot.add_cog(UserInfo(bot))
