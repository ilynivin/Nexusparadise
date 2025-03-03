import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OnLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.on_leave_role_id = None
        self.staff_role_id = None
        self.on_leave_message = "This staff member is currently on leave. Please expect delayed responses."
        self.leave_users = set()
        self.load_config()
        self.load_leave_users()

    def load_config(self):
        try:
            config_file_path = r"C:\Users\nivin\OneDrive\Desktop\Nexisusbot\config.json" #Raw string.
            with open(config_file_path, 'r') as f:
                config = json.load(f)
                self.on_leave_role_id = int(config.get('on_leave_role_id'))
                self.staff_role_id = int(config.get('staff_role_id'))
                self.on_leave_message = config.get('on_leave_message', self.on_leave_message)
        except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error loading on_leave configuration: {e}")

    def load_leave_users(self):
        try:
            leaves_file_path = r"C:\Users\nivin\OneDrive\Desktop\Nexisusbot\leaves.json" #Raw string.
            with open(leaves_file_path, 'r') as f:
                self.leave_users = set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            self.leave_users = set()

    def save_leave_users(self):
        try:
            leaves_file_path = r"C:\Users\nivin\OneDrive\Desktop\Nexisusbot\leaves.json" #Raw string.
            with open(leaves_file_path, 'w') as f:
                json.dump(list(self.leave_users), f)
        except FileNotFoundError:
            logging.error("leaves.json not found at the specified path")
        except Exception as e:
            logging.error(f"Error saving leaves.json: {e}")

    @app_commands.command(name="setleave", description="Sets your status to on leave.")
    async def setleave(self, interaction: discord.Interaction):
        if not self.on_leave_role_id or not self.staff_role_id:
            await interaction.response.send_message("On leave system is not configured. Contact an administrator.", ephemeral=True)
            return

        staff_role = interaction.guild.get_role(self.staff_role_id)
        if not staff_role or staff_role not in interaction.user.roles:
            await interaction.response.send_message("You must be a staff member to use this command.", ephemeral=True)
            return

        role = interaction.guild.get_role(self.on_leave_role_id)
        if not role:
            await interaction.response.send_message("Invalid on leave role. Contact an administrator.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id in self.leave_users:
            self.leave_users.remove(user_id)
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("Your on leave status has been removed.", ephemeral=True)
        else:
            self.leave_users.add(user_id)
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Your on leave status has been set.", ephemeral=True)

        self.save_leave_users()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        for member in message.mentions:
            if member.id in self.leave_users:
                try:
                    await message.channel.send(f"{member.mention} {self.on_leave_message}")
                except discord.Forbidden:
                    logging.error("I do not have permissions to send messages.")
                except Exception as e:
                    logging.error(f"Error sending on leave message: {e}")

async def setup(bot):
    await bot.add_cog(OnLeave(bot))