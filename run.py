"""
Actually runs the code
"""
import sys
from asyncio import get_event_loop
from bot import Nanochan
from cogs import Spoils, Filter, Pingy, Channels, Janitor, Logging, Stats, Owner, Reactions, Fightclub


def run(test: bool):
    loop = get_event_loop()
    if test:
        bot = loop.run_until_complete(Nanochan.get_test_instance())
    else:
        bot = loop.run_until_complete(Nanochan.get_instance())
    cogs = [
      Fightclub(bot),
      Logging(bot),
      Owner(bot),
      Spoils(bot),
      Filter(bot),
      Reactions(bot),
      Janitor(bot),
      Stats(bot),
      Channels(bot),
      Pingy(bot)
    ]
    bot.start_bot(cogs)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run(True)
    run(False)
