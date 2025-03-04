import discord
from discord.ext import commands
from discord import app_commands
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_category_id = None
        self.ticket_role_id = None
        self.transcript_channel_id = None
        self.dev_ids = []  # List of developer IDs
        self.guild_owner_id = None  # Guild Owner ID

    async def cog_load(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.ticket_category_id = config.get('ticket_category_id')
                self.ticket_role_id = config.get('ticket_role_id')
                self.transcript_channel_id = config.get('transcript_channel_id')
                self.dev_ids = config.get('dev_ids', [])  # Get dev IDs or empty list
                self.guild_owner_id = config.get('guild_owner_id')

                if self.ticket_category_id:
                    self.ticket_category_id = int(self.ticket_category_id)
                if self.ticket_role_id:
                    # Handle ticket_role_id as a list or single ID
                    if isinstance(self.ticket_role_id, list):
                        self.ticket_role_id = [int(role_id) for role_id in self.ticket_role_id]
                    else:
                        self.ticket_role_id = int(self.ticket_role_id)
                if self.transcript_channel_id:
                    self.transcript_channel_id = int(self.transcript_channel_id)
                if self.guild_owner_id:
                    self.guild_owner_id = int(self.guild_owner_id)

        except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error loading ticket configuration: {e}")

    def is_dev_or_owner(self, user_id):
        """Checks if a user is a developer or the guild owner."""
        return user_id in self.dev_ids or user_id == self.guild_owner_id

    @app_commands.command(name="panel", description="Sends a message with a button to create tickets.")
    async def panel(self, interaction: discord.Interaction):
        """Sends a message with a button to create tickets."""

        if not self.is_dev_or_owner(interaction.user.id) and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        embed = discord.Embed(title="Create a Support Ticket", description="Click the button below to create a support ticket.", color=discord.Color.blue())
        view = TicketButtonView(self.bot, self.ticket_category_id, self.ticket_role_id, timeout=None)  # Added timeout=None
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Ticket(bot))

class TicketButtonView(discord.ui.View):
    def __init__(self, bot, category_id, role_id, *, timeout=None):  # Added timeout.
        super().__init__(timeout=timeout)
        self.bot = bot
        self.category_id = category_id
        self.role_id = role_id

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()  # Defer the response immediately

        if not self.category_id:
            await interaction.followup.send("Ticket system is not configured. Please contact an administrator.", ephemeral=True)
            return

        category = self.bot.get_channel(self.category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("Invalid ticket category. Please contact an administrator.", ephemeral=True)
            return

        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            if self.role_id:
                # Handle self.role_id as a list or single ID
                if isinstance(self.role_id, list):
                    for role_id in self.role_id:
                        role = interaction.guild.get_role(role_id)
                        if role:
                            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
                else:
                    role = interaction.guild.get_role(self.role_id)
                    if role:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)

            channel = await category.create_text_channel(name=f"ticket-{interaction.user.name}", overwrites=overwrites)
            await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)  # Send the real message.

            embed = discord.Embed(title="Support Ticket", description=f"Welcome to your support ticket, {interaction.user.mention}!\nPlease describe your issue.", color=discord.Color.blue())
            await channel.send(embed=embed)
            if self.role_id:
                # Handle self.role_id as a list or single ID
                if isinstance(self.role_id, list):
                    role = interaction.guild.get_role(self.role_id[0]) # Get the first role for pinging.
                else:
                    role = interaction.guild.get_role(self.role_id)

                if role:
                    await channel.send(f"Support team: {role.mention}")
            await channel.send(view=TicketCloseButtonView(self.bot, self.bot.get_cog("Ticket").transcript_channel_id, timeout=None))  # Added timeout=None.

        except discord.Forbidden:
            await interaction.followup.send("I do not have the necessary permissions to create a ticket.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

class TicketCloseButtonView(discord.ui.View):
    def __init__(self, bot, transcript_channel_id, *, timeout=None):  # Added timeout.
        super().__init__(timeout=timeout)
        self.bot = bot
        self.transcript_channel_id = transcript_channel_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()  # Defer the response immediately.
        channel = interaction.channel
        try:
            messages = []
            async for message in channel.history(limit=None, oldest_first=True):
                messages.append(f"{message.author.name}: {message.content}")

            transcript = "\n".join(messages)

            if self.transcript_channel_id:
                transcript_channel = self.bot.get_channel(self.transcript_channel_id)
                if transcript_channel:
                    await transcript_channel.send(f"Transcript for {channel.name}:\n```{transcript}```")

            await interaction.followup.send("Ticket closed successfully.", ephemeral=True)  # Send confirmation.
            await channel.delete()

        except discord.Forbidden:
            await interaction.followup.send("I do not have the necessary permissions.", ephemeral=True)
        except discord.errors.HTTPException as e:
            if e.code == 10003:  # Unknown channel
                logging.warning(f"Attempted to send message to deleted channel: {channel.id}")
            else:
                await interaction.followup.send(f"An error occurred: {e}",ephemeral=True)
