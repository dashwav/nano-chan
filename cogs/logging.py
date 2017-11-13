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
            return
        if message.author.bot:
            return
        guild = self.bot.get_guild(self.bot.guild_id)
        a_irl_member = guild.get_member(message.author.id)
        found_role = False
        for role in a_irl_member.roles:
            if role.name.lower() == 'member':
                found_role = True
        if found_role:
            try:
                mod_info = self.bot.get_channel(self.bot.mod_info)
                local_embed = discord.Embed(
                    title=f'DM report:',
                    description=message.clean_content
                )
                await mod_info.send(embed=local_embed)
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
                    await mod_info.send(
                        f'**{time} | CLOVER: **Successfully applied clover to '
                        f'{after.mention}. [Joined: {join}]')
                elif role.name.lower() == 'member':
                    for role in before.roles:
                        if role.name.lower() == 'clover':
                            return
                    await mod_info.send(
                        f'**{time} | MEMBER: **Successfully applied member to '
                        f'{after.mention}. [Joined: {join}]')

def setup(bot):
    bot.add_cog(Logging(bot))
