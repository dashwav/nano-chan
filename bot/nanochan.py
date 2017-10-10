"""
Discord bot that spaces out spoiler comments
"""
import yaml
from discord.ext.commands import Bot
from time import time
from logging import Formatter, INFO, StreamHandler, getLogger
from utils.db_utils import PostgresController


def __get_logger():
        """
        returns a logger to be used
        :return: logger
        """
        logger = getLogger('nanochan')
        console_handler = StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(console_handler)
        logger.setLevel(INFO)
        return logger


class Nanochan(Bot):
    """
    actual bot class
    """
    def __init__(self, config, logger,
                 postgres_controller: PostgresController):
        """
        init for bot class
        """
        self.postgres_controller = postgres_controller
        self.start_time = int(time())
        self.credentials = config['token']
        self.guild_id = config['guild_id']
        self.bot_owner_id = config['owner_id']
        self.mod_log = config['mod_log']
        self.emoji_ignore_channels = config['emoji_ignore_channels']
        self.filter_channels = config['filter_channels']
        self.filter_allowed = config['filter_allowed']
        self.spoiler_channels = config['spoiler_channels']
        self.wait_time = config['wait_time']
        self.logger = logger
        super().__init__('-')

    async def get_instance(cls):
        """
        async method to initialize the postgres_controller class
        """
        with open("config/config.yml", 'r') as yml_config:
            config = yaml.load(yml_config)
        logger = __get_logger()
        postgres_cred = config['postgres_credentials']
        postgres_controller = await PostgresController.get_instance(
            logger=logger, connect_kwargs=postgres_cred)
        return cls(config, logger, postgres_controller)

    def start_bot(self, cogs):
        """
        actually start the bot
        """
        for cog in cogs:
            self.add_cog(cog)
        self.run(self.credentials)

    async def on_ready(self):
        self.logger.info(f'\nLogged in as\n{self.user.name}'
                         f'\n{self.user.id}\n------')
