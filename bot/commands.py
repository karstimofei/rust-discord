import discord
from discord import app_commands
import requests

from bot.services import get_item, reverse


def setup_commands(tree):

    @tree.command(name="rec", description="Show item recycle output")
    async def rec(interaction: discord.Interaction, item: str):
        await interaction.response.defer(thinking=True)

        try:
            data = get_item(item)
        except requests.RequestException:
            await interaction.followup.send("API is unavailable right now. Check that FastAPI is running and API_HOST is correct.")
            return

        if "error" in data:
            await interaction.followup.send("Item not found")
            return

        embed = discord.Embed(
            title=f"Recycle: {data['name']}",
            color=0x2b2d31,
        )

        recycle = data.get("recycle", {})

        if not recycle:
            embed.description = "No recycle data for this item."

        for key, value in recycle.items():
            embed.add_field(
                name=key.replace("_", " ").title(),
                value=str(value),
                inline=True,
            )

        await interaction.followup.send(embed=embed)

    @tree.command(name="rec_need", description="Calculate items needed for resource")
    async def rec_need(interaction: discord.Interaction, resource: str, amount: int):
        await interaction.response.defer(thinking=True)

        try:
            results = reverse(resource, amount)
        except requests.RequestException:
            await interaction.followup.send("API is unavailable right now. Check that FastAPI is running and API_HOST is correct.")
            return

        embed = discord.Embed(
            title=f"Need {amount} {resource}",
            color=0x5865F2,
        )

        if not results:
            embed.description = "No recycle matches found."
        else:
            for result in results[:5]:
                embed.add_field(
                    name=result["item"],
                    value=f"{result['needed']} pcs",
                    inline=False,
                )

        await interaction.followup.send(embed=embed)
