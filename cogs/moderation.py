"""
This cog is the moderation toolkit this is for tasks such as
kicking/banning users.
"""
import discord
from discord import HTTPException
from discord.ext import commands
from .utils import helpers, checks
from .utils.functions import GeneralMember, extract_id


class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = argument

        if len(ret) > 512:
            reason_max = 512 - len(ret) - len(argument)
            raise commands.BadArgument(
                f'reason is too long ({len(argument)}/{reason_max})')
        return ret


class Moderation(commands.Cog):
    """
    Main cog class
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.command()
    @checks.has_permissions(manage_messages=True)
    async def purge(self, ctx, *args, mentions=None):
        deleted = []
        try:
            count = int(next(iter(args or []), 'fugg'))
        except ValueError:
            count = 100
        mentions = ctx.message.mentions
        await ctx.message.delete()
        if mentions:
            for user in mentions:
                try:
                    deleted += await ctx.channel.purge(
                        limit=count,
                        check=lambda x: x.author == user
                    )
                except discord.Forbidden as e:
                    return await ctx.send(
                        'I do not have sufficient permissions to purge.')
                except Exception as e:
                    self.bot.logger.warning(f'Error purging messages: {e}')
        else:
            try:
                deleted += await ctx.channel.purge(limit=count)
            except discord.Forbidden as e:
                return await ctx.send(
                    'I do not have sufficient permissions to purge.')
            except Exception as e:
                    self.bot.logger.warning(f'Error purging messages: {e}')

    @commands.command()
    @checks.has_permissions(manage_roles=True)
    async def timeout(self, ctx, member: GeneralMember):
        guild_roles = ctx.guild.roles
        timeout_role = ctx.guild.get_role(self.bot.timeout_id)
        confirm = await helpers.confirm(ctx, member, '')
        removed_from_channels = []
        reply = ''
        if not confirm:
            await ctx.send("Cancelled timeout", delete_after=3)
            return
        try:
            try:
                await member.add_roles(timeout_role)
                reply += 'Successfully added TO role\n'
            except (HTTPException, AttributeError) as e:
                reply += f'Error adding user to TO role: <@&{self.bot.timeout_id}>!: {str(e)}\nContinuing with restoring permissions to self-assign channels.\n'
                pass
            r = await self.bot.pg_controller.get_chanreacts_fromuser(member.id)
            r = [x['target_channel'] for x in r]
            for target_channel in r:
                try:
                    target_channel = self.bot.get_channel(target_channel)
                    await self.remove_perms(member, target_channel)
                    removed_from_channels.append(target_channel.name)
                except (HTTPException, AttributeError) as e:
                    self.bot.logger.warning(f'Error removing user from channel!: {target_channel} {e}')  # noqa
        except Exception as e:
            self.bot.logger.warning(f'Error timing out user!: {e}')
            await ctx.send('❌', delete_after=3)
            return
        # send output to log channel
        time = self.bot.timestamp()
        ret = ', '.join(removed_from_channels)
        reply += f'**User: {member.name}#{member.discriminator}: **Successfully removed from channels: ``` {ret}```'  # noqa
        await ctx.send(f'**{time}** | {reply}')


    @commands.command()
    @checks.has_permissions(manage_roles=True)
    async def untimeout(self, ctx, member: GeneralMember):
        guild_roles = ctx.guild.roles
        timeout_role = ctx.guild.get_role(self.bot.timeout_id)
        confirm = await helpers.confirm(ctx, member, '')
        removed_from_channels = []
        reply = ''
        if not confirm:
            await ctx.send("Cancelled timeout", delete_after=3)
            return
        try:
            try:
                await member.add_roles(timeout_role)
                reply += 'Successfully added TO role\n'
            except (HTTPException, AttributeError) as e:
                reply += f'Error removing user from TO role: <@&{self.bot.timeout_id}>!: {e}\nContinuing with restoring permissions to self-assign channels.\n'
                pass
            r = await self.bot.pg_controller.get_chanreacts_fromuser(member.id)
            r = [x['target_channel'] for x in r]
            for target_channel in r:
                try:
                    target_channel = self.bot.get_channel(target_channel)
                    await self.add_perms(member, target_channel)
                    removed_from_channels.append(target_channel.name)
                except (HTTPException, AttributeError) as e:
                    self.bot.logger.warning(f'Error adding user to channel!: {target_channel} {e}')  # noqa
        except Exception as e:
            self.bot.logger.warning(f'Error untiming out user!: {e}')
            await ctx.send('❌', delete_after=3)
            return
        # send output to log channel
        time = self.bot.timestamp()
        ret = ', '.join(removed_from_channels)
        reply += f'**User: {member.name}#{member.discriminator}: **Successfully added to channels: ``` {ret}```'  # noqa
        await ctx.send(f'**{time}** | {reply}')

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

    """
    BLACKLIST
    """
    @commands.group(aliases=['blgu'], pass_context=True)
    @checks.has_permissions(manage_roles=True)
    async def blacklistglobaluser(self, ctx):
        """Add or remove a user to blacklist global list.

        Parameters
        ----------

        Returns
        -------
        """
        if ctx.invoked_subcommand is None:
            users = await self.bot.pg_controller.get_all_blacklist_users_global()
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
            users = [extract_id(x) for x in msg.split(',')]
        else:
            users = [extract_id(msg)]
        users = [x for x in users if x != '']

        try:
            for user in users:
                if int(user) in self.bot.dm_forward:
                    continue
                success = await self.bot.pg_controller.add_blacklist_user_global(user)
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
                    description=desc + '\nBy mod:' + str(ctx.author.mention),
                )
            else:
                self.bot.logger.info(f'Error adding users to global blacklist')
                return
        except Exception as e:
            self.bot.logger.info(f'Error adding users to global blacklist {e}')
        try:
            await ctx.send(embed=embed)
        except Exception as e:
            self.bot.logger.info(f'Error sending embed to modlog {e}')
        try:
            if added_users:
                for user_id in self.bot.dm_forward:
                    user = await self.bot.fetch_user(user_id)
                    await user.create_dm()
                    await user.dm_channel.send(embed=embed)
        except Exception as e:
            self.bot.logger.warning(f'Issue forwarding dm: {e}')

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
            users = [extract_id(x) for x in msg.split(',')]
        else:
            users = [extract_id(msg)]
        self.bot.logger.info(users)

        try:
            for user in users:
                success = False
                try:
                    success = await self.bot.pg_controller.rem_blacklist_user_global(user)
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
                description=desc + '\nBy mod:' + str(ctx.author.mention)
            )
            for field in fields:
                embeds.add_field(
                    name = field[0],
                    value = field[1],
                    inline = True
                )
        except Exception as e:
            self.bot.logger.warning(f'Issue removing users from ' +
                                    f'global blacklist: {e}')
        try:
            await ctx.send(embed=embeds)
        except Exception as e:
            self.bot.logger.info(f'Error sending embed to modlog {e}')
        try:
            if removed_users:
                for user_id in self.bot.dm_forward:
                    user = await self.bot.fetch_user(user_id)
                    await user.create_dm()
                    await user.dm_channel.send(embed=embeds)
        except Exception as e:
            self.bot.logger.warning(f'Issue forwarding dm: {e}')

