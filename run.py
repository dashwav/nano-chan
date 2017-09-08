"""
Actually runs the code
"""
from bot import Spoilerbot
from cogs import Spoils, Filter
from asyncio import get_event_loop


def run():
    loop = get_event_loop()
    bot = Spoilerbot()
    post_cog = Spoils(bot)
    filter_cog = Filter(bot)
    cogs = [
      post_cog,
      filter_cog
    ]
    bot.start_bot(cogs)


if __name__ == '__main__':
    run()
