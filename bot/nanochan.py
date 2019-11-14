"""
Discord bot that spaces out spoiler comments
"""
import gila
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
    def __init__(self, config, misc_config, logger, test,
                 pg_controller: PostgresController, chanreact, blacklist):
        """
        init for bot class
        """
        self.pg_controller = pg_controller
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
        self.timeout_id = misc_config['timeout_id']
        self.logger = logger
        self.chanreact = chanreact
        self.blglobal = blacklist
        super().__init__('-')

    @staticmethod
    def _record_to_dict(rec) -> dict:
        ret = {}
        for key, val in rec.items():
            ret[key] = int(val)
        return ret

    @classmethod
    async def get_instance(cls):
        """
        async method to initialize the pg_controller class
        """
        config = gila.Gila()
        misc_config = gila.Gila()
        config.set_config_file('config/config.yml')
        misc_config.set_config_file('config/misc_config.yml')
        config.read_config_file()
        misc_config.read_in_config()
        config = config.all_config()
        misc_config = misc_config.all_config()

        logger = getLogger('nanochan')
        console_handler = StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(console_handler)
        logger.setLevel(INFO)
        postgres_cred = config['postgres_credentials']
        pg_controller = await PostgresController.get_instance(
            logger=logger, connect_kwargs=postgres_cred)
        blgu = await pg_controller.get_all_blacklist_users_global()
        chanreact = await pg_controller.get_all_channels()
        chanreact = [cls._record_to_dict(x) for x in chanreact]  # cache the react channel_message as target_channel, message_id, host_channel
        return cls(config, misc_config, logger, False, pg_controller, chanreact, blgu)

    @classmethod
    async def get_test_instance(cls):
        """
        async method to everything except the pg_controller
        """
        config = gila.Gila()
        misc_config = gila.Gila()
        config.set_config_file('config/config.yml')
        misc_config.set_config_file('config/misc_config.yml')
        config.read_config_file()
        misc_config.read_config_file()
        config = config.all_config()
        misc_config = misc_config.all_config()
        logger = getLogger('nanochan')
        console_handler = StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(console_handler)
        logger.setLevel(INFO)
        postgres_cred = config['postgres_credentials']
        pg_controller = await PostgresController.get_instance(
            logger=logger, connect_kwargs=postgres_cred)
        chanreact = await pg_controller.get_all_channels()
        blgu = await pg_controller.get_all_blacklist_users_global()
        chanreact = [cls._record_to_dict(x) for x in chanreact]  # cache the react channel_message as target_channel, message_id, host_channel
        return cls(config, misc_config, logger, False, pg_controller, chanreact, blgu)

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
        await self.change_presence(activity=discord.Game(name=f'!faq in #commands-channel'))
        self.logger.info(f'\nLogged in as\n{self.user.name}'
                         f'\nVersion:\n {self.version}'
                         f'\n{self.user.id}\n------')

    async def on_message(self, ctx):
        # specifically handle blacklisted users
        if ctx.author.id not in self.blglobal:
            await self.process_commands(ctx)
        else:
            return
