import discord
from discord.ext import commands
from discord import app_commands

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a poll with reactions.")
    @app_commands.describe(question="The poll question.")
    @app_commands.describe(options="Comma-separated list of poll options.")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        """Creates a poll with reactions."""

        options_list = [opt.strip() for opt in options.split(',')]
        if len(options_list) > 20:  # Discord reaction limit
            await interaction.response.send_message("You can only have up to 20 poll options.", ephemeral=True)
            return

        embed = discord.Embed(title="Poll", description=question, color=discord.Color.blue())
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
                     "🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯"] #20 reactions

        for i, option in enumerate(options_list):
            embed.add_field(name=reactions[i], value=option, inline=False)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response() #get the message object.

        for i in range(len(options_list)):
            await message.add_reaction(reactions[i])

async def setup(bot):
    await bot.add_cog(Poll(bot))