import discord
from discord.ext import commands

# import the extension
from discord.ext.subcommands import subcommand


class HybridGroups(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Define hybrid command group - works as both slash and prefix commands
    @commands.hybrid_group(name="channel", description="Channel related commands.", invoke_without_command=True)
    async def channel(self, ctx: commands.Context):
        """Channel command group for both slash and prefix commands."""
        if ctx.interaction:
            await ctx.send("Channel command group. Use `/channel help` for more information.")
        else:
            await ctx.send(f"Channel command group. See `{ctx.prefix}channel help` for more information.")

    # Hybrid subcommand
    @channel.command(name="help", description="Show channel help commands")
    async def channel_help(self, ctx: commands.Context):
        """Show available channel commands."""
        commands_list = [f"- `{command.qualified_name} {command.signature}`" for command in self.channel.commands]
        await ctx.send(f"Channel help command. Available commands:\n{'\n'.join(commands_list)}")


class HybridChannelCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Hybrid subcommand using the subcommand decorator
    @subcommand("channel")
    @commands.hybrid_command(name="info", description="Show channel information")
    async def channel_info(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        """Show information about a channel."""
        target_channel = channel or ctx.channel

        if not isinstance(target_channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
            await ctx.send("This command only works with text, voice, or category channels.")
            return

        await ctx.send(
            f"## Channel Info:\n- Name: {target_channel.name}\n- ID: {target_channel.id}\n- Created: {discord.utils.format_dt(target_channel.created_at, 'F')}"
        )

    # Another hybrid subcommand
    @subcommand("channel")
    @commands.hybrid_command(name="topic", description="Get channel's topic")
    async def channel_topic(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        """Get a channel's topic."""
        target_channel = channel or ctx.channel

        if not isinstance(target_channel, discord.TextChannel):
            await ctx.send("This command only works with text channels.")
            return

        topic = target_channel.topic or "No topic set"
        await ctx.send(f"## Channel Topic:\n{topic}")


class HybridUtilityCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Define a hybrid subgroup
    @subcommand("channel")
    @commands.hybrid_group(name="utils", description="Channel utility commands")
    async def channel_utils(self, ctx: commands.Context):
        """Channel utility commands."""
        await ctx.send("## Channel Utility Commands:")

    # Hybrid subcommand of the subgroup
    @subcommand("channel utils")
    @commands.hybrid_command(name="membercount", description="Get member count who can see this channel")
    async def channel_utils_membercount(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        """Get the number of members who can see a channel."""
        target_channel = channel or ctx.channel

        if not isinstance(target_channel, (discord.TextChannel, discord.VoiceChannel)):
            await ctx.send("This command only works with text or voice channels.")
            return

        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        # Count members who can see the channel
        member_count = len([
            member for member in ctx.guild.members if target_channel.permissions_for(member).read_messages
        ])

        await ctx.send(f"## Channel Member Count:\n{member_count} members can see {target_channel.mention}")

    # Another utility command
    @subcommand("channel utils")
    @commands.hybrid_command(name="permissions", description="Check permissions for a channel")
    async def channel_utils_permissions(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        """Check your permissions for a channel."""
        target_channel = channel or ctx.channel

        if not isinstance(target_channel, (discord.TextChannel, discord.VoiceChannel)):
            await ctx.send("This command only works with text or voice channels.")
            return

        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        member = ctx.guild.get_member(ctx.author.id)
        if not member:
            await ctx.send("Could not find your member data.")
            return

        perms = target_channel.permissions_for(member)

        key_permissions = [
            ("Read Messages", perms.read_messages),
            ("Send Messages", perms.send_messages),
            ("Manage Messages", perms.manage_messages),
            ("Embed Links", perms.embed_links),
            ("Attach Files", perms.attach_files),
            ("Use External Emojis", perms.use_external_emojis),
        ]

        perm_list = [f"- {name}: {'✅' if has_perm else '❌'}" for name, has_perm in key_permissions]

        await ctx.send(f"## Your Permissions in {target_channel.mention}:\n{chr(10).join(perm_list)}")


# Channel management hybrid commands
class HybridChannelManagement(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Main channel management hybrid group
    @subcommand("channel")
    @commands.hybrid_group(name="manage", description="Channel management commands", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def manage(self, ctx: commands.Context):
        """Channel management commands (requires Manage Channels permission)."""
        await ctx.send("Channel management commands. Use the subcommands to manage channels.")

    # Channel creation hybrid command
    @manage.command(name="create", description="Create a new text channel")
    @commands.has_permissions(manage_channels=True)
    async def manage_create(self, ctx: commands.Context, name: str, *, topic: str | None = None):
        """Create a new text channel."""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        try:
            if topic:
                channel = await ctx.guild.create_text_channel(name=name, topic=topic)
            else:
                channel = await ctx.guild.create_text_channel(name=name)
            await ctx.send(f"✅ Created channel {channel.mention}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create channels.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to create channel: {e}")

    # Channel deletion hybrid command
    @manage.command(name="delete", description="Delete a channel")
    @commands.has_permissions(manage_channels=True)
    async def manage_delete(self, ctx: commands.Context, channel: discord.TextChannel):
        """Delete a channel."""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        channel_name = channel.name
        try:
            await channel.delete(reason=f"Deleted by {ctx.author}")
            # Send to current channel if it's different, otherwise send to system channel
            if channel != ctx.channel:
                await ctx.send(f"✅ Deleted channel #{channel_name}")
            elif ctx.guild.system_channel:
                await ctx.guild.system_channel.send(f"✅ Channel #{channel_name} was deleted by {ctx.author.mention}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete that channel.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to delete channel: {e}")


# Add cogs to bot like normal, in any order.
async def setup(bot: commands.Bot):
    await bot.add_cog(HybridGroups(bot))
    await bot.add_cog(HybridChannelCommands(bot))
    await bot.add_cog(HybridChannelManagement(bot))
    await bot.add_cog(HybridUtilityCommands(bot))
