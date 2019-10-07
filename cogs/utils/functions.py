"""Generalized Functions Hub."""

# internal modules
import re

# external modules
import discord

# relative modules

# global attributes
__all__ = ('extract_id',
           'get_role',
           'get_member',
           'get_channel',)
__filename__ = __file__.split('/')[-1].strip('.py')
__path__ = __file__.strip('.py').strip(__filename__)


def clean_str(argument: str, dtype: str = 'role'):
    argument = str(argument)
    general = argument.replace('<', '').replace('>', '')\
                      .replace('@', '')
    if dtype == 'role':
        return general.replace('&', '')
    if dtype == 'channel':
        return general.replace('#', '')
    else:
        return general.replace('#', '').replace('&', '')


def is_id(argument: str):
    """Check if argument is #.

    Parameters
    ----------
    argument: str
        text to parse

    Returns
    ----------
    str
        the bare id
    """
    # status = True
    for x in argument:
        try:
            _ = int(x)
        except Exception:
            # status = False
            return False
    return True


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
    cleaned = clean_str(argument).lower()
    try:
        ret = extract_id(argument, 'channel')
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
    cleaned = clean_str(argument, 'role').lower()
    try:
        ret = extract_id(argument, 'role')
        if not ret:
            ret = discord.utils.find(
                lambda m: (m.name.lower() == cleaned), ctx.guild.roles)
        else:
            return ctx.guild.get_role(int(ret))
        if ret:
            return ret
    except Exception:
        return False


def get_member(ctx, argument: str):
    """Tries to return a member object.

    Parameters
    ----------
    argument: str
        text to parse

    Returns
    ----------
    discord.Member
        member object to return
    """
    ret = extract_id(argument, 'member')
    t_st = clean_str(argument, 'member').lower()
    if not ret:
        ret = discord.utils.find(
            lambda m: (m.id == ret) or (m.name.lower() == t_st),
            ctx.guild.members)
    else:
        ret = ctx.guild.get_member(int(ret))
    if not ret:
        ret = ctx.guild.get_member_named(t_st)
    if ret:
        return ret
    else:
        return None


def extract_id(argument: str, dtype: str = 'member'):
    """Check if argument is # or <@#>.

    Parameters
    ----------
    argument: str
        text to parse

    Returns
    ----------
    str
        the bare id
    """
    if argument.strip(' ') == '':
        return ''
    argument = clean_str(argument, dtype)
    if is_id(argument):
        return argument
    if dtype == 'member':
        regexes = (
            r'\<?\@?(\d{17,})\>?',  # '<@!?#17+>'
            r'\<?\@?(\d{1,})\>?',  # '<@!?#+>'
            r'?(\d{17,})',  # '!?#17+>'
            r'?(\d{1,})',  # '!?#+>'
        )
    elif dtype == 'role':
        regexes = (
            r'\<?\@?\&?(\d{17,})\>?',  # '<@!?#17+>'
            r'\<?\@?\&?(\d{1,})\>?',  # '<@!?#+>'
            r'?(\d{17,})',  # '!?#17+>'
            r'?(\d{1,})',  # '!?#+>'
        )
    elif dtype == 'channel':
        regexes = (
            r'\<?\#?(\d{17,})\>?',  # '<@!?#17+>'
            r'\<?\#?(\d{1,})\>?',  # '<@!?#+>'
            r'?(\d{17,})',  # '!?#17+>'
            r'?(\d{1,})',  # '!?#+>'
        )
    else:
        regexes = (
            r'?(\d{17,})',  # '!?#17+>'
            r'?(\d{1,})',  # '!?#+>'
        )
    i = 0
    member_id = ''
    while i < len(regexes):
        regex = regexes[i]
        try:
            match = re.finditer(regex, argument, re.MULTILINE)
        except Exception:
            match = None
        i += 1
        if match is None:
            continue
        else:
            match = [x for x in match]
            if len(match) > 0:
                match = match[0]
                member_id = int(match[0], base=10)
                return str(member_id)
    return None
