import discord
from discord.ext import commands
from discord import app_commands

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a user from the server.")
    @app_commands.describe(user="The user to kick.")
    @app_commands.describe(reason="The reason for the kick.")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided."):
        """Kicks a user with an interactive confirmation. Requires kick permissions."""

        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("You do not have the required permissions (Kick Members).", ephemeral=True)
            return

        if interaction.user == user:
            await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
            return

        if interaction.guild.me == user:
            await interaction.response.send_message("I cannot kick myself.", ephemeral=True)
            return

        if interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot kick someone with an equal or higher role than yourself.", ephemeral=True)
            return

        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message("I cannot kick someone with an equal or higher role than myself.", ephemeral=True)
            return

        # Confirmation Embed
        embed = discord.Embed(title="Confirm Kick", description=f"Are you sure you want to kick {user.mention}?\n\n**Reason:** {reason}", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, view=KickConfirmation(user, reason, interaction.user, self.bot), ephemeral=True)

class KickConfirmation(discord.ui.View):
    def __init__(self, kicked_user: discord.Member, reason: str, moderator: discord.User, bot:commands.Bot):
        super().__init__()
        self.kicked_user = kicked_user
        self.reason = reason
        self.moderator = moderator
        self.bot = bot

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirms the kick and sends it."""
        if interaction.user != self.moderator:
            await interaction.response.send_message("Only the command invoker can confirm.", ephemeral=True)
            return

        try:
            await self.kicked_user.kick(reason=self.reason)
            await interaction.response.edit_message(embed=discord.Embed(title="User Kicked", description=f"{self.kicked_user.mention} has been kicked.\nReason: {self.reason}", color=discord.Color.green()), view=None)

        except discord.Forbidden:
            await interaction.response.edit_message(embed=discord.Embed(title="Kick Failed", description=f"I do not have permissions to kick {self.kicked_user.mention}.", color=discord.Color.red()), view=None)
        except Exception as e:
            await interaction.response.edit_message(embed=discord.Embed(title="Kick Failed", description=f"An error occurred: {e}", color=discord.Color.red()), view=None)
            print(f"Kick command error: {e}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancels the kick."""
        if interaction.user != self.moderator:
            await interaction.response.send_message("Only the command invoker can cancel.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=discord.Embed(title="Kick Cancelled", description="The kick has been cancelled.", color=discord.Color.light_grey()), view=None)

async def setup(bot):
    await bot.add_cog(Kick(bot))