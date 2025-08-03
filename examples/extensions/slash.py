import discord
from discord import app_commands
from discord.ext import commands

from discord.ext.subcommands import subcommand


class SlashCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Define the main slash command group called "server"
    server = app_commands.Group(name="server", description="Server related commands.")

    # Subcommand one for server group
    @server.command(name="info")
    async def server_info(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.")
            return

        await interaction.response.send_message(f"This server's name is {interaction.guild.name}")

    # Define a subgroup for server group
    server_settings = app_commands.Group(name="settings", description="Server settings commands.", parent=server)


class ServerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Subcommand two for server group
    @subcommand("server")
    @app_commands.command(name="banner")
    async def server_banner(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.")
            return

        if not interaction.guild.banner:
            await interaction.response.send_message("This server does not have a banner.")
            return

        await interaction.response.send_message(f"This server's banner is {interaction.guild.banner}")

    # Subcommand three for server group
    @subcommand("server")
    @app_commands.command(name="icon")
    async def server_icon(self, interaction: discord.Interaction):
        """Sends the server's icon."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.")
            return

        if not interaction.guild.icon:
            await interaction.response.send_message("This server does not have an icon.")
            return

        await interaction.response.send_message(f"This server's icon is {interaction.guild.icon}")


class ServerSettingsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Subcommand one for server settings group
    @subcommand("server settings")
    @app_commands.command(name="edit-name")
    async def server_settings_edit_name(self, interaction: discord.Interaction, new_name: str):
        """Edits the server's name."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.")
            return

        await interaction.guild.edit(name=new_name)
        await interaction.response.send_message(f"This server's name has been changed to {new_name}.")

    # Subcommand two for server settings group
    @subcommand("server settings")
    @app_commands.command(name="edit-description")
    async def server_settings_edit_description(self, interaction: discord.Interaction, new_description: str):
        """Edits the server's description."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.")
            return

        await interaction.guild.edit(description=new_description)
        await interaction.response.send_message(f"This server's description has been changed to {new_description}.")


# Add cogs to bot like normal, in any order.
async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCommands(bot))
    await bot.add_cog(SlashCog(bot))
    await bot.add_cog(ServerSettingsCommands(bot))
