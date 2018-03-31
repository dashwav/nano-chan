"""
This cog is to be used primarily for small janitorial tasks
(removing clover once member is hit, pruning clovers)
"""
import discord
from discord import AuditLogAction
from discord.ext import commands
from .utils import checks
from .utils.enums import Change
from datetime import datetime, timedelta
import asyncio


class Janitor():
    """
    The main class wrapepr
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.owner = None
        try:
            self.bg_task = self.bot.loop.create_task(self.daily_prune())
            self.owner_task = self.bot.loop.create_task(self.setup_owner_dm())
        except Exception as e:
            self.bot.logger.warning(f'Error starting task prune_clovers: {e}')

    async def setup_owner_dm(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info(
            f'Setting up owner channel {self.bot.bot_owner_id}')
        try:
            self.server_logs = self.bot.get_channel(378684962934751239)
            self.owner = await self.bot.get_user_info(self.bot.bot_owner_id)
        except Exception as e:
            self.bot.logger.warning(f'Error getting owner: {e}')
        self.bot.logger.info(f'User retrieved: {self.owner.name}')
        try:
            try:
                await self.owner.create_dm()
            except Exception as e:
                self.bot.logger.warning(f'Error creating dm channel: {e}')
            await self.owner.dm_channel.send('Bot started successfully')
            #await self.server_logs.send('Bot started successfully')
        except Exception as e:
            self.bot.logger.warning(f'Error getting dm channel: {e}')

    def remove_clover(self, member) -> list:
        member_roles = member.roles
        for index, role in enumerate(member_roles):
            if role.name.lower() == 'clover' or role.name.lower() == 'dedicated':
                del member_roles[index]
        return member_roles

    def remove_key(self, member) -> list:
        member_roles = member.roles.copy
        for index, role in enumerate(member_roles):
            if role.name.lower() == '🔑':
                key_index = index
        del member_roles[key_index]
        return member_roles

    def remove_access(self, member) -> list:
        member_roles = member.roles.copy()
        role_list = []
        for index, role in enumerate(member_roles):
            if role.name.lower() in ['muse', 'dev','lewd', 'swole', 'artsy', 'shokugeki', 'degenerate', 'simulcast', 'legacy', 'meta', 'stylish']:
                role_list.append(role)
        for role in role_list:
            member_roles.remove(role)
        return member_roles

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith('.iam'):
            return
        has_clover = False
        has_key = False
        has_member = False
        has_dedicated = False
        has_permrole = False
        member_roles = message.author.roles
        for index, role in enumerate(member_roles):
            if role.name.lower() == 'clover':
                has_clover = True
            elif role.name.lower() == '🔑':
                has_key = True
            elif role.name.lower() == 'dedicated':
                has_dedicated = True
            elif role.name.lower() in ['muse', 'dev','lewd', 'swole', 'artsy', 'shokugeki', 'degenerate', 'simulcast', 'legacy', 'meta', 'stylish']:
                has_permrole = True
            elif role.name.lower() == 'member':
                has_member = True
        if has_clover and has_member:
            member_roles = self.remove_clover(message.author)
            try:
                await message.author.edit(
                    roles=member_roles,
                    reason="User upgraded from clover to member")
                await message.add_reaction('🎊')
                self.bot.logger.info(
                    f'{message.author.display_name}'
                    ' was just promoted to member!')
                try:
                    await self.bot.postgres_controller.insert_rolechange(
                        message.guild.id, message.author.id, Change.PROMOTION
                    )
                except Exception as e:
                    self.bot.logger.warning(
                        f'Issue logging action to db: {e})')
            except Exception as e:
                self.bot.logger.warning(
                    f'Error updating users roles: {e}')
        if has_key and has_member:
            member_roles = self.remove_key(message.author)
            try:
                await message.author.edit(
                    roles=member_roles,
                    reason="User upgraded from Key to member")
                self.bot.logger.info(
                    f'{message.author.display_name}'
                    ' was just promoted to member!')
                try:
                    await self.bot.postgres_controller.insert_rolechange(
                        message.guild.id, message.author.id, Change.PROMOTION
                    )
                except Exception as e:
                    self.bot.logger.warning(
                        f'Issue logging action to db: {e})')
            except Exception as e:
                self.bot.logger.warning(
                    f'Error updating users roles: {e}')
        if has_dedicated and has_permrole:
            member_roles = self.remove_access(message.author)
            try:
                await message.author.edit(
                    roles=member_roles,
                    reason="User had perm roles")
                self.bot.logger.info(
                    f'{message.author.display_name}'
                    ' had access roles removed')
            except Exception as e:
                self.bot.logger.warning(
                    f'Error updating users access roles: {e}')

    @commands.command(hidden=True)
    @checks.has_permissions(manage_roles=True)
    async def aggroprune(self,ctx):
        self.bot.logger.info(f'Prune requested by: {ctx.message.author}')
        await self.prune_nonclovers()

    @commands.command(hidden=True)
    @checks.has_permissions(manage_roles=True)
    async def prune(self, ctx):
        self.bot.logger.info(f'Prune requested by: {ctx.message.author}')
        await self.prune_clovers()

    @prune.error
    async def prune_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            self.bot.logger.warning(f'{ctx.message.author} '
                                    'tried to run prune w/o permissions')

    @aggroprune.error
    async def aggroprune_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            self.bot.logger.warning(f'{ctx.message.author} '
                                    'tried to run prune w/o permissions')

    async def daily_prune(self):
        self.bot.logger.info("Starting prune task, first prune in 24 hours")
        while not self.bot.is_closed():
            await asyncio.sleep(86400)
            await self.prune_clovers()

    async def prune_clovers(self):
        try:
            self.bot.logger.info('Starting prune task now')
        except Exception as e:
            self.bot.logger.info('tf')
        clovers = []
        clover_role = None
        mod_log = self.bot.get_channel(self.bot.mod_log)
        a_irl = self.bot.get_guild(self.bot.guild_id)
        for role in a_irl.roles:
            if role.name.lower() == 'clover':
                clover_role = role
        if not clover_role:
            self.bot.logger.warning(
                'Something went really wrong, '
                'I couldn\'t find the clover role')
            return
        clovers = clover_role.members
        try:
            members_prunable = await self.bot.postgres_controller.get_all_prunable()
        except Exception as e:
            self.bot.logger.warning(f'{e}')
        prune_info = {'pruned': False, 'amount': 0}
        self.bot.logger.info(f'{members_prunable}')
        for member in clovers:
            if member.id in members_prunable:
                try:
                    new_roles = self.remove_clover(member)
                    await member.edit(
                        roles=new_roles,
                        reason="Pruned due to inactivity"
                    )
                    prune_info['pruned'] = True
                    prune_info['amount'] += 1
                except Exception as e:
                    self.bot.logger.warning(
                        f'Error pruning clovers: {e}'
                    )
        self.bot.logger.info(f'Prune info: {prune_info}')
        try:
            await self.bot.postgres_controller.reset_message_deleted()
        except Exception as e:
            self.bot.logger.warning(f'Issue resetting spam db: {e}')
        if prune_info['pruned']:
            try:
                await mod_log.send(
                    f'Pruned {prune_info["amount"]} clovers 🍀🔫')
            except Exception as e:
                self.bot.logger.warning(
                    f'Error posting prune info to mod_log: {e}')

    async def prune_nonclovers(self):
        try:
            self.bot.logger.info('Starting aggroprune task now')
        except Exception as e:
            self.bot.logger.info('tf')
        clovers = []
        clover_role = None
        mod_log = self.bot.get_channel(self.bot.mod_log)
        a_irl = self.bot.get_guild(self.bot.guild_id)
        for role in a_irl.roles:
            if role.name.lower() == 'clover':
                clover_role = role
        if not clover_role:
            self.bot.logger.warning(
                'Something went really wrong, '
                'I couldn\'t find the clover role')
            return
        clovers = clover_role.members
        self.bot.logger.info(f'Can i get uhhh')
        try:
            members_safe = await self.bot.postgres_controller.get_all_clovers()
        except Exception as e:
            self.bot.logger.warning(f'shiiiiittt:{e}')
        self.bot.logger.info(f'uhhh {members_safe}')
        prune_info = {'pruned': False, 'amount': 0}
        for member in clovers:
            if member.id not in members_safe:
                try:
                    new_roles = self.remove_clover(member)
                    await member.edit(
                        roles=new_roles,
                        reason="Pruned due to inactivity"
                    )
                    prune_info['pruned'] = True
                    prune_info['amount'] += 1
                except Exception as e:
                    self.bot.logger.warning(
                        f'Error pruning clovers: {e}'
                    )
        self.bot.logger.info(f'Prune info: {prune_info}')
        try:
            await self.bot.postgres_controller.reset_message_deleted()
            await self.bot.postgres_controller.reset_user_reactions()
        except Exception as e:
            self.bot.logger.warning(f'Issue resetting spam db: {e}')
        if prune_info['pruned']:
            try:
                await mod_log.send(
                    f'Pruned {prune_info["amount"]} clovers 🍀🔫')
            except Exception as e:
                self.bot.logger.warning(
                    f'Error posting prune info to mod_log: {e}')

    @commands.command()
    async def month_end(self, ctx):
        roles_to_wipe = ['member', 'active', 'regular', 'contributor', 'addicted', 'insomniac', 'no-lifer']
        local_embed = discord.Embed(
            title=f'Resetting Roles...',
            description=f'Please be patient, this might take a while...'
        )
        value_string =f'Clearing :key: role ... \n'\
                      f'Resetting *Member* role ...\n'\
                      f'Resetting *Active* role ...\n'\
                      f'Resetting *Regular* role ...\n'\
                      f'Resetting *Contributor* role ...\n'\
                      f'Resetting *Addicted* role ...\n'\
                      f'Resetting *Insomniac* role ...\n'\
                      f'Resetting *No-Lifer* role ...\n'
        local_embed.add_field(name="Progress:",
                value=value_string)
        values = value_string.split('\n')
        for index, val in enumerate(values):
            values[index] = val +'\n'
        message = await ctx.send(embed=local_embed)
        key_role = None
        for role in ctx.channel.guild.roles:
            if role.name.lower() == '🔑':
                key_role = role
        try:
            await self.rem_all_members(ctx, key_role)
            values[0] = f'Clearing :key: role :white_check_mark: \n'
            l_embed = message.embeds[0]
            l_embed.set_field_at(0 , name="Progress:", value="".join(values))
            await message.edit(embed = l_embed)
        except:
            values[0] = f'Clearing :key: role :x: \n'
            l_embed = message.embeds[0]
            l_embed.set_field_at(0, name="Progress:", value="".join(values))
            await message.edit(embed = l_embed)
        for counter, role in enumerate(roles_to_wipe):
            members = await self.get_all_members(ctx, role)
            if not members:
                values[counter+1] = f'Resetting **{role.title()}** role :x:\n'
                l_embed = message.embeds[0]
                l_embed.set_field_at(0, name="Progress:", value="".join(values))
                await message.edit(embed = l_embed)
                self.bot.logger.warning(f'ayy yo i didn"t find this one {role}')
                continue
            for member in members:
                try:
                    temp_roles = self.rem_role(member, role)
                    temp_roles = self.add_role(temp_roles, key_role)
                    await member.edit(roles=temp_roles)
                except Exception as e:
                    self.bot.logger.warning(f'Error removing {role} from {member}:\n\n{e}')
            values[counter+1] = f'Resetting **{role.title()}** role :white_check_mark:\n'
            l_embed = message.embeds[0]
            l_embed.set_field_at(0, name="Progress:", value="".join(values))
            await message.edit(embed = l_embed)

    async def rem_all_members(self, ctx, rem_role):
        for member in rem_role.members:
            roles_list = member.roles.copy()
            for counter, role in enumerate(roles_list):
                if role == rem_role:
                    roles_list = roles_list.pop(counter)
                    await member.edit(roles=roles_list)
                    continue


    async def get_all_members(self, ctx, role_name):
        found_role = None
        for role in ctx.channel.guild.roles:
            if role.name.lower() == role_name:
                found_role = role
        if not found_role:
            return None
        return found_role.members


    def add_role(self, role_list, role):
        role_list.append(role)
        return role_list

    def rem_role(self, member, role_name) -> list:
        key_index = None
        member_roles = member.roles.copy()
        for index, role in enumerate(member_roles):
            if role.name.lower() == role_name:
                key_index = index
        del member_roles[key_index]
        return member_roles
