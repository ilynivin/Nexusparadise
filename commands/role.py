import discord
from discord.ext import commands
from discord import app_commands

class Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giverole", description="Give a user a role.")
    @app_commands.describe(user="The user to give the role to.")
    @app_commands.describe(role="The role to give.")
    async def giverole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Gives a user a role."""

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have the required permissions (Manage Roles).", ephemeral=True)
            return

        if interaction.guild.me.top_role <= role:
            await interaction.response.send_message("I cannot assign a role that is higher or equal to my highest role.", ephemeral=True)
            return

        if interaction.user.top_role <= role:
            await interaction.response.send_message("You cannot assign a role that is higher or equal to your highest role.", ephemeral=True)
            return

        try:
            await user.add_roles(role)
            await interaction.response.send_message(f"Successfully given the {role.mention} role to {user.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have the necessary permissions to assign this role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while assigning the role: {e}", ephemeral=True)

    @app_commands.command(name="removerole", description="Remove a role from a user.")
    @app_commands.describe(user="The user to remove the role from.")
    @app_commands.describe(role="The role to remove.")
    async def removerole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Removes a role from a user."""

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have the required permissions (Manage Roles).", ephemeral=True)
            return

        try:
            await user.remove_roles(role)
            await interaction.response.send_message(f"Successfully removed the {role.mention} role from {user.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have the necessary permissions to remove this role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while removing the role: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Role(bot))