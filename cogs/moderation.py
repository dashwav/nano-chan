"""
This cog is the moderation toolkit this is for tasks such as 
kicking/banning users.
"""
import discord
from discord.ext import commands
from .utils import helpers, checks

class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        else:
            can_execute = ctx.author.id == ctx.bot.owner_id or \
                          ctx.author == ctx.guild.owner or \
                          ctx.author.top_role > m.top_role

            if not can_execute:
                raise commands.BadArgument('You cannot do this action on this user due to role hierarchy.')
            return m.id

class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            entity = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument("Not a valid previously-banned member.")
        return entity

class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = argument

        if len(ret) > 512:
            reason_max = 512 - len(ret) - len(argument)
            raise commands.BadArgument(f'reason is too long ({len(argument)}/{reason_max})')
        return ret

class Moderation:
    """
    Main cog class
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.command()
    @checks.has_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason: ActionReason = None):
        if reason is None:
                await ctx.send(
                    "You need to supply a reason, try again.",
                    delete_after=5)
                return
        confirm = await helpers.confirm(ctx, member, reason)
        if confirm:
            embed = self.create_embed('Kick', ctx.guild, reason)
            try:
                try:
                    await member.create_dm()
                    await member.dm_channel.send(embed=embed)
                except Exception as e:
                    self.bot.logger.warning(f'Error messaging user!: {e}')
                await member.kick(reason=f'by: {ctx.author} for: {reason}')
                await ctx.send('\N{OK HAND SIGN}', delete_after=3)
            except Exception as e:
                self.bot.logger.warning(f'Error kicking user!: {e}')
                await ctx.send('❌', delete_after=3)
                return
            self.bot.logger.info(f'Successfully kicked {member}')
        else:
            await ctx.send("Cancelled kick", delete_after=3)

    @commands.command()
    @checks.has_permissions(ban_members=True)
    async def ban(self, ctx, member_id: MemberID, *, reason: ActionReason = None):
        if reason is None:
                await ctx.send(
                    "You need to supply a reason, try again.",
                    delete_after=5)
                return
        member = await self.bot.get_user_info(member_id)
        confirm = await helpers.confirm(ctx, member, reason)
        if confirm:
            
            embed = self.create_embed('Ban', ctx.guild, reason)
            try:
                try:
                    await member.create_dm()
                    await member.dm_channel.send(embed=embed)
                except Exception as e:
                    self.bot.logger.warning(f'Error messaging user!: {e}')
                await ctx.guild.ban(
                    discord.Object(id=member_id),
                    delete_message_days=0,
                    reason=f'by: {ctx.author} for: {reason}')
                await ctx.send('\N{OK HAND SIGN}', delete_after=3)
            except Exception as e:
                self.bot.logger.warning(f'Error banning user!: {e}')
                await ctx.send('❌', delete_after=3)
                return
            self.bot.logger.info(f'Successfully banning {member}')
        else:
            await ctx.send("Cancelled ban", delete_after=3)

    @commands.command()
    @checks.has_permissions(ban_members=True)
    async def unban(self, ctx, member: BannedMember, *, reason: ActionReason = None):
        if reason is None:
                await ctx.send(
                    "You need to supply a reason, try again.",
                    delete_after=5)
                return
        confirm = await helpers.confirm(ctx, member.user, reason)
        if confirm:
            embed = self.create_embed('Unban', ctx.guild, reason)
            try:
                await ctx.guild.unban(
                    member.user,
                    reason=f'by: {ctx.author} for: {reason}')
                await ctx.send('\N{OK HAND SIGN}', delete_after=3)
            except Exception as e:
                self.bot.logger.warning(f'Error unbanning user!: {e}')
                await ctx.send('❌', delete_after=3)
                return
            self.bot.logger.info(f'Successfully unbanning {member}')
        else:
            await ctx.send("Cancelled unban", delete_after=3)

    def create_embed(self, command_type, server_name, reason):
        embed = discord.Embed(title=f'❗ {command_type} Reason ❗', type='rich')
        if command_type.lower() == 'ban':
            command_type = 'bann'
        elif command_type.lower() == 'unban':
            command_type = 'unbann'
        embed.description = f'\nYou were {command_type.lower()}ed from **{server_name}**.'
        embed.add_field(name='Reason:', value=reason)
        embed.set_footer(text='This is an automated message')
        return embed
