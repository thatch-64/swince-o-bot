
import discord

class Bot(discord.Client):
    async def on_ready(self):
        print(f'Logged in successfully as {self.user.name}')
