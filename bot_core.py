
import db
import discord

bot = discord.Bot(intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


def load_cogs():
    bot.load_extension('cogs.ping')
    bot.load_extension('cogs.swince')


load_cogs()
db.init_db()