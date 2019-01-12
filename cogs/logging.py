"""
Cog for logging info to mod-info
"""
import discord


class Logging():

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def on_message(self, message):
        if not isinstance(message.channel, discord.DMChannel):
            if message.channel.id != 367217621701099520:
                return
            if len(message.attachments) > 0:
                await message.channel.send('Worst Girl')
            return
        if message.author.bot:
            return
        found_role = True
        if found_role:
            try:
                mod_info = self.bot.get_channel(259728514914189312)
                local_embed = discord.Embed(
                    title=f'DM report from {message.author.name}#{message.author.discriminator}:',
                    description=message.clean_content
                )
                if message.attachments:
                    desc = ''
                    for file in message.attachments:
                        desc += f'{file.url}\n'
                    local_embed.add_field(
                        name='Attachments',
                        value=f'{desc}',
                        inline=True
                    )
                await mod_info.send(embed=local_embed)
                await message.channel.send(':white_check_mark: You have submitted a report to the moderators. Abusing this function will get you kicked or banned. Thanks.')
                for user_id in self.bot.dm_forward:
                    user = await self.bot.get_user_info(user_id)
                    await user.create_dm()
                    await user.dm_channel.send(embed=local_embed)
            except Exception as e:
                self.bot.logger.warning(f'Issue forwarding dm: {e}')

    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            mod_info = self.bot.get_channel(self.bot.mod_info)
            time = self.bot.timestamp()
            join = after.joined_at.strftime('%b %d %Y %H:%M')
            role_diff = set(after.roles) - (set(before.roles))
            for role in role_diff:
                if role.name.lower() == 'clover':
                    await self.bot.postgres_controller.add_new_clover(after)
                    await mod_info.send(
                        local_embed = discord.Embed(
                            color = 0x419400,
                            title = 'Clover',
                            description = f'**{time}: **Successfully applied clover to '
                                f'{after.mention}. [Joined: {join}]'))
                elif role.name.lower() == 'member':
                    for role in before.roles:
                        if '🔑' in role.name.lower():
                            return
                        elif role.name.lower() == 'clover':
                            return
                    await mod_info.send(
                        local_embed = discord.Embed(
                            color = 0x3498DB,
                            title = 'Member',
                            description = f'**{time} **Successfully applied member to '
                                f'{after.mention}. [Joined: {join}]'))

def setup(bot):
    bot.add_cog(Logging(bot))
