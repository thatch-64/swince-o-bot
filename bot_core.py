import discord

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


def load_cogs():
    bot.load_extension('cogs.ping')

load_cogs()
