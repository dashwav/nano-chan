"""
This cog queries an ical that has a list of birthdays and posts
in a chat if there is one on the current day WIP
"""
import icalendar
import aiohttp


class Birthdays():

    def __init__(self, bot):
        super().__init__()
        self.bot = bot


"""
Wow this never went anywhere
"""