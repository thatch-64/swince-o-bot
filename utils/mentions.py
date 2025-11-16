import re
from collections import Counter
from typing import List
import discord

def format_mentions(users) -> str:
    counts = Counter(users)
    return ', '.join(
        f"{user.mention} ({count}x)" if count > 1 else user.mention
        for user, count in counts.items()
    )

def extract_mentions(message: discord.Message, guild: discord.Guild) -> List[discord.Member]:
    mention_ids = re.findall(r'<@!?(\d+)>', message.content)
    return [
        guild.get_member(int(user_id))
        for user_id in mention_ids
        if guild.get_member(int(user_id))
    ]
