"""
Cog for logging info to mod-info
"""
import discord


class Logging():

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def on_message(self, message):
        if not message.channel isinstance(discord.DMChannel):
            return
        if message.author.bot:
            return
        guild = self.get_guild(self.bot.guild_id)
        a_irl_member = guild.get_member(message.author.id)
        found_role = False
        for role in member.roles:
            if role.name.lower() = 'member':
                found_role = True
        if found_role:
            mod_info = self.get_channel(self.mod_info)
            local_embed = discord.Embed(
                title=f'DM report:',
                description=message.clean_content
            )
            await mod_info.send(embed=local_embed)

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
