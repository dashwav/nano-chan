"""
Cog for logging info to mod-info
"""
import discord
from discord.ext import commands
import random
import datetime
from .utils import checks


class Logging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in self.bot.blglobal:
            return
        if not isinstance(message.channel, discord.DMChannel):
            if message.channel.id != 429536153251741706:
                return
            if len(message.attachments) > 0:
                if random.randint(1, 10) > 8:
                    return
                await message.channel.send(
                    random.choice([
                        # doing it this way cause i don't want to actually implement probability
                        'Worst girl',
                        'Best girl',
                        'Worst girl',
                        'Best girl',
                        'Worst girl',
                        'Best girl',
                        'Worst girl',
                        'Best girl',
                        'Worst girl',
                        'Best girl',
                        'Worst girl',
                        'Best girl',
                        'Ew.',
                        'LMAO :joy: :joy:',
                        'Why is this even in the show'
                    ])
                )
            return
        if message.author.bot:
            return
        try:
            content = message.clean_content
            desc = ''
            if message.attachments:
                for file in message.attachments:
                    desc += f'{file.url}\n'
                    content += f':=:{file.url}'

            report_id = await self.bot.postgres_controller.add_user_report(
                message.author.id, content)
            mod_info = self.bot.get_channel(259728514914189312)
            local_embed = discord.Embed(
                title=f'DM report from {message.author.name}#{message.author.discriminator}:',
                description=message.clean_content
            )
            local_embed.set_footer(text=f'Report ID: {report_id}')
            if message.attachments:
                local_embed.add_field(
                    name='Attachments',
                    value=f'{desc}',
                    inline=True
                )
            report_message = await mod_info.send(embed=local_embed)
            await mod_info.send(f'You can respond to this report by typing:\n```\n-respond {report_id} <message here>```')
            await message.channel.send(f':white_check_mark: You have submitted a report to the moderators. Abusing this function will get you kicked or banned. Thanks.\n\nThis report id is {report_id}')
            await self.bot.postgres_controller.set_report_message_id(
                report_id, report_message.id
            )
        except Exception as e:
            self.bot.logger.warning(f'Issue sending report to channel: {e}')
        try:
            for user_id in self.bot.dm_forward:
                user = await self.bot.fetch_user(user_id)
                await user.create_dm()
                await user.dm_channel.send(embed=local_embed)
        except Exception as e:
            self.bot.logger.warning(f'Issue forwarding dm: {e}')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            mod_info = self.bot.get_channel(self.bot.mod_info)
            time = self.bot.timestamp()
            join = after.joined_at.strftime('%b %d %Y %H:%M')
            role_diff = set(after.roles) - (set(before.roles))
            for role in role_diff:
                if role.name.lower() == 'clover':
                    await self.bot.postgres_controller.add_new_clover(after)
                    local_embed = discord.Embed(
                            color=0x419400,
                            title='Clover',
                            description=f'**{time}: **Successfully applied clover to '
                                        f'{after.mention}. [Joined: {join}]')
                    local_embed.set_footer(text=f'{after}')
                    await mod_info.send(embed=local_embed)
                elif role.name.lower() == 'member':
                    for role in before.roles:
                        if '🔑' in role.name.lower():
                            return
                        elif role.name.lower() == 'clover':
                            return
                    local_embed = discord.Embed(
                            color=0x3498DB,
                            title='Member',
                            description=f'**{time} **Successfully applied member to '
                                        f'{after.mention}. [Joined: {join}]')
                    local_embed.set_footer(text=f'{after}')
                    await mod_info.send(embed=local_embed)

    @commands.command()
    @checks.has_permissions(manage_roles=True)
    async def respond(self, ctx, report_id: int, *, response):
        """
        Respond back 
        """
        if not response:
            await ctx.send("Please add a message", delete_after=3)

        local_embed = discord.Embed(
                    title=f'Response from the mod team for report {report_id}:',
                    description=response
                )
        local_embed.set_footer(text=f'Report ID: {report_id}')
        if ctx.message.attachments:
            desc = ''
            for file in ctx.message.attachments:
                desc += f'{file.url}\n'
            local_embed.add_field(
                name='Attachments',
                value=f'{desc}',
                inline=True
            )
        try:
            report = await self.bot.postgres_controller.get_user_report(report_id)
            user = await self.bot.fetch_user(report[0]["user_id"])
            await user.create_dm()
            await user.dm_channel.send(embed=local_embed)

            await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

            await self.bot.postgres_controller.add_user_report_response(
                report_id, ctx.author.id)

            report_message = await ctx.channel.fetch_message(report[0]['message_id'])
            report_embed = report_message.embeds[0]
            report_embed.add_field(name="Response", value=f"[Link to response]({ctx.message.jump_url})")
            await self.bot.postgres_controller.set_report_message_content(
                report_id, report[0]['message'] + f';=;{ctx.message.jump_url}')
            await report_message.edit(embed=report_embed)
        except Exception as e:
            self.bot.logger.warning(f'Error in responding to report: {e}')  

    @commands.command()
    @checks.has_permissions(manage_roles=True)
    async def rebuild(self, ctx, report_id: int):
        """
        Rebuild a collapsed report
        """
        try:
            report = await self.bot.postgres_controller.get_user_report(report_id)
        except:
            await ctx.send('Couldn\'t find this report :(', delete_after=10)
            return
        report = report[0]
        content, attachments, responces = '', [], []
        if ':=:' in report['message']:
            content = report['message'].split(':=:')[0]
            attachments = report['message'].split(':=:')[1:]
            attachments[-1] = attachments[-1].split(';=;')[0]
        elif ';=;' in report['message']:
            content = report['message'].split(';=;')[0]
        else:
            content = report['message']
        if ';=;' in report['message']:
            responces = report['message'].split(';=;')[1:]

        local_embed = discord.Embed(
            title=f'DM report from <@{report["user_id"]}>:',
            description=content
        )
        local_embed.set_footer(text=f'Report ID: {report_id}')
        if len(attachments) > 0:
            desc = ''
            for f in attachments:
                desc += f'<{f}>\n'
            local_embed.add_field(
                name='Attachments',
                value=f'{desc}',
                inline=True
            )
        if len(responces) > 0:
            for f in responces:
                desc = f'[Link to responce]({f})'
                local_embed.add_field(
                    name='Response',
                    value=f'{desc}',
                    inline=True
                )
        try:
            message = await ctx.send(embed=local_embed)
            await self.bot.postgres_controller.set_report_message_id(
                report_id, message.id
            )
        except Exception as e:
            self.bot.logger.warning(f'Error in responding to report: {e}')
            return 

def setup(bot):
    bot.add_cog(Logging(bot))
