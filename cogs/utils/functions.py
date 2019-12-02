"""Generalized Functions Hub."""

# internal modules
import math
import datetime
import pickle
import warnings
warnings.filterwarnings("ignore")

# external modules
import asyncio
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import discord
from discord.ext import commands

# relative modules


class MemberID(commands.Converter):
    """Extract a member id and force to be in guild."""

    """
    The main purpose is for banning people and forcing
    the to-be-banned user in the guild.
    """
    async def convert(self, ctx, argument):
        """Discord converter."""
        try:
            argument = extract_id(argument)
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return str(int(argument, base=10))
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid'\
                                            'member or member ID.") from None
        else:
            can_execute = ctx.author.id == ctx.bot.owner_id or \
                ctx.author == ctx.guild.owner or \
                ctx.author.top_role > m.top_role

            if not can_execute:
                raise commands.BadArgument('You cannot do this action on this'
                                           ' user due to role hierarchy.')
            return m


class BannedMember(commands.Converter):
    """Find a banned user."""

    async def convert(self, ctx, argument):
        """Discord converter."""
        ban_list = await ctx.guild.bans()
        member_id = extract_id(argument)
        if member_id is not None:
            entity = discord.utils.find(
                lambda u: str(u.user.id) == str(member_id), ban_list)
            return entity
        else:
            raise commands.BadArgument("Not a valid previously-banned member.")

class GeneralRole(commands.Converter):
    """Generalized role maker."""

    """
    This will try to resolve a role given some argument,
    if unable to and the argument is an id, will contruct a fake role.
    If argument isn't an id then fail
    """
    async def convert(self, ctx, argument):
        """Discord Convert."""
        failed = False
        target = None
        try:
            target = get_role(ctx, argument)
        except Exception as e:
            failed = True
            self.bot.logger.warning(f'Problems resolving role, making a fake role. Probably was removed from the guild. {e}')  # noqa
        if failed or target is None:
            try:
                role_id = extract_id(argument)
                assert role_id is not None
                target = create_fake_role(role_id)
                target.guild = ctx.guild
            except Exception as e:
                self.bot.logger.warning(f'Problems resolving role, making a fake role. Probably was removed from the guild. {e}')  # noqa
        if target is not None:
            return target
        else:
            raise commands.BadArgument("Not a valid role.")


class GeneralMember(commands.Converter):
    """Generalized member maker."""

    """
    This will try to resolve a member given some argument,
    if unable to and the argument is an id, will contruct a fake user.
    If argument isn't an id then fail
    """
    async def convert(self, ctx, argument):
        """Discord Convert."""
        failed = False
        target = None
        try:
            target = get_member(ctx, argument)
        except Exception as e:
            failed = True
            self.bot.logger.warning(f'Problems resolving member, making a fake user. Probably was removed from the guild. {e}')  # noqa
        if failed or target is None:
            try:
                member_id = extract_id(argument)
                assert member_id is not None
                target = create_fake_user(member_id)
                target.guild = ctx.guild
                target.bot = False
            except Exception as e:
                self.bot.logger.warning(f'Problems resolving member, making a fake user. Probably was removed from the guild. {e}')  # noqa
        if target is not None:
            return target
        else:
            raise commands.BadArgument("Not a valid member.")


def create_fake(target_id: str, dtype: str = 'member'):
    """General ABC creator."""
    if dtype == 'member':
        return create_fake_user(target_id)
    elif dtype == 'role':
        return create_fake_role(target_id)


def create_fake_user(user_id: str):
    """Create fake ABC for a user."""
    member = fake_object(int(user_id))
    member.name = 'GenericUser'
    member.displayname = member.name
    member.discriminator = '0000'
    member.mention = f'<@{member.id}>'
    member.joined_at = datetime.datetime.utcnow()
    member.bot = False
    return member

def create_fake_role(role_id: str):
    """Create fake ABC for a role."""
    role = fake_object(int(role_id))
    role.name = 'GenericRole'
    role.displayname = role.name
    role.mention = f'<@&{role.id}>'
    role.created = datetime.datetime.utcnow()
    return role

class fake_object:
    """Recreate ABC class."""

    def __init__(self, snowflake):
        """Init. Method."""
        self.id = int(snowflake)
        self.name = ''
        self.created_at = datetime.datetime.utcnow()

    def __repr__(self):
        """Repr method."""
        return ''.format(self.id)

    def __eq__(self, other):
        """Equiv Method."""
        return self.id == other.id


def get_member(ctx, argument: str):
    """Return a member object."""
    """
    Parameters
    ----------
    argument: str
        text to parse

    Returns
    ----------
    discord.Member
        member object to return
    """
    ret = extract_id(argument)
    t_st = argument.lower()
    if not ret:
        ret = discord.utils.find(lambda m: (m.id == ret) or
                                           (t_st in [m.name.lower(), m.display_name.lower()]),  # noqa
                                 ctx.guild.members)
    else:
        ret = ctx.guild.get_member(int(ret))
    if not ret:
        ret = ctx.guild.get_member_named(t_st)
    if ret:
        return ret
    else:
        return None


def extract_id(argument: str, strict: bool=True):
    """Extract id from argument."""
    """
    Parameters
    ----------
    argument: str
        text to parse

    Returns
    ----------
    str
        the bare id
    """
    ex = ''.join(list(filter(str.isdigit, str(argument))))
    if len(ex) < 15 and strict:
        return None
    return ex

