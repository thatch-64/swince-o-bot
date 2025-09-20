
import discord
import re

from discord.ext import commands
from collections import Counter

# Utility function to format mentions with counts
def format_mentions(users) -> str:
    counts = Counter(users)
    return ', '.join(
        f"{user.mention} ({count}x)" if count > 1 else user.mention
        for user, count in counts.items()
    )

# Utility function to extract mentioned users from a message
def extract_mentions(message, guild) -> list:
    mention_ids = re.findall(r'<@!?(\d+)>', message.content)
    return [
        guild.get_member(int(user_id))
        for user_id in mention_ids
        if guild.get_member(int(user_id))
    ]

class SwinceCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="swince", description="Envoyez une swince !")
    async def submit_video(self, ctx):
        await ctx.respond(
            "Merci de soumettre votre vidéo ! Veuillez envoyer votre vidéo en pièce jointe ou via un lien.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if the message is a swince submission (video attachment or link)
        if (
            not message.reference and (
                any(
                    a.content_type and a.content_type.startswith("video")
                    for a in message.attachments
                ) or message.content.endswith((".mp4", ".mov", ".avi"))
            )
        ):
            prompt_msgs = [
                "merci de mentionner toutes les personnes présente dans la swince (ex: @personne-1, @personne-2).",
                "maintenant merci de mentionner les personnes nominées (ex: @nominé-1, @nominé-2)."
            ]
            replies = []

            for prompt in prompt_msgs:

                prompt_msg = await message.channel.send(f"{message.author.mention}, {prompt}")

                def check(m):
                    return m.author == message.author and m.channel == message.channel and m.mentions

                try:

                    reply = await self.bot.wait_for("message", check=check, timeout=60)
                    replies.append((prompt_msg, reply))

                except Exception:

                    await message.channel.send("Timeout ou aucune mention détectée. Veuillez réessayer.")
                    return

            present_users = extract_mentions(replies[0][1], message.guild)
            nominees = extract_mentions(replies[1][1], message.guild)

            await message.channel.send(f"Merci ! Swinceur(s): {format_mentions(present_users)} | Nominé(s) : {format_mentions(nominees)}")

            for prompt_msg, reply in replies:
                await prompt_msg.delete()
                await reply.delete()

def setup(bot):
    bot.add_cog(SwinceCommand(bot))
