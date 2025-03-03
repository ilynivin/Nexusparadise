import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timeout", description="Timeout a user.")
    @app_commands.describe(user="The user to timeout.")
    @app_commands.describe(duration_minutes="Duration of the timeout in minutes.")
    @app_commands.describe(reason="Reason for the timeout.")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration_minutes: int, reason: str = "No reason provided."):
        """Timeouts a user."""

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("You do not have the required permissions (Moderate Members).", ephemeral=True)
            return

        if interaction.user == user:
            await interaction.response.send_message("You cannot timeout yourself.", ephemeral=True)
            return

        if interaction.guild.me == user:
            await interaction.response.send_message("I cannot timeout myself.", ephemeral=True)
            return

        if interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot timeout someone with an equal or higher role than yourself.", ephemeral=True)
            return

        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message("I cannot timeout someone with an equal or higher role than myself.", ephemeral=True)
            return

        duration = datetime.timedelta(minutes=duration_minutes)
        timeout_until = discord.utils.utcnow() + duration

        try:
            await user.timeout(timeout_until, reason=reason)
            await interaction.response.send_message(f"{user.mention} has been timed out for {duration_minutes} minutes. Reason: {reason}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have the necessary permissions to timeout this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while timing out the user: {e}", ephemeral=True)

    @app_commands.command(name="removetimeout", description="Remove a timeout from a user.")
    @app_commands.describe(user="The user to remove the timeout from.")
    async def removetimeout(self, interaction: discord.Interaction, user: discord.Member):
        """Removes a timeout from a user."""

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("You do not have the required permissions (Moderate Members).", ephemeral=True)
            return

        try:
            await user.timeout(None)  # Set timeout to None to remove it
            await interaction.response.send_message(f"Timeout removed from {user.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have the necessary permissions to remove the timeout.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while removing the timeout: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Timeout(bot))