"""
A cog that handles posting a large embed to block out spoils.
"""
import discord
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands
from .utils import checks


class Spoils():
    """
    Class that creates a task to run every minute and check for
    time since last post
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.wait_time = bot.wait_time
        # create the background task and run it in the background
        try:
            self.bg_task = self.bot.loop.create_task(self.my_background_task())
        except Exception as e:
            self.bot.logger.warning(f"Error starting task {e}")

    @commands.command(aliases = ['tenfeettaller'])
    @checks.has_permissions(manage_roles=True)
    async def wall(self, ctx, *, reason=None):
        local_embed = self.create_wall_embed(reason)
        try:
            await ctx.send(embed=local_embed)
            await ctx.message.delete()
        except Exception as e:
            self.bot.logger.warning(f'Issue building wall: {e}')

    async def my_background_task(self):
        local_embed = self.create_wall_embed()
        await self.bot.wait_until_ready()
        self.bot.logger.info("Starting spoiler task")
        while not self.bot.is_closed():
            for channel_id in self.bot.spoiler_channels:
                try:
                    channel = self.bot.get_channel(channel_id)
                except Exception as e:
                    self.bot.logger.warning(
                        f'Error getting channel {channel_id}: {e}')
                if channel:
                    async for message in channel.history(limit=1):
                        if not message.author.bot:
                            last_post = datetime.utcnow() - message.created_at
                            if last_post > timedelta(seconds=self.wait_time):
                                try:
                                    await channel.send(embed=local_embed)
                                except Exception as e:
                                    self.bot.logger.warning(
                                        f'Error posting to channel'
                                        f' {channel_id}: {e}')
                else:
                    self.bot.logger.warning(
                        f'Couldn\'t find channel: {channel_id}: {e}')
            await asyncio.sleep(60)

    def create_wall_embed(self, reason=None):
        local_embed = discord.Embed(title='Clear Spoilers', type='rich')
        temp_description = '\_\_\_'
        for i in range(60):
            temp_description += ' \n'
        if reason:
            temp_description += f'\_\_\_\nSpoilers for {reason} above'
        else:
            temp_description += '\_\_\_\nSpoilers above'
        local_embed.description = temp_description
        return local_embed
