from discord.ext import commands
from discord.utils import find


class Pingy():

    def __init__(self, bot):
        """
        init for cog class
        """
        super().__init__()
        self.bot = bot

    @commands.command()
    async def pingy(self, ctx, *roles: commands.clean_content):
        """
        Pings all the roles in the command
        """
        if not roles:
            await ctx.send(":thinking:")
            await ctx.message.delete()
        guild_roles = ctx.guild.roles
        found_roles = []
        for role in roles:
            if role.lower() not in ['dedicated', 'updated', 'moderator', 'admin', 'representative']:
                continue
            guild_role = find(lambda m: m.name.lower() == role.lower(), guild_roles)
            if not guild_role:
                continue
            found_roles.append(guild_role)
        if not found_roles:
            return
        mention_str = ""
        for role in found_roles:
            await role.edit(mentionable=True)
            mention_str += f'{role.mention} '
        await ctx.send(mention_str)
        for role in found_roles:
            await role.edit(mentionable=False)
