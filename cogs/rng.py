from discord.ext import commands
import random as rng

class RNG(commands.Cog):

    @commands.group(pass_context=True)
    async def random(self, ctx):
        """Displays a random thing you request."""
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Incorrect random subcommand passed. Try {ctx.prefix}help random')

    @random.command()
    async def number(self, ctx, minimum=0, maximum=100):
        """Displays a random number within an optional range.
        The minimum must be smaller than the maximum and the maximum number
        accepted is 1000.
        """

        maximum = min(maximum, 1000)
        if minimum >= maximum:
            await ctx.send('Maximum is smaller than minimum.')
            return

        await ctx.send(rng.randint(minimum, maximum))

    @commands.command()
    async def choose(self, ctx, *choices: commands.clean_content):
        """Chooses between multiple choices.
        To denote multiple choices, you should use double quotes.
        """
        if len(choices) < 2:
            return await ctx.send('Not enough choices to pick from.')

        await ctx.send(rng.choice(choices)