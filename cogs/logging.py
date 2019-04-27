"""
Cog for logging info to mod-info
"""
import discord
from discord.ext import commands
import random


class Logging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.Cog.listener()
    async def on_message(self, message):
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
        found_role = True
        if found_role:
            try:
                report_id = await self.bot.postgres_controller.add_user_report(
                    message.author.id)
                mod_info = self.bot.get_channel(259728514914189312)
                local_embed = discord.Embed(
                    title=f'DM report from {message.author.name}#{message.author.discriminator}:',
                    description=message.clean_content
                )
                local_embed.set_footer(text=report_id)
                if message.attachments:
                    desc = ''
                    for file in message.attachments:
                        desc += f'{file.url}\n'
                    local_embed.add_field(
                        name='Attachments',
                        value=f'{desc}',
                        inline=True
                    )
                report_message = await mod_info.send(embed=local_embed)
                await message.channel.send(':white_check_mark: You have submitted a report to the moderators. Abusing this function will get you kicked or banned. Thanks.')
                await self.bot.postgres_controller.set_report_message_id(
                    report_id, report_message.id
                )
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
    async def respond(self, ctx, report_id: int, *, response):
        """
        Respond back 
        """
        if not response:
            await ctx.send("Please add a message", delete_after=3)

        local_embed = discord.Embed(
                    title=f'Response from the mod team:',
                    description=response
                )

        report = await self.bot.postgres_controller.get_user_report(report_id)
        user = await self.bot.fetch_user(report["user_id"])
        await user.create_dm()
        await user.dm_channel.send(embed=local_embed)

        await self.bot.postgres_controller.add_user_report_response(
            ctx.author.id, report_id 
        )
        

def setup(bot):
    bot.add_cog(Logging(bot))
