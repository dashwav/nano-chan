"""
A cog that filters all but a specific few phrases. (ignores bots)
"""
import discord


class Filter():

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.channels = bot.filter_channels
        self.filter_allowed = bot.filter_allowed

    async def on_message(self, message):
        if message.channel.id not in self.channels:
            return
        if message.author.bot:
            return
        cleaned_message = message.clean_content
        if cleaned_message.lower() in self.filter_allowed:
            return
        try:
            await message.delete()
            await self.bot.postgres_controller.add_message_delete(
                message.author.id
            )
            user_deleted = await self.bot.postgres_controller.get_message_deleted(
                message.author.id
            )
            self.bot.logger.info(user_deleted)
            if int(user_deleted) in [5,10,20,100]:
                self.bot.logger.info('koko wa deska')
                time = self.bot.timestamp()
                mod_info = self.bot.get_channel(self.bot.mod_info)
                await mod_info.send(
                    f'**{time} | SPAM:** {message.author} has had {user_deleted} '\
                    f'messages deleted in #welcome-center'
                )
            self.bot.logger.info(
                'Successfully deleted message from: '
                f'{message.author.display_name}')
        except Exception as e:
            self.bot.logger.warning(f'Error deleting message: {e}')
