"""
This cog is to be used primarily for small janitorial tasks 
(removing clover once member is hit, pruning clovers)
"""

class Janitor():
    """
    The main class wrapepr
    """
    __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_message(self, message):
        if message.author.bot:
            return
        has_clover = False
        clover_index = None
        has_member = False
        member_roles = message.author.roles
        for index, role in enumerate(member_roles):
            if role.name.lower() == 'clover':
                has_clover = True
                clover_index = index
            elif role.name.lower() == 'member':
                has_member = True

        if has_clover and has_member:
            member_roles.del(clover_index)
            try:
                await message.author.edit(
                    roles=member_roles,
                    reason="User upgraded from clover to member")
                await message.add_reaction('🎊')
            except Exception as e:
                self.bot.logger.warning(f'Error updating users roles: {e}')
