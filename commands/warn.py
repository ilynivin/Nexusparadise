import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os

# setup basic logging.
logging.basicConfig(level=logging.INFO)

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warns = self.load_warns()

    def load_warns(self):
        try:
            filepath = r"C:\Users\nivin\OneDrive\Desktop\Nexisusbot\warns.json"  # Raw string for Windows path
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_warns(self):
        try:
            filepath = r"C:\Users\nivin\OneDrive\Desktop\Nexisusbot\warns.json"  # Raw string for Windows path
            with open(filepath, 'w') as f:
                json.dump(self.warns, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving warns.json: {e}")

    @app_commands.command(name="warn", description="Warn a user.")
    @app_commands.describe(user="The user to warn.")
    @app_commands.describe(reason="The reason for the warning.")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided."):
        """Warns a user with an interactive confirmation. Requires kick or mute permissions."""

        if not interaction.user.guild_permissions.kick_members and not interaction.user.guild_permissions.mute_members:
            await interaction.response.send_message("You do not have the required permissions (Kick or Mute).", ephemeral=True)
            return

        embed = discord.Embed(title="Confirm Warning", description=f"Are you sure you want to warn {user.mention}?\n\n**Reason:** {reason}", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, view=WarnConfirmation(user, reason, interaction.user, self.bot, self.warns, self.save_warns), ephemeral=True)

    @app_commands.command(name="warns", description="Show a user's warnings.")
    @app_commands.describe(user="The user to show warnings for.")
    async def warns_command(self, interaction: discord.Interaction, user: discord.Member):
        """Shows a user's warnings. Requires kick or mute permissions."""

        if not interaction.user.guild_permissions.kick_members and not interaction.user.guild_permissions.mute_members:
            await interaction.response.send_message("You do not have the required permissions (Kick or Mute).", ephemeral=True)
            return

        user_id = str(user.id)
        guild_id = str(interaction.guild.id)
        print(f"Warns: User ID: {user_id}, Guild ID: {guild_id}")  # Debug print

        if user_id in self.warns and guild_id in self.warns[user_id]:
            guild_warns = self.warns[user_id][guild_id]
            print(f"Guild Warns: {guild_warns}") # Debug print
            if guild_warns:
                embed = discord.Embed(title=f"Warnings for {user.name}", color=discord.Color.blue())
                for i, warn in enumerate(guild_warns, 1):
                    embed.add_field(name=f"Warn {i}", value=f"Reason: {warn['reason']}\nModerator: <@{warn['moderator']}>", inline=False)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"{user.mention} has no warnings in this server.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.mention} has no warnings in this server.", ephemeral=True)

    @app_commands.command(name="delwarn", description="Delete a warning from a user.")
    @app_commands.describe(user="The user to delete the warning from.")
    @app_commands.describe(warn_number="The number of the warning to delete.")
    async def delwarn_command(self, interaction: discord.Interaction, user: discord.Member, warn_number: int):
        """Deletes a specific warning from a user."""

        if not interaction.user.guild_permissions.kick_members and not interaction.user.guild_permissions.mute_members:
            await interaction.response.send_message("You do not have the required permissions (Kick or Mute).", ephemeral=True)
            return

        user_id = str(user.id)
        guild_id = str(interaction.guild.id)

        if user_id in self.warns and guild_id in self.warns[user_id]:
            guild_warns = self.warns[user_id][guild_id]
            if 1 <= warn_number <= len(guild_warns):
                deleted_warn = guild_warns.pop(warn_number - 1)  # Remove the warning
                self.save_warns()
                await interaction.response.send_message(f"Warning {warn_number} deleted: {deleted_warn['reason']}.", ephemeral=True)
            else:
                await interaction.response.send_message("Invalid warning number.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.mention} has no warnings in this server.", ephemeral=True)

class WarnConfirmation(discord.ui.View):
    def __init__(self, warned_user: discord.Member, reason: str, moderator: discord.User, bot: commands.Bot, warns: dict, save_warns):
        super().__init__()
        self.warned_user = warned_user
        self.reason = reason
        self.moderator = moderator
        self.bot = bot
        self.warns = warns
        self.save_warns = save_warns

    async def _check_moderator(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.moderator:
            await interaction.response.send_message("Only the command invoker can perform this action.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_moderator(interaction):
            return

        user_id = str(self.warned_user.id)
        guild_id = str(interaction.guild.id)

        if user_id not in self.warns:
            self.warns[user_id] = {}
        if guild_id not in self.warns[user_id]:
            self.warns[user_id][guild_id] = []

        self.warns[user_id][guild_id].append({
            "reason": self.reason,
            "moderator": str(self.moderator.id)
        })

        print(f"Warns after adding: {self.warns}")  # Debug print
        self.save_warns()

        try:
            await self.warned_user.send(f"You have been warned in {interaction.guild.name} by {self.moderator.name}#{self.moderator.discriminator}.\nReason: {self.reason}")
            await interaction.response.edit_message(embed=discord.Embed(title="User Warned", description=f"{self.warned_user.mention} has been warned.\nReason: {self.reason}", color=discord.Color.green()), view=None)

        except discord.Forbidden:
            await interaction.response.edit_message(embed=discord.Embed(title="Warning Failed", description=f"Could not send a DM to {self.warned_user.mention}. Check their privacy settings.", color=discord.Color.red()), view=None)
        except Exception as e:
            await interaction.response.edit_message(embed=discord.Embed(title="Warning Failed", description=f"An unknown error occurred: {type(e).__name__} - {e}", color=discord.Color.red()), view=None)
            logging.error(f"Warn command error: {e}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_moderator(interaction):
            return
        await interaction.response.edit_message(embed=discord.Embed(title="Warning Cancelled", description="The warning has been cancelled.", color=discord.Color.light_grey()), view=None)

async def setup(bot):
    await bot.add_cog(Warn(bot))