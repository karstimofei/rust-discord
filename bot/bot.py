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


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")

client.run(DISCORD_TOKEN)
