"""
Fun things with stats
"""
import discord
import datetime
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
        self.editible_posts = []

    async def on_message(self, message):
        if not isinstance(message.channel, discord.TextChannel):
            return
        found_emojis = []
        confirmed_emojis = []
        if message.channel.id == 191102386633179136:
            return
        for word in message.content.split():
            if '<:' or '<a:' in word:
                found_emojis.append(word)
        for emoji_id in found_emojis:
            for emoji in message.guild.emojis:
                if emoji_id == str(emoji):
                    confirmed_emojis.append(emoji)
        try:
            for emoji in confirmed_emojis:
                await self.bot.postgres_controller.add_emoji(
                    emoji, message.id, message.author, message.author, message.channel, False, emoji.animated)
        except Exception as e:
            self.bot.logger.warning(f'Error adding emoji to db: {e}')

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        """
        Called when an emoji is added
        """
        channel = self.bot.get_channel(channel_id)
        user = self.bot.get_user(user_id)
        message = await channel.get_message(message_id)
        for server_emoji in channel.guild.emojis:
            if emoji.id == server_emoji.id:
                await self.bot.postgres_controller.add_emoji(
                    emoji, message_id, user, message.author, channel, True, emoji.animated)

    @commands.group(aliases=['s'])
    @commands.guild_only()
    @checks.is_admin()
    async def stats(self, ctx):
        """
        This is the base command for the fun shit
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('bruh thats not even a command')

    @stats.command()
    async def user(self, ctx, user: discord.Member):
        """
        Returns stats on a user
        """
        user_count = defaultdict(int)
        target_count = defaultdict(int)
        stats = await self.bot.postgres_controller.get_user_emojis(user)
        for record in stats['user']:
            user_count[record['emoji_name']] += 1
        for record in stats['target']:
            target_count[record['emoji_name']] += 1
        temp_str = 'Most used emoji:\n'
        for key in sorted(user_count, key=user_count.get, reverse=True):
            temp_str += f'{key}: {user_count[key]}\n'
        temp_str = f'\n\n Most whatever thing'
        for key in sorted(target_count, key=target_count.get, reverse=True):
            temp_str += f'{key}: {target_count[key]}\n'
        local_embed = discord.Embed(
            title=f'Stats for {user.mention}',
            description= temp_str
        )
        await ctx.send(embed=local_embed)


    @commands.command()
    @checks.has_permissions(manage_emojis=True)
    async def emojis(self, ctx, days: int=1):
        count_dict = defaultdict(int)
        for emoji in ctx.guild.emojis:
            try:
                count_dict[emoji] = await \
                    self.bot.postgres_controller.get_emoji_count(
                        emoji, days, self.bot.logger
                    )
            except Exception as e:
                self.bot.logger(f'Error getting emoji info:{e}')
        desc = ''
        for key in sorted(count_dict, key=count_dict.get, reverse=True):
            desc += f'{key}: {count_dict[key]}\n'
        local_embed = discord.Embed(
            title=f'Emoji use over the past {days} day/s:',
            description=desc
        )
        await ctx.send(embed=local_embed)
            

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
                if ch.id in {148609211977302017, 149945199873884160, 266805623579082758, 266805579115134976}:
                    continue 
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
                    if message.author.bot:
                        continue
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
