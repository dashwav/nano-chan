"""
This cog will create messages that will manage channel perms with reacts.
"""
import discord
import datetime
from collections import defaultdict
from .utils import helpers, checks
from discord.ext import commands


class Channels():
    """
    """

    def __init__(self, bot):
        super().__init__()
        self.reaction_emojis = [ 
            '\N{REGIONAL INDICATOR SYMBOL LETTER A}',
            '1\u20e3', '2\u20e3', '3\u20e3', '4\u20e3',
            '5\u20e3', '6\u20e3', '7\u20e3', '8\u20e3',
            '9\u20e3',
            '\N{REGIONAL INDICATOR SYMBOL LETTER B}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER C}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER D}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER E}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER F}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER G}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER H}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER I}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER J}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER K}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER L}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER M}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER N}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER O}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER P}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER Q}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER R}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER S}',
            ]
        self.bot = bot

    @commands.group()
    @commands.guild_only()
    @checks.has_permissions(manage_channels=True)
    async def channel_message(self, ctx):
         if ctx.invoked_subcommand is None:
            await ctx.send(':thinking:')
    
    @channel_message.command()
    async def create(self, ctx, *, message: str):
        local_embed = discord.Embed(
            title=f'{message}',
            description='',
            type="rich"
        )
        message = await ctx.send(embed=local_embed)
        await self.bot.postgres_controller.add_channel_message(message.id, ctx.channel.id, [])
    
    @channel_message.command()
    async def add(self, ctx, channel: discord.TextChannel, *, description):
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("that is not a valid channel fam", delete_after=4)
            return
        self.bot.logger.info(f'{channel.id}')
        message_info = await self.bot.postgres_controller.add_and_get_message(
            self.bot.logger,
            ctx.channel.id, channel.id)
        if not message_info:
            await ctx.send("oops something went wrong", delete_after=4)
            return
        if message_info['reacts'] >= 27:
            await ctx.send(f'You have reached the max amount of redos for this message, either recreate it or message dash to fix the shitty code that caused this')
            return
        self.bot.logger.info(f'test1 id:{message_info["message_id"]}')
        og_message = await ctx.channel.get_message(message_info['message_id'])
        og_embed = og_message.embeds[0]
        og_embed.add_field(
            name=f"{self.reaction_emojis[message_info['reacts'] + 1]}  {description}",
            value=f'{channel}')
        self.bot.logger.info('test2')
        try:
            await og_message.add_reaction(self.reaction_emojis[message_info['reacts'] + 1])
        except discord.HTTPException:
            await ctx.send("There are too many reactions on this message, please create a new one", delete_after=4)
            return
        await og_message.edit(embed=og_embed)
        await ctx.message.delete()

    @channel_message.command(aliases=['rem'])
    async def remove(self, ctx, channel: discord.TextChannel):
        """
        uhhh it removes the thing
        """
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("that is not a valid channel fam", delete_after=4)
            return
        try:
            message_info = await self.bot.postgres_controller.rem_perm_channel(
                ctx.channel.id, channel
            )
        except Exception as e:
            await ctx.send("something broke", delete_after=3)
            return
        if not message_info:
            return
        og_message = await ctx.channel.get_message(message_info)
        og_embed = og_message.embeds[0]

        for index, field in enumerate(og_embed.fields):
            if field.value == f'{channel}':
                og_embed.remove_field(index)
                for reaction in og_message.reactions:
                    if reaction.emoji == field.name.split(' ')[0]:
                        async for user in reaction.users:
                            await og_message.remove_reaction(reaction.emoji, user)
                            await self.remove_perms(user, field.value)
                        await og_message.remove_reaction(reaction.emoji, og_message.author)
                        break
        await og_message.edit(embed=og_embed)
        await ctx.message.delete()

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        """
        Called when an emoji is added
        """
        if await self.bot.postgres_controller.check_message_id(message_id):
            channel = self.bot.get_channel(channel_id)
            user = self.bot.get_user(user_id)
            message = await channel.get_message(message_id)
            target_channel = None
            for field in enumerate(message.embeds[0].fields):
                if emoji == field.name.split(' ')[0]:
                    target_channel = field.value
            if not target_channel:
                return
            await target_channel.set_permissions(user, read_messages=True,
                                                        send_messages=True)
            
    async def remove_perms(self, user, channel):
        """
        removes a users perms on a channel
        """
        await channel.set_permissions(user, read_messages=False,
                                                        send_messages=False)
