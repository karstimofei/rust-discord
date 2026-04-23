import discord
from discord import app_commands

from bot.commands import setup_commands
from config import DISCORD_TOKEN


class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)


client = Client()
setup_commands(client.tree)


@client.event
async def on_ready():
    await client.tree.sync()
    print("Bot ready")


@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    message = "Command failed."

    if isinstance(error, app_commands.CommandInvokeError) and error.original:
        message = f"Command failed: {error.original}"

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")

client.run(DISCORD_TOKEN)
