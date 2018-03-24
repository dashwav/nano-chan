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
            '0\u20e3', '1\u20e3', '2\u20e3', '3\u20e3', '4\u20e3',
            '5\u20e3', '6\u20e3', '7\u20e3', '8\u20e3', '9\u20e3',
            '\N{REGIONAL INDICATOR SYMBOL LETTER A}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER B}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER C}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER D}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER E}',
            '\N{REGIONAL INDICATOR SYMBOL LETTER F}',
            ]
        self.bot = bot

    @commands.group()
    @commands.guild_only()
    @checks.has_permissions(manage_channels=True)
    async def channel_message(self, ctx):
         if ctx.invoked_subcommand is None:
            await ctx.send(':thinking:')
    
    @channel_message.command(aliases=['add'])
    async def create(self, ctx, target_channel: discord.TextChannel, *, description: str):
        if not isinstance(target_channel, discord.TextChannel):
            await ctx.send("that is not a valid channel fam", delete_after=4)
            return
        local_embed = discord.Embed(
            title=f'#{target_channel.name}',
            description=f'{description}',
            type="rich"
        )
        message = await ctx.send(embed=local_embed)
        await message.add_reaction(self.reaction_emojis[0])
        await self.bot.postgres_controller.add_channel_message(
            message.id, target_channel, ctx.channel.id)
        await ctx.message.delete()

    @channel_message.command(aliases=['rem'])
    async def remove(self, ctx, target_channel: discord.TextChannel):
        """
        uhhh it removes the thing
        """
        if not isinstance(target_channel, discord.TextChannel):
            await ctx.send("that is not a valid channel fam", delete_after=4)
            return
        try:
            message_id = await self.bot.postgres_controller.get_message_id(
                ctx.channel.id, target_channel.id)
        except Exception as e:
            await ctx.send("something broke", delete_after=3)
            return
        if not message_id:
            return
        og_message = await ctx.channel.get_message(message_id)
        for reaction in og_message.reactions:
            async for user in reaction.users:
                await og_message.remove_reaction(reaction.emoji, user)
                await self.remove_perms(user, target_channel)
        await og_message.delete()
        await ctx.message.delete()

    @channel_message.command()
    async def edit(self, ctx, target_channel: discord.TextChannel, *, edit: str):
        if not isinstance(target_channel, discord.TextChannel):
            await ctx.send("that is not a valid channel fam", delete_after=4)
            return
        try:
            message_id = await self.bot.postgres_controller.get_message_id(
                ctx.channel.id, target_channel.id)
        except:
            await ctx.send("something broke", delete_after=3)
            return
        if not message_id:
            return
        og_message = await ctx.channel.get_message(message_id)
        og_embed = og_message.embeds[0]
        og_embed.description = edit
        await og_message.edit(embed=og_embed)
        await ctx.send(":ok_hand:", delete_after=3)

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        """
        Called when an emoji is added
        """
        target_channel = await self.bot.postgres_controller.get_target_channel(channel_id, message_id)
        if not target_channel:
                return 
        user = self.bot.get_user(user_id)
        await self.add_perms(user, target_channel)

    async def on_raw_reaction_remove(self, emoji, message_id, channel_id, user_id):
        """
        Called when an emoji is removed
        """
        target_channel = await self.bot.postgres_controller.get_target_channel(channel_id, message_id)
        if not target_channel:
            return
        user = self.bot.get_user(user_id)
        await self.remove_perms(user, target_channel)
    
    async def add_perms(self, user, channel):
        """
        Adds a user to channels perms
        """
        await channel.set_permissions(user, read_messages=True,
                                                        send_messages=True)
            
    async def remove_perms(self, user, channel):
        """
        removes a users perms on a channel
        """
        await channel.set_permissions(user, read_messages=False,
                                                        send_messages=False)
