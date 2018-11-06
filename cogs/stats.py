"""
Fun things with stats
"""
import discord
import datetime
from collections import defaultdict
from .utils import helpers, checks
from discord.ext import commands

ALLOWED_CHANNELS = [
    378684962934751239,
    282640120388255744,
    220762067739738113,
    176429411443146752,
]

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

    async def on_raw_reaction_add(self, payload):
        """
        Called when an emoji is added
        """
        channel = self.bot.get_channel(payload.channel_id)
        user = self.bot.get_user(payload.user_id)
        message = await channel.get_message(payload.message_id)
        for server_emoji in channel.guild.emojis:
            if payload.emoji.id == server_emoji.id:
                await self.bot.postgres_controller.add_emoji(
                    payload.emoji, payload.message_id, user, message.author, channel, True, payload.emoji.animated)

    @commands.group(aliases=['s'])
    @commands.guild_only()
    async def stats(self, ctx):
        """
        This is the base command for the fun shit
        """
        if ctx.message.channel.id not in ALLOWED_CHANNELS:
            return
        if ctx.invoked_subcommand is None:
            await ctx.send('bruh thats not even a command')

    @stats.command()
    async def me(self, ctx, days: int=-1):
        """
        Returns stats on a user
        """
        if ctx.message.channel.id not in [220762067739738113,176429411443146752]:
            return
        user = ctx.message.author
        user_count = defaultdict(int)
        target_count = defaultdict(int)
        stats = await self.bot.postgres_controller.get_user_emojis(user, days)
        for record in stats['user']:
            if record['channel_id'] in [297834395945926667, 329500167118258176, 294248007422181376, 148606162810568704, 227385793637777408, 264704915845283840, 191102386633179136, 378684962934751239, 232371423069339648, 343953048940314625]: #nsfw-roleplay, meta, brainpower
                continue
            user_count[record['emoji_id']] += 1
        for record in stats['target']:
            if record['channel_id'] in [297834395945926667, 329500167118258176, 294248007422181376, 148606162810568704, 227385793637777408, 264704915845283840, 191102386633179136, 378684962934751239, 232371423069339648, 343953048940314625]: #nsfw-roleplay, meta, brainpower
                continue
            target_count[record['emoji_id']] += 1
        day_str = f'in the last {days} days' if days != -1 else f'ever'
        temp_str = f'Most used emoji {day_str}:\n'
        for key in sorted(user_count, key=user_count.get, reverse=True)[:5]:
            emoji_t = self.bot.get_emoji(key)
            if emoji_t:
                temp_str += f'{emoji_t} - {user_count[key]}\n'
            else:
                temp_str += f'{key} - {user_count[key]}\n'
        temp_str += f'\n\n Most reacted on you {day_str}:\n'
        for key in sorted(target_count, key=target_count.get, reverse=True)[:5]:
            emoji_t = self.bot.get_emoji(key)
            if emoji_t:
                temp_str += f'{emoji_t} - {target_count[key]}\n'
            else:
                temp_str += f'{key} - {target_count[key]}\n'
        nick = user.nick if user.nick else user.name
        local_embed = discord.Embed(
            title=f'Stats for {nick}',
            description= temp_str
        )
        await ctx.send(embed=local_embed)

    @stats.command()
    async def user(self, ctx, user: discord.Member, days: int=-1):
        """
        Returns stats on a user
        """
        user_count = defaultdict(int)
        target_count = defaultdict(int)
        stats = await self.bot.postgres_controller.get_user_emojis(user, days)
        for record in stats['user']:
            if record['channel_id'] in [297834395945926667, 329500167118258176, 294248007422181376, 148606162810568704, 227385793637777408, 264704915845283840, 191102386633179136, 378684962934751239, 232371423069339648, 343953048940314625]: #nsfw-roleplay, meta, brainpower
                continue
            user_count[record['emoji_id']] += 1
        for record in stats['target']:
            if record['channel_id'] in [297834395945926667, 329500167118258176, 294248007422181376, 148606162810568704, 227385793637777408, 264704915845283840, 191102386633179136, 378684962934751239, 232371423069339648, 343953048940314625]: #nsfw-roleplay, meta, brainpower
                continue
            target_count[record['emoji_id']] += 1
        day_str = f'in the last {days} days' if days != -1 else f'ever'
        temp_str = f'Most used emoji {day_str}:\n'
        for key in sorted(user_count, key=user_count.get, reverse=True)[:5]:
            emoji_t = self.bot.get_emoji(key)
            if emoji_t:
                temp_str += f'{emoji_t} - {user_count[key]}\n'
            else:
                temp_str += f'{key} - {user_count[key]}\n'
        temp_str += f'\n\n Most reacted on them {day_str}:\n'
        for key in sorted(target_count, key=target_count.get, reverse=True)[:5]:
            emoji_t = self.bot.get_emoji(key)
            if emoji_t:
                temp_str += f'{emoji_t} - {target_count[key]}\n'
            else:
                temp_str += f'{key} - {target_count[key]}\n'
        nick = user.nick if user.nick else user.name
        local_embed = discord.Embed(
            title=f'Stats for {nick}',
            description= temp_str
        )
        await ctx.send(embed=local_embed)

    @stats.command()
    async def emoji(self, ctx, emoji: discord.Emoji, days: int=-1):
        """
        Returns stats on an Emoji
        """
        emoji_stats = await self.bot.postgres_controller.get_emoji_stats(emoji, days)
        user_count = defaultdict(int)
        target_count = defaultdict(int)
        total_count = 0
        reaction_count = 0
        for row in emoji_stats:
            if row['channel_id'] in [297834395945926667, 329500167118258176, 294248007422181376, 148606162810568704, 227385793637777408, 264704915845283840, 191102386633179136, 378684962934751239, 232371423069339648, 343953048940314625]: #nsfw-roleplay, meta, brainpower
                continue
            user_count[row['user_id']] += 1
            total_count += 1
            if row['reaction']:
                target_count[row['target_id']] += 1
                reaction_count += 1
        day_str = f'in the last {days} days' if days != -1 else f'since forever'
        temp_str = f'Emoji used in messages {day_str}: {total_count-reaction_count}\n'
        temp_str += f'Emoji used in reactions {day_str}: {reaction_count}\n\n'
        temp_str += f'Top 5 users {day_str}:\n--------\n'
        for key in sorted(user_count, key=user_count.get, reverse=True)[:5]:
            user_t = self.bot.get_user(key)
            if user_t:
                temp_str += f'**{user_t.name}**#{user_t.discriminator}: {user_count[key]}\n'
            else:
                temp_str += f'**{key}**: {user_count[key]}\n'
        temp_str += f'\n\nTop 5 targets {day_str}:\n--------\n'
        for key in sorted(target_count, key=target_count.get, reverse=True)[:5]:
            user_t = self.bot.get_user(key)
            if user_t:
                temp_str += f'**{user_t.name}**#{user_t.discriminator}: {target_count[key]}\n'
            else:
                temp_str += f'**{key}**: {target_count[key]}\n'
        local_embed = discord.Embed(
            title=f'Emoji usage for {emoji}',
            description=temp_str
        )
        await ctx.send(embed=local_embed)

    @commands.group(aliases=['ts'])
    @commands.guild_only()
    async def top_stats(self, ctx):
        """
        This is the base command for the fun shit
        """
        if ctx.message.channel.id not in ALLOWED_CHANNELS:
            return
        if ctx.invoked_subcommand is None:
            await ctx.send('bruh thats not even a command')

    @top_stats.command(name='emoji')
    async def top_emoij(self, ctx, emoji: discord.Emoji, days: int=-1, channel=None):
        """
        Returns top post in timespan with reacts
        """
        day_str = f'in the last {days} days' if days != -1 else f'since forever'
        all_records = await self.bot.postgres_controller.get_top_post_by_emoji(
            emoji, days, channel
        )
        l_embed = discord.Embed(
            title=f'Top 3 Posts with {emoji} reacts {day_str}',
            desc=f'___'
        )
        for index, record in enumerate(all_records):
            channel = self.bot.get_channel(record['ch_id'])
            embed_image = False
            if channel.id in [183215451634008065]: 
                embed_image = True
            if channel.id in [259728514914189312, 220762067739738113, 230958006701916160, 304366022276939776]:
                return
            try:
                message = await channel.get_message(record['id'])
                if len(message.clean_content) > 600:
                    msg_content = f'{message.clean_content[:500]} ... `(message shortened)`'
                else:
                    msg_content = f'{message.clean_content[:500]}' if message.content != '' else ''
                msg_str = f'`Author`: {message.author.mention} ({message.author})\n'\
                          f'`Channel`: {message.channel.mention}\n'\
                          f'`Reacts`: {record["count"]}\n`Text`:\n{msg_content}\n'\
                          f'`Message Link`: {message.jump_url}\n'
                if message.attachments:
                    desc = ''
                    for file in message.attachments:
                        if embed_image:
                            desc += f'{file.url}'
                        else:
                            desc += f'**(!!might be nsfw!!)**:\n'\
                                    f'<{file.url}>\n**(!!might be nsfw!!)**'
                    msg_str += f'`Attachments` \n{desc}'
            except discord.errors.NotFound:
                msg_str = f'Message not found, probably deleted.'
            l_embed.add_field(
                name=f'**{index+1}.**',
                value=msg_str,
                inline=True,
            )
        await ctx.send(embed=l_embed)

    @top_stats.command(name='user')
    async def top_user(self, ctx, user: discord.Member, emoji: discord.Emoji, days: int=-1, channel: discord.TextChannel=None):
        """
        Returns top post in timespan with reacts
        """
        channel_id = channel.id if channel else None
        day_str = f'in the last {days} days' if days != -1 else f'since forever'
        all_records = await self.bot.postgres_controller.get_top_post_by_emoji_and_user(
             user.id, emoji, days, channel_id
        )
        l_embed = discord.Embed(
            title=f'Top 3 Posts with {emoji} reacts {day_str} on {user.name}',
            desc=f'___'
        )
        for index, record in enumerate(all_records):
            channel = self.bot.get_channel(record['ch_id'])
            embed_image = False
            if channel.id in [183215451634008065]: 
                embed_image = True
            if channel.id in [259728514914189312, 220762067739738113, 230958006701916160, 304366022276939776]:
                return
            try:
                message = await channel.get_message(record['id'])
                if len(message.clean_content) > 600:
                    msg_content = f'{message.clean_content[:500]} ... `(message shortened)`'
                else:
                    msg_content = f'{message.clean_content[:500]}' if message.content != '' else ''
                msg_str = f'`Author`: {message.author.mention} ({message.author})\n'\
                          f'`Channel`: {message.channel.mention}\n'\
                          f'`Reacts`: {record["count"]}\n`Text`:\n{msg_content}\n'\
                          f'`Message Link`: {message.jump_url}\n'
                if message.attachments:
                    desc = ''
                    for file in message.attachments:
                        if embed_image:
                            desc += f'{file.url}'
                        else:
                            desc += f'**(!!might be nsfw!!)**:\n'\
                                    f'<{file.url}>\n**(!!might be nsfw!!)**'
                    msg_str += f'`Attachments` \n{desc}'
            except discord.errors.NotFound:
                msg_str = f'Message not found, probably deleted.'
            l_embed.add_field(
                name=f'**{index+1}.**',
                value=msg_str,
                inline=True,
            )
        await ctx.send(embed=l_embed)

    @commands.command()
    @checks.has_permissions(manage_emojis=True)
    async def emojis(self, ctx, days: int=1):
        count_dict = defaultdict(int)
        desc_over = None
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
        if len(desc) > 2048:
            desc_over = ''
            count = 0
            temp = desc.split('\n')
            desc = ''
            for emoji in temp:
                count += len(emoji) + 1
                if count > 2047:
                    desc_over += f'{emoji}\n'
                else:
                    desc += f'{emoji}\n'
        local_embed = discord.Embed(
            title=f'Emoji use over the past {days} day/s:',
            description=desc
        )
        if desc_over:
            local_embed.add_field(
                name='------cont-----',
                value=desc_over
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
