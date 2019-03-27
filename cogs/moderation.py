"""
This cog is the moderation toolkit this is for tasks such as
kicking/banning users.
"""
import discord
from discord import HTTPException
from discord.ext import commands
from discord.utils import find
from .utils import helpers, checks
from .utils.enums import Action


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid'\
                                            'member or member ID.") from None
        else:
            can_execute = ctx.author.id == ctx.bot.owner_id or \
                          ctx.author == ctx.guild.owner or \
                          ctx.author.top_role > m.top_role

            if not can_execute:
                raise commands.BadArgument('You cannot do this action on this'
                                           ' user due to role hierarchy.')
            return m.id


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            entity = discord.utils.find(
                lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(
                lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument("Not a valid previously-banned member.")
        return entity


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
    async def timeout(self, ctx, member: discord.Member):
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
            all_channels = await self.bot.postgres_controller.get_all_channels()
            for row in all_channels:
                print(row)
                try:
                    channel = self.bot.get_channel(row['host_channel'])
                    message = await channel.fetch_message(row['message_id'])
                except:
                    continue
                if not message:
                    continue
                reaction = message.reactions[0]
                users = await reaction.users().flatten()
                to_member = find(lambda m: m.id == member.id, users)
                if to_member == None:
                    continue
                self.bot.logger.info(f'{row}, {to_member.id}')
                try:
                    target_channel = self.bot.get_channel(
                        row['target_channel'])
                    await self.remove_perms(to_member, target_channel)
                    removed_from_channels.append(target_channel.name)
                except (HTTPException, AttributeError) as e:
                    self.bot.logger.warning(f'Error removing user from channel!: {row["target_channel"]}{e}')  # noqa
                self.bot.logger.warning(f'{row["target_channel"]}') # noqa
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
    async def untimeout(self, ctx, member: discord.Member):
        guild_roles = ctx.guild.roles
        timeout_role = ctx.guild.get_role(self.bot.timeout_id)
        confirm = await helpers.confirm(ctx, member, '')
        member_roles = member.roles
        removed_from_channels = []
        reply = ''
        if not confirm:
            await ctx.send("Cancelled timeout", delete_after=3)
            return
        try:
            try:
                if timeout_role in member_roles:
                    await member.remove_roles(timeout_role)
                    reply += 'Successfully removed TO role\n'
                else:
                    raise AttributeError
            except (HTTPException, AttributeError) as e:
                reply += f'Error removing user from TO role: <@&{self.bot.timeout_id}>!: {e}\nContinuing with restoring permissions to self-assign channels.\n'
                pass
            all_channels = await self.bot.postgres_controller.get_all_channels()
            for row in all_channels:
                print(row)
                try:
                    channel = self.bot.get_channel(row['host_channel'])
                    message = await channel.fetch_message(row['message_id'])
                except:
                    continue
                if not message:
                    continue
                reaction = message.reactions[0]
                users = await reaction.users().flatten()
                to_member = find(lambda m: m.id == member.id, users)
                if to_member == None:
                    continue
                self.bot.logger.info(f'{row}, {to_member.id}')
                try:
                    target_channel = self.bot.get_channel(
                        row['target_channel'])
                    await self.add_perms(member, target_channel)
                    removed_from_channels.append(target_channel.name)
                except (HTTPException, AttributeError) as e:
                    self.bot.logger.warning(f'Error adding user to channel!: {row["target_channel"]}{e}')  # noqa
                self.bot.logger.warning(f'{row["target_channel"]}') # noqa
        except Exception as e:
            self.bot.logger.warning(f'Error timing out user!: {e}')
            await ctx.send('❌', delete_after=3)
            return
        # send output to log channel
        time = self.bot.timestamp()
        ret = ', '.join(removed_from_channels)
        reply += f'**User: {member.name}#{member.discriminator}: **Successfully added to channels: ``` {ret}```'  # noqa
        await ctx.send(f'**{time}** | {reply}')
        pass

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
