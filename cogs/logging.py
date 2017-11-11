"""
Cog for logging info to mod-info
"""
import discord


class Logging():

    def __init__(self, bot):
        self.bot = bot
        self.mod_info = bot.get_channel(bot.mod_info)
        super().__init__()

    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            time = self.bot.timestamp()
            join = after.joined_at.strftime('%b %d $Y $H:$M')
            role_diff = set(after.roles) - (set(before.roles))
            for role in role_diff:
                if role.name.lower() == 'clover':
                    await self.mod_info.send(
                        f'**{time} | CLOVER:**Successfully applied clover to '
                        f'{message.author.display_name}. [Joined: {join}]')
                elif role.name.lower() == 'member':
                    await self.mod_info.send(
                        f'**{time} | MEMBER:**Successfully applied member to '
                        f'{message.author.display_name}. [Joined: {join}]')