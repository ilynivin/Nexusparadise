import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a user from the server.")
    @app_commands.describe(user="The user to ban.")
    @app_commands.describe(reason="The reason for the ban.")
    @app_commands.describe(delete_message_days="Number of days of messages to delete (0-7).")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided.", delete_message_days: app_commands.Range[int, 0, 7] = 0):
        """Bans a user with an interactive confirmation. Requires ban permissions."""

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You do not have the required permissions (Ban Members).", ephemeral=True)
            return

        if interaction.user == user:
            await interaction.response.send_message("You cannot ban yourself.", ephemeral=True)
            return

        if interaction.guild.me == user:
            await interaction.response.send_message("I cannot ban myself.", ephemeral=True)
            return

        if interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot ban someone with an equal or higher role than yourself.", ephemeral=True)
            return

        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message("I cannot ban someone with an equal or higher role than myself.", ephemeral=True)
            return

        # Confirmation Embed
        embed = discord.Embed(title="Confirm Ban", description=f"Are you sure you want to ban {user.mention}?\n\n**Reason:** {reason}\n**Delete Messages:** {delete_message_days} days", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, view=BanConfirmation(user, reason, interaction.user, self.bot, delete_message_days), ephemeral=True)

    @app_commands.command(name="tempban", description="Ban a user for a set time.")
    @app_commands.describe(user="The user to temporarily ban.")
    @app_commands.describe(duration_minutes="Duration of the ban in minutes.")
    @app_commands.describe(reason="Reason for the ban.")
    @app_commands.describe(delete_message_days="Number of days of messages to delete on ban.")
    async def tempban(self, interaction: discord.Interaction, user: discord.Member, duration_minutes: int, reason: str = "Temporary Ban", delete_message_days: app_commands.Range[int, 0, 7] = 0):
        """Bans a user for a set time, then unbans them."""

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You do not have the required permissions (Ban Members).", ephemeral=True)
            return

        if interaction.user == user:
            await interaction.response.send_message("You cannot tempban yourself.", ephemeral=True)
            return

        if interaction.guild.me == user:
            await interaction.response.send_message("I cannot tempban myself.", ephemeral=True)
            return

        if interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot tempban someone with an equal or higher role than yourself.", ephemeral=True)
            return

        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message("I cannot tempban someone with an equal or higher role than myself.", ephemeral=True)
            return

        duration = datetime.timedelta(minutes=duration_minutes)

        try:
            await interaction.guild.ban(user, reason=reason, delete_message_days=delete_message_days)
            await interaction.response.send_message(f"{user.mention} has been temporarily banned for {duration_minutes} minutes. Reason: {reason}", ephemeral=True)

            await asyncio.sleep(duration_minutes * 60)

            await interaction.guild.unban(user, reason="Temporary ban expired.")
            await interaction.followup.send(f"{user.mention} has been unbanned.", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("I do not have the necessary permissions.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class BanConfirmation(discord.ui.View):
    def __init__(self, banned_user: discord.Member, reason: str, moderator: discord.User, bot: commands.Bot, delete_message_days: int):
        super().__init__()
        self.banned_user = banned_user
        self.reason = reason
        self.moderator = moderator
        self.bot = bot
        self.delete_message_days = delete_message_days

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirms the ban and sends it."""
        if interaction.user != self.moderator:
            await interaction.response.send_message("Only the command invoker can confirm.", ephemeral=True)
            return

        try:
            await self.banned_user.ban(reason=self.reason, delete_message_days=self.delete_message_days)
            await interaction.response.edit_message(embed=discord.Embed(title="User Banned", description=f"{self.banned_user.mention} has been banned.\nReason: {self.reason}", color=discord.Color.green()), view=None)

        except discord.Forbidden:
            await interaction.response.edit_message(embed=discord.Embed(title="Ban Failed", description=f"I do not have permissions to ban {self.banned_user.mention}.", color=discord.Color.red()), view=None)
        except Exception as e:
            await interaction.response.edit_message(embed=discord.Embed(title="Ban Failed", description=f"An error occurred: {e}", color=discord.Color.red()), view=None)
            print(f"Ban command error: {e}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancels the ban."""
        if interaction.user != self.moderator:
            await interaction.response.send_message("Only the command invoker can cancel.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=discord.Embed(title="Ban Cancelled", description="The ban has been cancelled.", color=discord.Color.light_grey()), view=None)

async def setup(bot):
    await bot.add_cog(Ban(bot))