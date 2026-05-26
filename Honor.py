import discord
from discord import app_commands
from discord.ext import commands

from storage import add_honor, remove_honor, get_honor_user, get_honor_leaderboard


class Honor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="vouch", description="Give honor to a user")
    @app_commands.describe(user="User to vouch for")
    async def vouch(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        success, msg = add_honor(user.id, interaction.user.id)
        await interaction.followup.send(msg, ephemeral=not success)

    @app_commands.command(name="unvouch", description="Remove honor you gave to a user")
    @app_commands.describe(user="User to remove your vouch from")
    async def unvouch(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        success, msg = remove_honor(user.id, interaction.user.id)
        await interaction.followup.send(msg, ephemeral=not success)

    @app_commands.command(name="honor", description="Check a user's honor")
    @app_commands.describe(user="User to check (leave empty for yourself)")
    async def honor(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        record = get_honor_user(target.id)

        if not record:
            await interaction.response.send_message(f"{target.name} has no honor yet.")
        else:
            await interaction.response.send_message(
                f"⭐ **{target.name}** has **{record['Karma']}** honor "
                f"(vouched by {len(record['vouched_by'])} people)"
            )

    @app_commands.command(name="honorboard", description="View the honor leaderboard")
    async def honorboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        entries = get_honor_leaderboard(top_n=10)
        if not entries:
            await interaction.followup.send("No one has any honor yet.")
            return

        lines = []
        for i, (user_id, honor) in enumerate(entries, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                name = user.name
            except Exception:
                name = f"Unknown ({user_id})"
            lines.append(f"**{i}.** {name} — ⭐ **{honor}**")

        await interaction.followup.send("⭐ **HONOR LEADERBOARD** ⭐\n" + "\n".join(lines))


async def setup(bot: commands.Bot):
    await bot.add_cog(Honor(bot))