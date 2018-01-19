"""
Actually runs the code
"""
from asyncio import get_event_loop
from bot import Nanochan
from cogs import Spoils, Filter, Janitor, Logging, Stats, Owner, Reactions, Fightclub


def run():
    loop = get_event_loop()
    bot = loop.run_until_complete(Nanochan.get_instance())
    cogs = [
      Fightclub(bot),
      Logging(bot),
      Owner(bot),
      Spoils(bot),
      Filter(bot),
      Reactions(bot),
      Janitor(bot),
      Stats(bot)
    ]
    bot.start_bot(cogs)


if __name__ == '__main__':
    run()
