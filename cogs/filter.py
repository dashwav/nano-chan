"""
A cog that filters all but a specific few phrases. (ignores bots)
"""
import discord
from discord.ext import commands


class Filter(commands.Cog):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.channels = bot.filter_channels
        self.filter_allowed = bot.filter_allowed

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in self.bot.blglobal:
            return
        if isinstance(message.channel, discord.DMChannel):
            return
        if message.channel.id not in self.channels:
            return
        if message.author.bot:
            return
        cleaned_message = message.clean_content
        if cleaned_message in self.filter_allowed:
            return
        try:
            await message.delete()
            await self.bot.pg_controller.add_message_delete(
                message.author.id
            )
            user_deleted = await self.bot.pg_controller.get_message_deleted(
                message.author.id
            )
            if int(user_deleted) in [5,10,20,100]:
                time = self.bot.timestamp()
                mod_info = self.bot.get_channel(259728514914189312)
                await mod_info.send(
                    f'**{time} | SPAM:** {message.author} has had {user_deleted} '\
                    f'messages deleted in {message.channel.name}'
                )
            self.bot.logger.info(
                'Successfully deleted message from: '
                f'{message.author.display_name}')
        except Exception as e:
            self.bot.logger.warning(f'Error deleting message: {e}')
