import discord
from discord import app_commands
from discord.ext import commands

from storage import get_honor_user, get_honor_leaderboard


class Honor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="honor", description="Check a user's karma")
    @app_commands.describe(user="User to check (leave empty for yourself)")
    async def honor(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        record = get_honor_user(target.id)

        if not record:
            await interaction.response.send_message(f"{target.name} has no karma yet.")
        else:
            await interaction.response.send_message(
                f"⭐ **{target.name}** has **{record['karma']}** karma"
            )

    @app_commands.command(name="honorboard", description="View the karma leaderboard")
    async def honorboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        entries = get_honor_leaderboard(top_n=10)
        if not entries:
            await interaction.followup.send("No one has any karma yet.")
            return

        lines = []
        for i, (user_id, karma) in enumerate(entries, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                name = user.name
            except Exception:
                name = f"Unknown ({user_id})"
            lines.append(f"**{i}.** {name} — ⭐ **{karma}**")

        await interaction.followup.send("⭐ **KARMA LEADERBOARD** ⭐\n" + "\n".join(lines))


async def setup(bot: commands.Bot):
    await bot.add_cog(Honor(bot))