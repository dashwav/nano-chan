import discord
import random as rng
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

    @commands.command()
    @commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
    async def fight(self, ctx, target: discord.Member):
        """
        """
        if ctx.channel.id not in [367217621701099520, 403805028697243648]:
            return
        if ctx.message.author == target:
            return

        try:
            aggressor = await self.bot.postgres_controller.get_fightclub_member(
                ctx.message.author)
            if aggressor is None:
                raise ValueError('aggressor doesnt exist yet')
        except Exception as e:
            print(f'An error occured getting stats: {e}')
            aggressor = await self.bot.postgres_controller.add_fightclub_member(
                ctx.message.author)
        try:
            defender = await self.bot.postgres_controller.get_fightclub_member(
                target)
            if defender is None:
                raise ValueError('defender doesnt exist yet')
        except Exception as e:
            print(f'An error occured getting stats: {e}')
            defender = await self.bot.postgres_controller.add_fightclub_member(
                target)
        aggro_elo = self.expected(aggressor['elo'], defender['elo'])
        def_elo = self.expected(defender['elo'], aggressor['elo'])

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
                            f'({aggressor["elo"]} + {round(self.elo(aggro_elo, 1), 1)})'
                            f' took down {defender["username"]} '
                            f'({defender["elo"]} {round(self.elo(def_elo, 0), 1)})'
                            f' with {roll} damage.'
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
                            f'({defender["elo"]} + {round(self.elo(def_elo, 1.05), 1)})'
                            f' took down {aggressor["username"]} '
                            f'({aggressor["elo"]} {round(self.elo(aggro_elo, 0), 1)})'
                            f' with {roll} damage.'
            ))

    @commands.command()
    async def stats(self, ctx, *, member: discord.Member = None):
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

    def ratio(self, a ,b):
        a = float(a)
        b = float(b)
        if b == 0:
            return a
        ratio_u = a/b
        return round(ratio_u, 2)
 

    async def get_member_string(self, server, attribute, usr_list):
        string = ''
        for member in usr_list:
            user = server.get_member(member['userid'])
            string += (f'{member["username"]}  ({member[attribute]})\n')
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
