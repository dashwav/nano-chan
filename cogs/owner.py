""" 
Misc commands that I want to run 
""" 
import discord 
from discord.ext import commands 
from .utils import checks 


class Owner(commands.Cog):
    """
    Cog with misc owner commands
    """
    def __init__(self, bot):
        """
        init for cog class
        """
        super().__init__()
        self.bot = bot

    @commands.command()
    @checks.is_admin()
    async def set_playing(self, ctx, *, game=None):
        if game:
            await self.bot.change_presence(game=discord.Game(name=game))
        ctx.delete()


    @commands.command(hidden=True)
    async def echo(self, ctx, channel, *, message):
        """
        Echoes a string into a different channel
        :params channel: channel to echo into params message: message to 
        :echo
        """
        is_owner = await ctx.bot.is_owner(ctx.author)
        if not is_owner:
            return
        if not ctx.message.channel_mentions:
            return await ctx.send(
                f'<command> <channel mention> <message> u idiot')
        try:
            for channel in ctx.message.channel_mentions:
                await channel.send(f'{message}')
        except Exception as e:
            ctx.send('Error when trying to send fam')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def fixdb(self, ctx, correction: str):
        """
        This command is a highly custom command that will be used to help
        rsync/fix the db when code is updated.

        Parameters
        ----------
        corrections: str
            This is a string with the name of the correction to run. The
            current corrections are rebuildReport
        Returns
        -------
        None
        """
        actions = ('rebuildReport',)
        if correction not in actions:
            await ctx.send('Your action {} was not found in the actionable list: {}'.format(correction, actions))
            return
        if correction == 'rebuildReport':
            # Add column to table
            sql = """
                ALTER TABLE {}.user_reports
                ADD COLUMN message TEXT;
            """.format(self.bot.postgres_controller.schema)
            try:
                await self.bot.postgres_controller.pool.execute(sql)
            except Exception as err:
                # await ctx.send('Couldn\'t add column to db: {}'.format(err), delete_after=15)
                pass
            # gather all user reports
            user_reports = []
            try:
                user_reports = await self.bot.postgres_controller.get_all_user_reports()
            except Exception as err:
                # await ctx.send(err, delete_after=15)
                pass
            # Now go through and grab message contents
            for report in user_reports:
                # self.bot.logger.info(f'Fixing report {report["report_id"]}')
                # self.bot.logger.info(f'Report {report}')
                report_message = ''
                try:
                    report_message = await ctx.channel.fetch_message(int(report['message_id']))
                    # self.bot.logger.info(f'Message {report_message}')
                    report_message = report_message.embeds[0].description
                except Exception as err:
                    # await ctx.send(err, delete_after=15)
                    pass
                # self.bot.logger.info(report_message)
                if report_message != '':
                    try:
                        await self.bot.postgres_controller.set_report_message_content(report['report_id'], report_message)
                    except Exception as err:
                        pass # self.bot.logger.warning('Failed: {}'.format(err))
            await ctx.send('Fixed the db')

        return
