# discord-ext-subcommands

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![discord.py Version](https://img.shields.io/badge/discord.py-2.5.2+-blue.svg)](https://github.com/Rapptz/discord.py)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

A powerful Discord.py extension that revolutionizes command organization by allowing you to define subcommands across multiple files and cogs. Say goodbye to monolithic command files and embrace modular, maintainable bot architecture.

## Table of Contents

- [Why Use This?](#why-use-this)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Why Use This?

🎯 **Modular Organization**: Split large command groups across multiple files for better code organization  
🔧 **Easy Maintenance**: Each subcommand lives in its own logical cog, making updates and debugging simpler  
🔄 **Flexible**: Works seamlessly with prefix commands, slash commands, and hybrid commands  
📁 **Clean Architecture**: Keep related functionality together while maintaining separation of concerns  
⚡ **Automatic Management**: Handles the complex task of connecting subcommands to their parent groups automatically  

Perfect for large bots where command groups become unwieldy when defined in a single file!

## Installation

### Stable Release (Recommended)
```bash
python -m pip install discord-ext-subcommands
```

### Development Version
For the latest features and bug fixes:
```bash
python -m pip install "discord-ext-subcommands @ git+https://github.com/yourusername/discord-ext-subcommands"
```

### Requirements
- Python 3.12+
- discord.py 2.5.2+


## Inspiration

This project is based on [pycord-multicog](https://github.com/Dorukyum/pycord-multicog) by @Dorukyum and adapted for discord.py.

## Quick Start

```python
import discord
from discord.ext import commands
from discord.ext.subcommands import MultiFilesSubcommandsManager, subcommand

# Main bot file
bot = commands.Bot(..)
manager = MultiFilesSubcommandsManager(bot)

# Create a command group
@bot.hybrid_group(name="admin")
async def admin_group(ctx):
    """Administrative commands"""
    pass

# In a separate cog file
class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @subcommand("admin")  # This will be attached to the admin group
    @commands.hybrid_command(name="ban")
    async def admin_ban(self, ctx, user: discord.Member, *, reason="No reason provided"):
        """Ban a user from the server"""
        await ctx.send(f"Banned {user.mention} for: {reason}")

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
```

> **💡 Tip**: This example shows how you can keep your main command groups in your bot file while distributing related subcommands across multiple cog files, making your code more organized and maintainable.

## Usage Guide

### Step-by-Step Setup

### 1. Initialize the Manager

```python
from discord.ext.subcommands import MultiFilesSubcommandsManager

bot = commands.Bot(...)
manager = MultiFilesSubcommandsManager(bot)
```

### 2. Create Command Groups

Define your main command groups wherever you like:

```python
@bot.hybrid_group(name="admin")
async def admin_group(ctx):
    """Administrative commands"""
    pass

@bot.group(name="economy")
async def economy_group(ctx):
    """Economy commands"""
    pass
```

> **💡 Best Practice**: Define your main groups in your bot file or a dedicated commands file for better organization.

### 3. Add Subcommands in Separate Files

Use the `@subcommand()` decorator to attach commands to existing groups:

```python
from discord.ext.subcommands import subcommand

class EconomyCog(commands.Cog):
    @subcommand("economy")
    @commands.command(name="balance")
    async def check_balance(self, ctx, user: discord.Member = None):
        """Check user's balance"""
        user = user or ctx.author
        await ctx.send(f"{user.name} has 1000 coins")

    @subcommand("economy")
    @commands.command(name="pay")
    async def pay_user(self, ctx, user: discord.Member, amount: int):
        """Pay another user"""
        await ctx.send(f"Paid {amount} coins to {user.mention}")
```

> **🔗 Key Point**: The `@subcommand("economy")` decorator automatically connects these commands to the `economy` group defined elsewhere.

### 4. Nested Groups

You can create complex command hierarchies:

```python
# Main group
@bot.hybrid_group(name="server")
async def server_group(ctx):
    """Server management commands"""
    pass

# Nested group
@server_group.group(name="settings")
async def server_settings_group(ctx):
    """Server settings management"""
    pass

# Subcommand for nested group
class ConfigCog(commands.Cog):
    @subcommand("server settings")  # Note: full qualified name
    @commands.hybrid_command(name="prefix")
    async def set_prefix(self, ctx, new_prefix: str):
        """Set the server's command prefix"""
        await ctx.send(f"Prefix set to: {new_prefix}")
```

> **🏗️ Advanced**: Use the full qualified name (e.g., `"server settings"`) to target nested groups. The extension handles the hierarchy automatically.

## Examples

Check out the [examples](./examples/) directory for complete working examples:

- **[Basic Bot](./examples/bot.py)**: Simple setup with extenions that includes all command types


## API Reference

### `MultiFilesSubcommandsManager`

The central manager class that orchestrates subcommand organization across your bot.

#### Constructor Parameters

| Parameter                  | Type           | Default  | Description                                    |
| -------------------------- | -------------- | -------- | ---------------------------------------------- |
| `bot`                      | `commands.Bot` | Required | The bot instance to manage                     |
| `copy_group_error_handler` | `bool`         | `False`  | Copy error handlers from groups to subcommands |
| `check_group_type`         | `bool`         | `False`  | Enforce group type compatibility               |

#### Methods

**`remove()`**  
Cleanly removes the manager and detaches all subcommands. This is 
done automatically for a cog when it is removed.

**`raise_for_remaining_commands()`**  
Raises an error if any subcommands couldn't be attached to their groups. Useful for debugging configuration issues.

### `@subcommand(group_name)`

A decorator that marks a command as a subcommand of an existing group.

#### Parameters

| Parameter    | Type  | Description                                                                   |
| ------------ | ----- | ----------------------------------------------------------------------------- |
| `group_name` | `str` | The qualified name of the target group (e.g., `"admin"`, `"server settings"`) |

#### Supported Command Types

| Command Type    | Decorator                                  | Notes                           |
| --------------- | ------------------------------------------ | ------------------------------- |
| Prefix Commands | `@commands.command()`                      | Traditional text-based commands |
| Hybrid Commands | `@commands.hybrid_command()`               | Both prefix and slash support   |
| Slash Commands  | `@app_commands.command()`                  | Discord slash commands only     |
| Command Groups  | `@commands.group()` / `app_commands.Group` | For nested command structures   |


## License

This project is licensed under the [Mozilla Public License 2.0](LICENSE).

---

<div align="center">
  <p>
    <strong>Made with ❤️ for the Discord.py community</strong>
  </p>
  <p>
    <a href="https://github.com/yourusername/discord-ext-subcommands/issues">Report Bug</a> •
    <a href="https://github.com/yourusername/discord-ext-subcommands/discussions">Request Feature</a> •
    <a href="https://github.com/yourusername/discord-ext-subcommands">Star on GitHub</a>
  </p>
</div>