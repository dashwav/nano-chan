"""
I love democracy
"""

import discord
import asyncio
import re
from discord.ext import commands
from .utils import checks


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            argument = extract_member_id(argument)
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid'\
                                            'member or member ID.") from None
        else:
            return m.id


def extract_member_id(argument):
    """Check if argument is # or <@#> or <@!>."""
    regexes = (
        r'\\?\<\@!?([0-9]{18})\>',  # '<@!?#18+>'
        r'\\?\<\@!?([0-9]+)\>',  # '<@!?#+>'
        r'!?([0-9]{18})',  # '!?#18+>'
        r'!?([0-9]+)',  # '!?#18+>'
    )
    i = 0
    member_id = None
    while i < len(regexes):
        regex = regexes[i]
        match = re.findall(regex, argument)
        i += 1
        if (match is not None) and (len(match) > 0):
            member_id = int(match[0], base=10)
            return member_id
    return member_id


class GeneralMember(commands.Converter):
    async def convert(self, ctx, argument):
        member_id = extract_member_id(argument)
        if member_id is not None:
            entity = ctx.guild.get_member(member_id)
            return entity
        else:
            raise commands.BadArgument("Not a valid member.")


class Democracy(commands.Cog):

    def __init__(self, bot):
        super().__init__()

        self.bot = bot

    @commands.command()
    async def vote(self, ctx, member: GeneralMember):
        """
        Begins a vote on a user
        """
        # if member.id == ctx.author.id:
            # return
        ballot = await self.enact_democracy(member, ctx.channel)
        self.bot.loop.create_task(
            self.collect_votes(ballot, member, ctx.author))

    async def enact_democracy(self, user: discord.Member, channel):
        local_embed = discord.Embed(
            title=f'❗ Vote Started ❗',
            colour=0xF26E00,
            type='rich')
        local_embed.description = f' {user.mention} is being voted into purgatory, react to this message to cast your vote\n'\
            '\n\n*Vote closing in 30 seconds...*'
        ballot = await channel.send(embed=local_embed)
        await ballot.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        await ballot.add_reaction('\N{Cross Mark}')
        return ballot

    async def collect_votes(self, ballot: discord.Message, target: discord.Member,
                            actor: discord.Member):
        """
        Collects all votes for a message after 30 seconds
        """
        await asyncio.sleep(30)
        updatedBallot = await ballot.channel.fetch_message(ballot.id)
        allReactions = updatedBallot.reactions
        votes = {
            'yes': 0,
            'no': 0
        }
        for reaction in allReactions:
            if reaction.emoji == '\N{WHITE HEAVY CHECK MARK}':
                votes['yes'] += reaction.count
            elif reaction.emoji == '\N{Cross Mark}':
                votes['no'] += reaction.count
        if votes['yes'] + votes['no'] <= 2:
            # Not enough votes
            await self.close_vote(updatedBallot, votes)
            return
        elif votes['yes'] > votes['no']:
            # Target gets removed
            infractions = await self.bot.postgres_controller.add_user_removal(target.id, actor.id, updatedBallot.channel.id)
            await updatedBallot.delete()
            return await self.punish(target, ballot.channel, votes, infractions, None)
        elif votes['yes'] < votes['no']:
            # Actor is removed
            infractions = await self.bot.postgres_controller.add_user_removal(actor.id, actor.id, updatedBallot.channel.id)
            await updatedBallot.delete()
            return await self.punish(target, ballot.channel, votes, infractions, actor)

    async def close_vote(self, ballot: discord.Message, votes):
        """
        Clean up the embed, state the outcome
        """
        local_embed = discord.Embed(
            title=f'⛔ Vote Closed ⛔',
            colour=0x651111,
            type='rich')
        local_embed.description = f'There were not enough reactions to'\
                                  f' decide an outcome!\n\nYes votes: {votes["yes"]}\nNo votes: {votes["no"]}'
        await ballot.edit(embed=local_embed)

    async def punish(self, target: discord.Member, channel: discord.TextChannel, votes, infractions, reflection):
        """
        Gives the user the purgatory role for x amount of time
        """
        if infractions < 5:
            infractions = 5
        if reflection:
            local_embed = discord.Embed(
                title=f'✅ Vote Closed ✅',
                colour=0x419400,
                type='rich')
            local_embed.description = f'**{reflection.mention} has been removed for trying to remove {target} and failing!**\n\n'\
                                      f'Yes votes: {votes["yes"]}\nNo votes: {votes["no"]}'
            shame_role = channel.guild.get_role(self.bot.shame_role)
            await reflection.add_roles(shame_role)
            await channel.send(embed=local_embed)
            purgatory = channel.guild.get_channel(self.bot.purgatory)
            await purgatory.send(f'Welcome to purgatory {reflection.mention}! You will be let out in {infractions} minutes!')
            await asyncio.sleep(60 * infractions)
            await reflection.remove_roles(shame_role)
        else:
            local_embed = discord.Embed(
                title=f'✅ Vote Closed ✅',
                colour=0x419400,
                type='rich')
            local_embed.description = f'**{target.mention} has been removed!**\n\n'\
                                      f'Yes votes: {votes["yes"]}\nNo votes: {votes["no"]}'
            shame_role = channel.guild.get_role(self.bot.shame_role)
            await target.add_roles(shame_role)
            await channel.send(embed=local_embed)
            purgatory = channel.guild.get_channel(self.bot.purgatory)
            await purgatory.send(f'Welcome to purgatory {target.mention}! You will be let out in {infractions} minutes!')
            await asyncio.sleep(60 * infractions)
            await target.remove_roles(shame_role)
