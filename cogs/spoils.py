"""
A cog that handles posting a large embed to block out spoils.
"""
import discord
import asyncio
from datetime import datetime, timedelta

class Spoils():
    """
    Class that creates a task to run every minute and check for time since last post
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.wait_time = bot.wait_time
        self.embed = discord.Embed(title='Clear Spoilers', type='rich')
        self.embed.description = '\_\_\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'\
                                 '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\_\_\_\nSpoilers above'
        # create the background task and run it in the background
        self.bg_task = self.bot.loop.create_task(self.my_background_task())

    def __unload(self):
        self.bg_task.cancel()

    async def my_background_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for channel_id in self.bot.spoiler_channels:
                try:
                    channel = self.bot.get_channel(channel_id) # channel ID goes here
                except Exception as e:
                    self.bot.logger.warning(f'Error getting channel {channel_id}: {e}')
                if channel:
                    iterator = channel.history(limit=1)
                    async for message in channel.history(limit=1):
                        if not message.author.bot:
                            last_post = datetime.utcnow() - message.created_at
                            if last_post > timedelta(seconds=self.wait_time):
                                try:
                                    await channel.send(embed=self.embed)
                                except Exception as e:
                                    self.bot.logger.warning(f'Error posting to channel {channel_id}: {e}')
                else:
                    self.bot.logger.warning(f'Couldn\'t find channel: {channel_id}: {e}')
            await asyncio.sleep(60) # task runs every 60 seconds
