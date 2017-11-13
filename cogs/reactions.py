"""
Class for adding custom reactions
"""
import discord
from discord.ext import commands
from .utils import checks


class Reactions():
    """
    """

    def __init__(self, bot):
        self.bot = bot
        self.triggers = []
        super().__init__()

    @commands.group(aliases=['reacts'])
    @checks.is_admin()
    async def reactions(self, ctx):
        self.triggers = await self.bot.postgres_controller.get_all_triggers()
        if ctx.invoked_subcommand is None:
            desc = ''
            for trigger in self.triggers:
                desc += f'{trigger}\n'
            local_embed = discord.Embed(
                title=f'Current Reaction Triggers:',
                description = desc,
            )
            await ctx.send(embed=local_embed)

    @reactions.command()
    @checks.is_admin()
    async def add(self, ctx, trigger, *, reaction):
        """
        Adds reaction to bot
        """
        if reaction is None:
            await ctx.send('No reaction given please use `reacts add <trigger> <reaction>')
            return
        try:
            await self.bot.postgres_controller.add_reaction(trigger, reaction.strip())
            await ctx.send('\N{OK HAND SIGN}', delete_after=3)
            self.triggers = await self.bot.postgres_controller.get_all_triggers()
        except Exception as e:
            await ctx.send('❌', delete_after=3)
            self.bot.logger.warning(f'Error adding reaction: {e}')
    
    @reactions.command(aliases=['rem'])
    @checks.is_admin()
    async def remove(self, ctx, trigger):
        """
        Removes reaction to bot
        """
        if trigger is None:
            await ctx.send('No trigger given please use `reacts rem <trigger>')
            return
        try:
            await self.bot.postgres_controller.rem_reaction(trigger)
            await ctx.send('\N{OK HAND SIGN}', delete_after=3)
            self.triggers = await self.bot.postgres_controller.get_all_triggers()
        except Exception as e:
            await ctx.send('❌', delete_after=3)
            self.bot.logger.warning(f'Error adding reaction: {e}')

    async def on_message(self, message):
        """
        Actually responds with the reaction
        """
        if self.triggers is None:
            return
        if message.clean_content in self.triggers:
            await message.channel.send(
                await self.bot.postgres_controller.get_reaction(message.clean_content)
            )


