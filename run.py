"""
Actually runs the code
"""
from bot import Nanochan
from cogs import Spoils, Filter, Janitor
from asyncio import get_event_loop


def run():
    loop = get_event_loop()
    bot = Nanochan()
    cogs = [
      Spoils(bot),
      Filter(bot),
      Janitor(bot)
    ]
    bot.start_bot(cogs)


if __name__ == '__main__':
    run()
