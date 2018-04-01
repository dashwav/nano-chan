import discord
import random as rng
import asyncio
from discord.ext import commands


"""
Don't talk about fight club
"""


class Fightclub():
    """
    """

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        try:
            self.bg_task = self.bot.loop.create_task(self.team_stats())
        except:
            self.bot.logger.warning("team_loop didn't work")

    async def team_stats(self):
        await asyncio.sleep(15)
        try:
            guild = self.bot.get_guild(148606162810568704)
            channel = guild.get_channel(403805028697243648)
        except Exception as e:
            self.bot.logger.warning(f'{e}')
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(120)
                full_list = await self.bot.postgres_controller.get_fightclub_stats()
                team_1_elo = 1000
                team_1_users = 0
                team_2_elo = 1000
                team_2_users = 0
                for entry in full_list:
                    if entry['team'] == 429898985734537237:
                        team_1_elo += entry['elo']
                        team_1_users += 1
                    if entry['team'] == 429899025043423232:
                        team_2_elo += entry['elo']
                        team_2_users += 1
                team_1_elo = team_1_elo / team_1_users
                team_2_elo = team_2_elo / team_2_users
                l_embed = discord.Embed(
                    title='Team Stats:',
                    description=f'Mealies elo: {team_1_elo}\nStealies elo: {team_2_elo}'
                )
                self.bot.logger.info(f'{team_1_elo} {team_2_elo}')
                await channel.send(embed=l_embed)
            except Exception as e:
                self.bot.logger.warning(f'Issue creating dm for team stats {e}')

    @commands.command()
    @commands.is_owner()
    async def assign_teams(self, ctx):
        """
        """
        try:
            team_1 = None
            team_2 = None
            for role in ctx.channel.guild.roles:
                if role.id == 429898985734537237:
                    team_1 = role
                if role.id == 429899025043423232:
                    team_2 = role
            if not team_1:
                self.bot.logger.warning('shits fucked')
                return
            if not team_2:
                self.bot.logger.warning('shits fucked yo')
                return
            for role in ctx.channel.guild.roles:
                if role.id in [375012340401176586]:
                    for member in role.members:
                        if member.id % 10 in [1,2,3,4,5]:
                            team = team_1
                        else:
                            team = team_2
                        role_list = member.roles.copy()
                        role_list.append(team)
                        try:
                            await member.edit(roles=role_list)
                        except Exception as e:
                            self.bot.logger.warning(f'error assigning role {e}')
                            pass
        except Exception as e:
            self.bot.logger.warning(f'fucked up the team shit {e}')
    
    @commands.command()
    async def assign(self, ctx):
        """
        """
        team_1 = None
        team_2 = None
        for role in ctx.channel.guild.roles:
            self.bot.logger.info(f'{role.name} - {role.id}')
            if role.id == 429898985734537237:
                team_1 = role
                continue
            if role.id == 429899025043423232:
                team_2 = role
                continue
        if not team_1:
            await ctx.send('no mealies :sad:')
            return
        if not team_2:
            await ctx.send('no stealies :sad:')
            return
        if ctx.author.id % 10 in [1,2,3,4,5]:
            team = team_1
        else:
            team = team_2
        role_list = ctx.author.roles.copy()
        role_list.append(team)
        await ctx.author.edit(roles=role_list)
        await ctx.send(f'You have been added to {team.name}', delete_after=3)
        await ctx.message.delete()

    @commands.command()
    @commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
    async def fight(self, ctx, target: discord.Member):
        """
        """
        if ctx.channel.id not in [367217621701099520, 403805028697243648, 176429411443146752]:
            return
        if ctx.message.author == target:
            return
        aggro_team = 0
        def_team = 0
        for role in ctx.message.author.roles:
            if role.id in [429898985734537237, 429899025043423232, 429935358851940353]:
                aggro_team = role.id
        for role in target.roles:
            if role.id in [429898985734537237, 429899025043423232, 429935358851940353]:
                def_team = role.id
        if aggro_team == 0:                  
            await ctx.send("you need to pick a side before you fight anyone my man `-assign` in this channel to get assigned")
            return
        if def_team == 0:
            await ctx.send("attacking a neutural? thats a pussy ass move tbh")
            return
        if aggro_team == def_team:
            await ctx.send("lmao thats friendly fire you retard")
            return
        try:
            aggressor = await self.bot.postgres_controller.get_fightclub_member(
                ctx.message.author)
            if aggressor is None:
                raise ValueError('aggressor doesnt exist yet')
        except Exception as e:
            print(f'An error occured getting stats: {e}')
            aggressor = await self.bot.postgres_controller.add_fightclub_member(
                ctx.message.author, aggro_team)
        try:
            defender = await self.bot.postgres_controller.get_fightclub_member(
                target)
            if defender is None:
                raise ValueError('defender doesnt exist yet')
        except Exception as e:
            print(f'An error occured getting stats: {e}')
            defender = await self.bot.postgres_controller.add_fightclub_member(
                target, def_team)
        aggro_elo = self.expected(aggressor['elo'], defender['elo'])
        def_elo = self.expected(defender['elo'], aggressor['elo'])
        if target.bot:
            roll = rng.randint(-1000, 1000)
        elif target.id == 164546159140929538:
            roll = rng.randint(-99999999, 1000)
        else:
            roll = rng.randint(0, 1000)
        if roll > 499:
            winner = ctx.message.author
            loser = target
            await self.bot.postgres_controller.add_fightclub_win(
                True, winner, self.elo(aggro_elo, 1))
            await self.bot.postgres_controller.add_fightclub_loss(
                False, loser, self.elo(def_elo, 0))
            await ctx.send(embed=discord.Embed(
                title='Results',
                description=f'{aggressor["username"]} '
                            f'took down {defender["username"]} '
                            f'with {roll} damage.'
            ))
        else:
            winner = target
            loser = ctx.message.author
            roll = 1000 - roll
            await self.bot.postgres_controller.add_fightclub_win(
                False, winner, self.elo(def_elo, 1.05))
            await self.bot.postgres_controller.add_fightclub_loss(
                True, loser, self.elo(aggro_elo, 0))
            await ctx.send(embed=discord.Embed(
                title='Results',
                description=f'{defender["username"]} '
                            f'took down {aggressor["username"]} '
                            f'with {roll} damage.'
            ))

    @commands.command()
    @commands.is_owner()
    async def fight_stats(self, ctx, *, member: discord.Member = None):
        if ctx.channel.id not in [367217621701099520, 403805028697243648]:
            return
        full_list = await self.bot.postgres_controller.get_fightclub_stats()
        full_elo = sorted(full_list, key=lambda user: user['elo'], reverse=True)
        if member is None:
            total_aggro_w = 0
            total_aggro_l = 0
            total_def_w = 0
            total_def_l = 0
            for entry in full_list:
                total_aggro_w += entry['aggrowins']
                total_aggro_l += entry['aggroloss']
                total_def_w += entry['defwins']
                total_def_l += entry['defloss']
            total_aggro_r = self.ratio(total_aggro_w, total_aggro_l)
            total_def_r = self.ratio(total_def_w, total_def_l)
            top_5_aggro = sorted(full_list, key=lambda user: user['aggrowins'], reverse=True)[:5]
            top_5_def = sorted(full_list, key=lambda user: user['defwins'], reverse=True)[:5]
            local_embed = discord.Embed(title='Overall Stats', description=f'Offensive Ratio: {total_aggro_r}\nDefensive Ratio: {total_def_r}')
            local_embed.add_field(name='Top 10 (by score)', value=(
                await self.get_member_string(ctx.guild, 'elo', full_elo[:10])))
            await ctx.send(embed=local_embed)
            return
        else:
            user_stats = await self.bot.postgres_controller.get_fightclub_member(member)
            aggrowr = self.ratio(user_stats['aggrowins'], user_stats['aggroloss'])
            defwr = self.ratio(user_stats['defwins'], user_stats['defloss'])
            await ctx.send(embed=discord.Embed(
                title=f'Stats for {user_stats["username"]}',
                description=f'Rank: {full_elo.index(dict(user_stats)) + 1}'
                            f'/{len(full_elo)}\n'
                            f'Score: {user_stats["elo"]}\n'
                            f'Aggressive Wins: {user_stats["aggrowins"]}\n'
                            f'Aggressive W/L: {aggrowr}\n'
                            f'Defensive Wins: {user_stats["defwins"]}\n'
                            f'Defensive W/L: {defwr}\n'
            ))

    @commands.command()
    @commands.is_owner()
    async def dock(self, ctx, member: discord.Member, amt=50):
        await self.bot.postgres_controller.add_fightclub_loss(True, member, -amt)
        await ctx.send(':okhand:')

    @commands.command()
    @commands.is_owner()
    async def full_leaderboard(self, ctx, *, amt: int=80):
        if ctx.channel.id not in [367217621701099520, 403805028697243648]:
            return
        full_list = await self.bot.postgres_controller.get_fightclub_stats()
        full_elo = sorted(full_list, key=lambda user: user['elo'], reverse=True)
        if amt == -1:
            await ctx.send(embed=discord.Embed(
                title=f'Users sorted by score:',
                description=(await self.get_member_string(
                    ctx.guild, 'elo', full_elo))))
            return
        local_embed = discord.Embed(
            title=f'Top {amt} by elo:',description='')
        count = 1
        while amt/20 > 0:
            local_embed.add_field(name=f'{((count * 20) - 20)} - {((count * 20) - 1)}', value=(await self.get_member_string(
                ctx.guild, 'elo', full_elo[((count * 20) - 20):((count * 20) - 1)])))
            count += 1
            amt -= 20
        await ctx.send(embed=local_embed)

    @commands.command()
    @commands.is_owner()
    async def final_stats(self, ctx):
        full_list = await self.bot.postgres_controller.get_fightclub_stats()
        total_aggro_w = 0
        total_aggro_l = 0
        total_def_w = 0
        total_def_l = 0
        for entry in full_list:
            total_aggro_w += entry['aggrowins']
            total_aggro_l += entry['aggroloss']
            entry['aggroratio'] = self.ratio(
                entry['aggrowins'], entry['aggroloss'])
            total_def_w += entry['defwins']
            total_def_l += entry['defloss']
            entry['defratio'] = self.ratio(entry['defwins'], entry['defloss'])
            entry['winratio'] = self.ratio(
                (entry['aggrowins']+entry['defwins']),
                (entry['aggroloss']+entry['defloss']))
        total_aggro_r = self.ratio(total_aggro_w, total_aggro_l)
        total_def_r = self.ratio(total_def_w, total_def_l)
        top_10_aggro = await self.get_member_string(
            ctx.guild,
            'aggrowins',
            sorted(
                full_list,
                key=lambda user: user['aggrowins'],
                reverse=True)[:10])
        top_10_def = await self.get_member_string(
            ctx.guild,
            'defwins',
            sorted(
                full_list,
                key=lambda user: user['defwins'],
                reverse=True)[:10])
        top_10_wr = await self.get_member_string(
            ctx.guild,
            'winratio',
            sorted(
                full_list,
                key=lambda user: user['winratio'],
                reverse=True)[:10])
        all_member_elo = await self.get_member_string(
            ctx.guild,
            'elo_final',
            sorted(
                full_list,
                key=lambda user: user['elo'],
                reverse=True))
        full_leaderboard_embed1 = discord.Embed(
            title='Full Leaderboard Page 1', description=f'')
        full_leaderboard_embed2 = discord.Embed(
            title='Full Leaderboard Page 2', description=f'')
        full_leaderboard_embed3 = discord.Embed(
            title='Full Leaderboard Page 3', description=f'')
        leaderboard_list = all_member_elo.split('\n')
        leaderboard_s = ''
        count = 0
        board = 1
        for user in leaderboard_list:
            if len(leaderboard_s) > 980:
                count += 1
                if count > 11:
                    full_leaderboard_embed3.add_field(
                    name='----', value=leaderboard_s, inline=True)
                    leaderboard_s = ''
                elif count > 5:
                    full_leaderboard_embed2.add_field(
                    name='----', value=leaderboard_s, inline=True)
                    leaderboard_s = ''
                else:
                    full_leaderboard_embed1.add_field(
                        name='----', value=leaderboard_s, inline=True)
                    leaderboard_s = ''
            leaderboard_s += f'{user}\n'
        final_stats_embed = discord.Embed(
            title='Top 10\'s', description='--------')
        final_stats_embed.add_field(
            name='Top 10 by Aggressive Wins: ', value=top_10_aggro)
        final_stats_embed.add_field(
            name='Top 10 by Defensive Wins: ', value=top_10_def)
        final_stats_embed.add_field(
            name='Top 10 by Winrate: ', value=top_10_wr)
        overall_stats_embed = discord.Embed(
            title='Overall Stats',
            description=f'-------------\n'
                        f'Total fights: {total_aggro_w + total_aggro_l}\n'
                        f'Total Aggressive wins: {total_aggro_w}\n'
                        f'Total Defensive wins: {total_def_w}\n'
                        f'Total Aggressive winrate: {total_aggro_r}\n'
                        f'Total Defensive winrate: {total_def_r}\n'
            )
        await ctx.send(embed=full_leaderboard_embed1)
        await ctx.send(embed=full_leaderboard_embed2)
        await ctx.send(embed=final_stats_embed)
        await ctx.send(embed=overall_stats_embed)

    def ratio(self, a, b):
        a = float(a)
        b = float(b)
        if b == 0:
            return a
        ratio_u = a/b
        return round(ratio_u, 2)

    async def get_member_string(self, server, attribute, usr_list):
        string = ''
        count = 0
        for member in usr_list:
            count += 1
            if attribute == 'elo_final':
                string += (
                    f'**{count}.**  {member["username"]}  '
                    f'({member["elo"]}) W/L: {member["winratio"]}\n')
                continue
            string += (f'**{count}.**  {member["username"]}  ({member[attribute]})\n')
        return string


    def expected(self, A, B):
        """
        Calculate expected score of A in a match against B
        :param A: Elo rating for player A
        :param B: Elo rating for player B
        """      
        return 1 / (1 + 10 ** ((B - A) / 400))

    def elo(self, exp, score, k=64):
        """
        Calculate the new Elo rating for a player
        :param old: The previous Elo rating
        :param exp: The expected score for this match
        :param score: The actual score for this match
        :param k: The k-factor for Elo (default: 32)
        """
        return k * (score - exp)
