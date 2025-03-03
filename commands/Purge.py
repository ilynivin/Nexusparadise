import discord
from discord.ext import commands
from discord import app_commands

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge", description="Delete a specified number of messages (up to 45).")
    @app_commands.describe(count="The number of messages to delete (1-45).")
    async def purge(self, interaction: discord.Interaction, count: app_commands.Range[int, 1, 45]):
        

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have the required permissions (Manage Messages).", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await interaction.channel.purge(limit=count + 1)
            await interaction.followup.send(f"Deleted {len(deleted) - 1} messages.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I do not have the necessary permissions to delete messages.", ephemeral=True)
        except discord.HTTPException:
            await interaction.followup.send("An error occurred while deleting messages.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An unknown error occurred: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Purge(bot))