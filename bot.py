import discord
import os
import asyncio
import json
from discord.ext import commands
from discord import app_commands

class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.initial_extensions = [f'commands.{filename[:-3]}' for filename in os.listdir('./commands') if filename.endswith('.py')]

    async def setup_hook(self):
        # Load command modules
        for extension in self.initial_extensions:
            try:
                print(f'Loaded\t{extension}!')
                await self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}: {e}')

              

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')
        print(f'Bot Ready!')
        stream = discord.Streaming(
            name="NEXUS PARADISE!",
            url="https://www.twitch.tv/pug_isop",
            platform="Twitch"

        )
        await bot.change_presence(activity=stream)
        
        
        await self.tree.sync()
        try:
            with open('./config.json') as f:
                config = json.load(f)
                self.report_channel_id = config.get('report_channel_id')
                if self.report_channel_id:
                    self.report_channel_id = int(self.report_channel_id)
        except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error loading report_channel_id: {e}")
        

    async def on_disconnect(self):
        print(f'{self.user.name} has disconnected.')


intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

# Load the bot token from config.json
try:
    with open('./config.json') as f:
        config = json.load(f)
        token = config['Token']
except FileNotFoundError:
    print("config.json not found")
    exit(1)
except KeyError:
    print("Token not found in config.json")
    exit(1)
except json.JSONDecodeError:
    print("Invalid JSON in config.json")
    exit(1)
except Exception as e:
    print(f"An Error Occured: {e}")
    exit(1)

bot = MyBot(command_prefix="nx!", intents=intents)
### Context Menu 

@bot.tree.context_menu(name="User Info")
async def user_info(interaction: discord.Interaction, user: discord.Member):
    """Displays information about a user."""
    embed = discord.Embed(title=f"User Info - {user.name}", color=user.color)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.add_field(name="ID", value=user.id, inline=False)
    embed.add_field(name="Nickname", value=user.nick if user.nick else "None", inline=False)
    embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Roles", value=", ".join([role.mention for role in user.roles[1:]]) if len(user.roles) > 1 else "None", inline=False)
    embed.add_field(name="Top Role", value=user.top_role.mention, inline=False)
    embed.add_field(name="Is Bot?", value=user.bot, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.context_menu(name="User Roles")
async def user_roles(interaction: discord.Interaction, user: discord.Member):
    """Displays the roles of a user."""
    roles = ", ".join([role.mention for role in user.roles[1:]]) if len(user.roles) > 1 else "None"
    embed = discord.Embed(title=f"Roles of {user.name}", description=roles, color=user.color)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.context_menu(name="Report Message")
async def report_message(interaction: discord.Interaction, message: discord.Message):
    """Reports a message to the moderation team."""
    if not bot.report_channel_id: #Access through bot
        await interaction.response.send_message("The report channel has not been configured.", ephemeral=True)
        return

    report_channel = bot.get_channel(bot.report_channel_id) #Access through bot
    if not report_channel:
        await interaction.response.send_message("The report channel could not be found.", ephemeral=True)
        return

    embed = discord.Embed(title="Message Report", description=f"Message reported by {interaction.user.mention} in {message.channel.mention}.", color=discord.Color.red())
    embed.add_field(name="Message Content", value=message.content if message.content else "No message content", inline=False)
    embed.add_field(name="Message Author", value=message.author.mention, inline=False)
    embed.add_field(name="Message ID", value=message.id, inline=False)
    embed.add_field(name="Reporter User ID", value=interaction.user.id, inline=False)
    embed.add_field(name="Message Link", value=message.jump_url, inline=False)
    await report_channel.send(embed=embed)
    await interaction.response.send_message("Message reported successfully.", ephemeral=True)

bot.run(token)