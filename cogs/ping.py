import time
import discord

from discord.ext import commands

class PingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="ping", description="Check the bot's latency")
    async def ping(self, ctx):
        start = time.perf_counter()
        await ctx.respond("Pong!", ephemeral=True)
        end = time.perf_counter()
        latency = (end - start) * 1000
        await ctx.edit(content=f"Pong! ({latency:.2f} ms)")

def setup(bot):
    bot.add_cog(PingCommand(bot))
