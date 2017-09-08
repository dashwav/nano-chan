"""
Actually runs the code
"""
from bot import Nanochan
from cogs import Spoils, Filter
from asyncio import get_event_loop


def run():
    loop = get_event_loop()
    bot = Nanochan()
    post_cog = Spoils(bot)
    filter_cog = Filter(bot)
    cogs = [
      post_cog,
      filter_cog
    ]
    bot.start_bot(cogs)


if __name__ == '__main__':
    run()
