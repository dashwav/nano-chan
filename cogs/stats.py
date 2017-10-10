"""
Fun things with stats
"""
import discord
import datetime
import calendar
from dateutil.relativedelta import relativedelta
from collections import defaultdict
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
    async def stats_emoji(self, ctx):
        found_emojis = []
        total_reactions = defaultdict(int)
        emoji_count = defaultdict(int)
        check_date = datetime.datetime.now() + datetime.timedelta(-30)
        for channel in ctx.message.guild.channels:
            if isinstance(channel, discord.TextChannel):
                self.bot.logger.info(f'Starting on channel: {channel.name}')
                if channel.id in self.bot.emoji_ignore_channels:
                    continue
                try:
                    message_history = channel.history(
                        limit=None, after=check_date)
                except Exception as e:
                    self.bot.logger.warning(
                        f'Issue getting channel history: {e}')
                self.bot.logger.info(f'Parsing messages: {channel.name}')        
                async for message in message_history:
                    for word in message.content.split():
                        if '<:' in word:
                            found_emojis.append(word)
                    for reaction in message.reactions:
                        total_reactions[reaction.emoji] += reaction.count
        self.bot.logger.info(f'Counting emojis: {channel.name}')
        for emoji_id in found_emojis:
            for emoji in ctx.message.guild.emojis:
                if emoji_id == str(emoji):
                    emoji_count[emoji] += 1
        for emoji in ctx.message.guild.emojis:
            if emoji in total_reactions:
                emoji_count[emoji] += total_reactions[emoji]
        temp_str = 'Emoji use over last 30 days:\n'
        for key in sorted(emoji_count, key=emoji_count.get, reverse=True):
            temp_str += f'{key}: {emoji_count[key]}\n'
        await ctx.send(temp_str)

    @commands.command()
    @checks.is_admin()
    async def stats_traffic(self, ctx):
        """
        This will go through all the channels 
        and create a graph of channel usage over time
        """
        channel_traffic_month = {}
        channel_traffic_total = {}
        self.bot.logger.info(f'Starting stats.')
        today = datetime.datetime.today()
        first_day = today.replace(day=1)
        for i in range(1, 2):
            prev_month = first_day - relativedelta(months=i)
            prev_month_end = prev_month + relativedelta(months=1)
            self.bot.logger.info(
                f'Getting stats from {prev_month} to {prev_month_end}')
            for ch in ctx.message.guild.channels:
                totalcount = 0
                if isinstance(ch, discord.TextChannel):
                    self.bot.logger.info(
                        f'Getting channel history: {ch.name}')
                    if ch.id in self.bot.traffic_ignore_channels:
                        continue
                    elif ch.category_id in self.bot.traffic_ignore_channels:
                        continue
                    try:
                        message_history = ch.history(
                            limit=None,
                            before=prev_month_end,
                            after=prev_month)
                    except Exception as e:
                        self.bot.logger.warning(
                            f'Issue getting channel history: {e}')
                        continue
                    self.bot.logger.info(
                        f'Counting messages: {ch.name}')
                    async for message in message_history:
                        self.bot.logger.info(f'{message}')
                        totalcount += 1
                    channel_traffic_month.update({ch.name:totalcount})
            channel_traffic_total.update({calendar.month_abbr[i]:channel_traffic_month})
        self.bot.logger.info(f'Traffic info: {channel_traffic_total}')
