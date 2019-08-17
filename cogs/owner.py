""" 
Misc commands that I want to run 
""" 
import discord 
from discord.ext import commands 
from .utils import checks 
from .utils.functions import extract_id


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

    """
    BLACKLIST
    """
    @commands.group(aliases=['blgu'], pass_context=True)
    @commands.is_owner()
    async def blacklistglobaluser(self, ctx):
        """Add or remove a user to blacklist global list.

        Parameters
        ----------

        Returns
        -------
        """
        if ctx.invoked_subcommand is None:
            users = await self.bot.postgres_controller.get_all_blacklist_users_global()
            if isinstance(users, type(None)):
                users = []
            if len(users) > 0:
                title = 'Users in global blacklist'
                desc = '<@'
                desc += '>, <@'.join(map(str, users))
                desc += '>'
            else:
                desc = ''
                title = 'No users in global blacklist'
            embed = discord.Embed(
                title=title,
                description=desc
            )
            await ctx.send(embed=embed)

    @blacklistglobaluser.command(name='add', pass_context=True)
    async def _blgua(self, ctx: commands.Context, *, uids: str=None):
        """Add user to global blacklist.

        Parameters
        ----------
        uids: str
            List of id, comma separated

        Returns
        -------
        """
        added_users = []
        msg = uids.replace(' ', '')
        if ',' in msg:
            users = [extract_id(x, 'member') for x in msg.split(',')]
        else:
            users = [extract_id(msg, 'member')]
        users = [x for x in users if x != '']

        try:
            for user in users:
                success = await self.bot.postgres_controller.add_blacklist_user_global(user)
                if success:
                    added_users.append(user)
            if added_users:
                self.bot.blglobal += list(map(int, added_users))
                title = 'Users added into global blacklist'
                desc = '<@'
                desc += '>, <@'.join(map(str, added_users))
                desc += '>'
                embed = discord.Embed(
                    title=title,
                    description=desc,
                )
            else:
                self.bot.logger.info(f'Error adding users to global blacklist')
                return
            await ctx.send(embed=embed)
        except Exception as e:
            self.bot.logger.info(f'Error adding users to global blacklist {e}')

    @blacklistglobaluser.command(name='remove', aliases=['rem', 'del', 'rm'])
    async def _blgur(self, ctx: commands.Context, *, uids: str=None):
        """Removes a user from the blacklist.

        Parameters
        ----------
        uids: str
            List of id, comma separated

        Returns
        -------
        """
        removed_users = []
        user_notfound = []
        msg = uids.replace(' ', '')
        if ',' in msg:
            users = [extract_id(x, 'member') for x in msg.split(',')]
        else:
            users = [extract_id(msg, 'member')]
        print(users)

        try:
            for user in users:
                success = False
                try:
                    success = await self.bot.postgres_controller.rem_blacklist_user_global(user)
                    if success:
                        self.bot.blglobal.remove(int(user))
                        removed_users.append(user)
                    else:
                        user_notfound.append(user)
                except:
                    user_notfound.append(user)

            fields = []
            if removed_users:
                fields.append(['PASS', ', '.join([f'<@{x}>' for x in removed_users])])
            if user_notfound:
                fields.append(['FAIL', ', '.join([f'<@{x}>' for x in user_notfound])])
            title = 'Users blacklisting'
            desc = ''
            embeds = discord.Embed(
                title=title,
                description=desc
            )
            for field in fields:
                embeds.add_field(
                    name = field[0],
                    value = field[1],
                    inline = True
                )
            await ctx.send(embed=embeds)
        except Exception as e:
            self.bot.logger.warning(f'Issue removing users from ' +
                                    f'global blacklist: {e}')

