from discord.ext import commands
from discord.utils import find
from .utils import checks


class Tutoring():

    def __init__(self, bot):
        """
        init for cog class
        """
        super().__init__()
        self.bot = bot
        self.studying_timers = []

    @commands.command()
    async def study(self, ctx, minutes):
        if minutes is None:
                await ctx.send(
                    "You need to supply an amount of hours, try again.",
                    delete_after=5)
                return
        member = ctx.message.author
        studying_id = 526994881676181507
        channel_backup = []
        try:
            await member.add_roles(studying_id)
            all_channels = self.bot.postgres_controller.get_all_channels()
            for row in all_channels:
                channel = self.bot.get_channel(row['host_channel'])
                message = channel.get_message(row['message_id'])
                reacted_users = await message.reactions[0].users().flatten()
                if member in reacted_users:
                    try:
                        target_channel = self.bot.get_channel(row['target_channel'])
                        await self.remove_perms(member, target_channel)
                    except Exception as e:
                        self.bot.logger.warning(f'Error removing user from channel!: {row["target_channel"]}{e}')
            self.studying_timers.append(self.bot.loop.create_task(self.study_end(minutes, member)))
        except Exception as e:
            self.bot.logger.warning(f'Error letting user study!: {e}')
            await ctx.send('❌', delete_after=3)
            return

    @commands.command()
    async def slack_off(self, ctx):
        member = ctx.message.author
        studying_id = 526994881676181507
        channel_backup = []
        confirm = await helpers.confirm(ctx, member, '')
        if confirm:
            try:
                await member.remove_roles(studying_id)
                all_channels = self.bot.postgres_controller.get_all_channels()
                for row in all_channels:
                    channel = self.bot.get_channel(row['host_channel'])
                    message = channel.get_message(row['message_id'])
                    reacted_users = await message.reactions[0].users().flatten()
                    if member in reacted_users:
                        try:
                            target_channel = self.bot.get_channel(row['target_channel'])
                            await self.add_perms(member, target_channel)
                        except Exception as e:
                            self.bot.logger.warning(f'Error removing user from channel!: {row["target_channel"]}{e}')
            except Exception as e:
                self.bot.logger.warning(f'Error letting user slack of!: {e}')
                await ctx.send('❌', delete_after=3)
                return
        else:
            await ctx.send("Cancelled timeout", delete_after=3)

    async def study_end(self, minutes, member):
        await asyncio.sleep(minutes/60)
        studying_id = 526994881676181507
        try:
            await member.remove_roles(studying_id)
            all_channels = self.bot.postgres_controller.get_all_channels()
            for row in all_channels:
                channel = self.bot.get_channel(row['host_channel'])
                message = channel.get_message(row['message_id'])
                reacted_users = await message.reactions[0].users().flatten()
                if member in reacted_users:
                    try:
                        target_channel = self.bot.get_channel(row['target_channel'])
                        await self.add_perms(member, target_channel)
                    except Exception as e:
                        self.bot.logger.warning(f'Error removing user from channel!: {row["target_channel"]}{e}')
        except Exception as e:
            self.bot.logger.warning(f'Error letting user finish studying: {e}')
            return

    async def add_perms(self, user, channel):
        """
        Adds a user to channels perms
        """
        try:
            await channel.set_permissions(user, read_messages=True)
        except Exception as e:
            self.bot.logger.warning(f'{e}')  
    
    async def remove_perms(self, user, channel):
        """
        removes a users perms on a channel
        """
        try:
            await channel.set_permissions(user, read_messages=False)
        except Exception as e:
            self.bot.logger.warning(f'{e}')  