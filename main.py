import dotenv
import os
from bot_core import bot

dotenv.load_dotenv()


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
