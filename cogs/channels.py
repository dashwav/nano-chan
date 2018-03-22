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
            '1\u20e3',
            '2\u20e3',
            '3\u20e3',
            '4\u20e3',
            '5\u20e3',
            '6\u20e3',
            '7\u20e3',
            '8\u20e3',
            '9\u20e3',]
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
            await ctx.send("that is not a valid channel fam")
        self.bot.logger.info(f'{channel.id}')
        message_info = await self.bot.postgres_controller.add_and_get_message(
            self.bot.logger,
            ctx.channel.id, channel.id)
        if not message_info:
            await ctx.send("oops something went wrong")
            return
        self.bot.logger.info(f'test1 id:{message_info["message_id"]}')
        og_message = await ctx.channel.get_message(message_info['message_id'])
        og_embed = og_message.embeds[0]
        og_embed.add_field(
            name=f"{self.reaction_emojis[message_info['reacts'] + 1]}  {description}",
            value=f'{channel.name}')
        self.bot.logger.info('test2')
        await og_message.edit(embed=og_embed)
        await og_message.add_reaction(self.reaction_emojis[message_info['reacts'] + 1])


