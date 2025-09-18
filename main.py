import os
import dotenv
import discord

from bot import Bot

dotenv.load_dotenv()
TOKEN: str = os.getenv('DISCORD_TOKEN')

bot_intents = discord.Intents.default()

bot_intents.message_content = True
bot_intents.guilds = True
bot_intents.members = True

client = Bot(intents=bot_intents)
client.run(TOKEN)
