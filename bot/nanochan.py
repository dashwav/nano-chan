"""
Discord bot that spaces out spoiler comments
"""
import yaml
import os
import discord
from discord.ext.commands import Bot
from time import time
import datetime
from logging import Formatter, INFO, StreamHandler, getLogger
from cogs.utils.db_utils import PostgresController


class Nanochan(Bot):
    """
    actual bot class
    """
    def __init__(self, config, logger, test,
                 postgres_controller: PostgresController):
        """
        init for bot class
        """
        self.postgres_controller = postgres_controller
        self.start_time = int(time())
        self.version = discord.__version__
        if test:
            self.credentials = os.environ['TOKEN']
        else:
            self.credentials = config['token']
        self.guild_id = config['guild_id']
        self.mod_log = config['mod_log']
        self.mod_info = config['mod_info']
        self.emoji_ignore_channels = config['emoji_ignore_channels']
        self.traffic_ignore_channels = config['traffic_ignore_channels']
        self.filter_channels = config['filter_channels']
        self.filter_allowed = config['filter_allowed']
        self.spoiler_channels = config['spoiler_channels']
        self.wait_time = config['wait_time']
        self.clover_days = config['clover_days']
        self.dm_forward = config['dm_forward']
        self.logger = logger
        super().__init__('-')

    @classmethod
    async def get_instance(cls):
        """
        async method to initialize the postgres_controller class
        """
        with open("config/config.yml", 'r') as yml_config:
            config = yaml.load(yml_config)
        logger = getLogger('nanochan')
        console_handler = StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(console_handler)
        logger.setLevel(INFO)
        postgres_cred = config['postgres_credentials']
        postgres_controller = await PostgresController.get_instance(
            logger=logger, connect_kwargs=postgres_cred)
        return cls(config, logger, False, postgres_controller)

    @classmethod
    async def get_test_instance(cls):
        """
        async method to everything except the postgres_controller
        """
        with open("config/config.yml", 'r') as yml_config:
            config = yaml.load(yml_config)
        logger = getLogger('nanochan')
        console_handler = StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(console_handler)
        logger.setLevel(INFO)
        postgres_cred = config['postgres_credentials']
        postgres_controller = await PostgresController.get_instance(
            logger=logger, connect_kwargs=postgres_cred)
        return cls(config, logger, True, postgres_controller)

    def start_bot(self, cogs):
        """
        actually start the bot
        """
        for cog in cogs:
            self.add_cog(cog)
        self.run(self.credentials)

    def timestamp(self):
        """
        returns a timestamp formatted string
        """
        current = datetime.datetime.utcnow()
        return current.strftime('%H:%M:%S')

    async def on_ready(self):
        await self.change_presence(game=discord.Game(name=f'!faq in #commands-channel'))
        self.logger.info(f'\nLogged in as\n{self.user.name}'
                         f'\nVersion:\n {self.version}'
                         f'\n{self.user.id}\n------')
