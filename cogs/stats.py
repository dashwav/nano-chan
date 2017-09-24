"""
Fun things with stats
"""
import re
import discord
import datetime
from .utils import helpers, checks
from discord.ext import commands

class Stats:
    """
    Main stats class
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.command()
    @checks.has_permissions(manage_emojis=True)
    async def stats_reactions(self, ctx):
        emoji_list = []
        for emoji in ctx.message.guild.emojis:
            emoji_list.append(
                {
                    'emoji_name': emoji.name,
                    'emoji_id': emoji.id,
                    'count': 0
                }
            )
        print(emoji_list)
        check_date = datetime.datetime.now() + datetime.timedelta(-30)
        for channel in ctx.message.guild.channels:
            try:
                message_history = channel.history(after=check_date)
            except Exception as e:
                self.bot.logger.warning(f'Issue getting channel history: {e}')
            async for message in message_history:
                for word in message.content.split():
                    if '<:' in word:
                        word = re.sub(r'\:(.*?)\:', ' ', word)
                        word = re.sub(r'[<>]', '', word)
                        print(word)
