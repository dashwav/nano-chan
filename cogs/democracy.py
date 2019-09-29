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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            message_content = message.content
            if message_content.split(' ')[0].lower() == "remove":
                #TODO: add remove vote
                pass
            elif message_content.split(' ')[0].lower() == "keep":
                #TODO: add keep vote
                pass
        if message.channel.id != self.bot.good_meme_channel:
            return
        if not message.attachments:
            return
        SHRUG = 623740401764794391
        UPARROW = 624465937164140564
        DOWNARROW = 624465662995202052
        guild = await self.bot.fetch_guild(333342931601588253)
        shrug = await guild.fetch_emoji(SHRUG)
        up = await guild.fetch_emoji(UPARROW)
        down = await guild.fetch_emoji(DOWNARROW)

        #Set up Ballot voting
        await message.clear_reactions()
        await message.add_reaction(up)
        await message.add_reaction(shrug)
        await message.add_reaction(down)

        await self.bot.postgres_controller.add_meme_ballot(
            message.author.id, message.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Called when an emoji is added
        """
        if payload.user_id in [333344884696285184, 333803905337262080]:
            return
        channel = self.bot.get_channel(payload.channel_id)
        user = self.bot.get_user(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        SHRUG = 623740401764794391
        UPARROW = 624465937164140564
        DOWNARROW = 624465662995202052
        #TODO: abstract to config file
        if payload.channel_id not in [self.bot.good_meme_channel]:
            return
        if payload.emoji.id in [DOWNARROW, UPARROW, SHRUG]:
            # Down arrow
            if payload.emoji.id == DOWNARROW:
                vote = 2
            # Up arrow
            if payload.emoji.id == UPARROW:
                vote = 1
            # Shrug
            if payload.emoji.id == SHRUG:
                vote = 0
            vote_count = await self.bot.postgres_controller.add_meme_vote(
                payload.user_id,
                payload.message_id,
                vote
            )
            yes_count = 0
            no_count = 0
            shrug_count = 0
            print(f"voteCOunt: {vote_count}")
            for votes in vote_count:
                if votes["vote"] == 0:
                    shrug_count = votes["count"]
                elif votes["vote"] == 1:
                    yes_count = votes["count"]
                elif votes["vote"] == 2:
                    no_count = votes["count"]
            keep_votes = shrug_count + yes_count
            total_votes = keep_votes + no_count
            no_ratio = no_count / total_votes

            # There needs to be at least this many votes
            #TODO: abstract to config file
            if total_votes < self.bot.vote_total:
                return

            # NO votes ratio for removal
            #TODO: abstract to config file
            if no_ratio < self.bot.vote_ratio:
                return
            try:
                self.bot.logger.debug(f"Okay hit it lmao \nyes votes: {keep_votes} no votes: {no_count}")
                author = message.author
                await message.delete()
                await channel.send(f"{author.mention}, your message has been deemed unworthy")
                await self.bot.postgres_controller.add_meme_removal(
                    author.id,
                    message.id
                )
            except Exception as e:
                self.bot.logger.error(f"Issue deleting bad meme: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Called when an emoji is removed
        """
        if payload.user_id in [333344884696285184, 333803905337262080]:
            return
        channel = self.bot.get_channel(payload.channel_id)
        user = self.bot.get_user(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        SHRUG = 623740401764794391
        UPARROW = 624465937164140564
        DOWNARROW = 624465662995202052
        #TODO: abstract to config file
        if payload.channel_id not in [self.bot.good_meme_channel]:
            return
        #TODO: abstract to config file
        if payload.emoji.id not in [SHRUG, UPARROW, DOWNARROW]:
            return
        # Down arrow
        if payload.emoji.id == DOWNARROW:
            vote = 2
        # Up arrow
        if payload.emoji.id == UPARROW:
            vote = 1
        # Shrug
        if payload.emoji.id == SHRUG:
            vote = 0
        try:
            await self.bot.postgres_controller.rem_meme_vote(
                user.id,
                message.id,
                vote
            )
        except Exception as e:
            self.bot.logger.error(f"Error removing vote: {e}")