def get_channel(ctx, argument: str):
    """Tries to return a channel object.

    Parameters
    ----------
    argument: str
        text to parse

    Returns
    ----------
    discord.Channel
        channel object to return
    """
    cleaned = argument.lower()
    try:
        ret = extract_id(argument)
        if not ret:
            ret = discord.utils.find(lambda m: (m.id == ret) or
                (m.name.lower() == cleaned), ctx.guild.channels) # noqa
        else:
            return ctx.guild.get_channel(int(ret))
        if ret:
            return ret
    except Exception:
        return False


def get_role(ctx, argument: str):
    """Tries to return a role object.

    Parameters
    ----------
    argument: str
        text to parse

    Returns
    ----------
    discord.Role
        role object to return
    """
    cleaned = argument.lower()
    try:
        ret = extract_id(argument)
        if not ret:
            ret = discord.utils.find(
                lambda m: (m.name.lower() == cleaned), ctx.guild.roles)
        else:
            return ctx.guild.get_role(int(ret))
        if ret:
            return ret
    except Exception:
        return False

async def add_perms(bot, user, channel):
    """
    Adds a user to channels perms
    """
    try:
        await channel.set_permissions(user, read_messages=True)
    except Exception as e:
        bot.logger.warning(f'{e}')

async def deny_perms(bot, user, channel):
    """
    Sets perm to deny a users perms on a channel
    """
    try:
        await channel.set_permissions(user, read_messages=False)
    except Exception as e:
        bot.logger.warning(f'{e}')

async def remove_perms(bot, user, channel):
    """
    removes a users perms on a channel
    """
    try:
        await channel.set_permissions(user, read_messages=None)
    except Exception as e:
        bot.logger.warning(f'{e}')

def chunk(l, n):  
    # looping till length l 
    for i in range(0, len(l), n):  
        yield l[i:i + n] 

async def plot_leaderboard(bot, ctx):
    server_id = ctx.guild.id

    fac = 8.6

    def exp_to_level(exp: int):
        return math.floor(math.sqrt(exp) / fac)

    def level_to_exp(lvl: int):
        return math.ceil((lvl * fac) ** 2)

    def frac_to_level(exp: int):
        level = exp_to_level(exp)  # current level
        totalexp = level_to_exp(level + 1)  # total exp of the next level
        diffexp = (totalexp - exp) / (totalexp - level_to_exp(level))
        return 1. - diffexp

    URL = f'https://www.danbo.space/api/v1/servers/{server_id}'

    # sending get request and saving the response as response object 
    try:
        r = requests.get(url = URL) 

        # extracting data in json format 
        data = r.json()

        # Example data
        users = list(map(lambda x: [f'{x["name"]}#{x["disc"]}', x["level"], level_to_exp(x["level"] + 1),
                                    frac_to_level(x["experience"]), x["experience"]], data['users']))
        users.sort(key=lambda x: x[-1], reverse=True)
    except Exception:
        bot.logger.warn('Unable to get leaderboard')
        await ctx.message.add_reaction(r'❌')
        return False

    # open a file, where you ant to store the data
    f = open(f'leaderboard{server_id}.pickle', 'wb')
    pickle.dump(users, f)
    f.close()
    bot.logger.info('Wrote pickle')
    try:

        pdf = PdfPages(f"leaderboard{server_id}.pdf")
        for i, people in enumerate(chunk(users, 100)):
            amount = len(people)
            if amount < 10:
                amount = 10
            font = 14
            # for plot width
            good_amount_min = 10.
            good_amount_max = 100.
            good_width_min = 1.5
            good_width_max = 10
            width_slope = (good_width_max - good_width_min) / (good_amount_max - good_amount_min)
            width_b = good_width_max - good_amount_max * width_slope
            # for plot height
            good_height_min = 1.
            good_height_max = 2
            height_slope = (good_height_max - good_height_min) / (good_amount_max - good_amount_min)
            height_b = good_height_max - good_amount_max * height_slope
            widthfac = amount * width_slope + width_b
            height_fac = amount * height_slope + height_b

            figsize = (amount / widthfac, amount * height_fac) # noqa
            fig, ax = plt.subplots(figsize=figsize) # noqa
            exp = []
            y_pos = []
            names = []
            for i, x in enumerate(people):
                exp.append(int(x[-2] * 100.))
                names.append(f'{x[0]}    Level: {x[1]}    Exp: {int(x[-1])}/{int(x[2])}')
            y_pos = list(range(len(people)))
            bar = ax.barh(y_pos, exp, 0.75, align='center', alpha=0.5)
            ax.invert_yaxis()
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, rotation=0, horizontalalignment='left', fontsize=font, color='white')
            ax.set_xticks([])
            ax.set_xticklabels([])
            ax.tick_params('y', direction='in', pad=-30)
            ax.margins(y=0.05 * (10 / amount))
            ax.set_facecolor('#2C2F33')
            ax.set_title(f'Leaderboard for: {server_id} on {datetime.datetime.now()}', fontsize=font, color='black')
            pdf.savefig(fig, bbox_inches='tight')
        pdf.close()
        return f'leaderboard{server_id}'
    except Exception as e:
        bot.logger.warn(f'Unable to plot leaderboard, but pickle should be available. Will continue with rest.{e}')
        await ctx.message.add_reaction(r'❌')
        return False


# end of code

# end of file
