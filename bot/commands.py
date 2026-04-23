import discord
from discord import app_commands

from bot.services import get_item, reverse


def setup_commands(tree):

    @tree.command(name="rec", description="Show item recycle output")
    async def rec(interaction: discord.Interaction, item: str):
        data = get_item(item)

        if "error" in data:
            await interaction.response.send_message("Item not found")
            return

        embed = discord.Embed(
            title=f"Recycle: {data['name']}",
            color=0x2b2d31,
        )

        for key, value in data["recycle"].items():
            embed.add_field(
                name=key.replace("_", " ").title(),
                value=str(value),
                inline=True,
            )

        await interaction.response.send_message(embed=embed)

    @tree.command(name="rec_need", description="Calculate items needed for resource")
    async def rec_need(interaction: discord.Interaction, resource: str, amount: int):
        results = reverse(resource, amount)

        embed = discord.Embed(
            title=f"Need {amount} {resource}",
            color=0x5865F2,
        )

        for result in results[:5]:
            embed.add_field(
                name=result["item"],
                value=f"{result['needed']} pcs",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)
