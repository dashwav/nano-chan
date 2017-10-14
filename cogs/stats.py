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
    async def download_guild_history(self, ctx):
        """
        This will go through all the channels
        and download them.
        """
        confirm = await helpers.custom_confirm(
            ctx,
            f'\nAre you sure you want to do this?'
            ' This will literally take just about forever. Like days maybe.\n')
        if not confirm:
            return
        confirm2 = await helpers.custom_confirm(
            ctx,
            f'\nSeriously this is going to take at least 4 hours,'
            ' and it could even go up to a week. Only respond with'
            ' confirm if you **really** mean it\n')
        if not confirm2:
            return
        self.bot.logger.info(
            f'Starting to pull messages, this will take a while')
        totalcount = 0
        errorcount = 0
        for ch in ctx.message.guild.channels:
            if isinstance(ch, discord.TextChannel): 
                self.bot.logger.info(
                    f'Downloading messages from: {ch.name}')
                try:
                    message_history = ch.history(
                        limit=None, reverse=True)
                except Exception as e:
                    self.bot.logger.warning(
                        f'Issue getting channel history: {e}')
                    continue
                async for message in message_history:
                    totalcount += 1
                    try:
                        await self.bot.postgres_controller.add_message(
                            message
                        )
                    except Exception as e:
                        errorcount += 0
                        self.bot.logger.warning(
                            f'Issue while putting message in database: {e}')
        await ctx.send(f'<@{ctx.message.author.id}>\n'
                       f'\n L-look, i did what you wanted... (⁄ ⁄•⁄ ⁄•⁄ ⁄)⁄\n'
                       f'Total Messages processed: {totalcount}\n'
                       f'Errors encountered: {errorcount}')
