import pathlib

import discord
from discord.ext import commands

from discord.ext.subcommands import MultiFilesSubcommandsManager


class MyBot(commands.Bot):
    def __init__(
        self,
    ) -> None:
        intents = discord.Intents(messages=True, guilds=True, members=True)
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

        self.subcommands_manager = MultiFilesSubcommandsManager(
            self, copy_group_error_handler=True, check_group_type=False
        )

    async def setup_hook(self) -> None:
        print(f"{self.user} has logged in!")

        # load extensions
        # the order of loading does not matter
        for ext in pathlib.Path(__file__).parent.glob("extensions/*.py"):
            try:
                await self.load_extension(ext.with_stem(f"extensions.{ext.stem}").stem)
            except Exception as e:
                raise e
            else:
                print(f"Successfully loaded extension {ext.name}")

        # optional
        self.subcommands_manager.raise_for_remaining_commands()

        # Sync all app commands
        # Do NOT do this in production
        guild = discord.Object(id=423828791098605578)
        self.tree.copy_global_to(guild=guild)
        commands = await self.tree.sync(guild=guild)  # Replace with your guild ID
        print(f"Synced {len(commands)} commands.", commands)


bot = MyBot()
bot.run("YOUR-BOT-TOKEN")
