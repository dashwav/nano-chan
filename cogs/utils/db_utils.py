"""
Database utility functions.
"""
from datetime import datetime, timedelta
from json import dumps, loads
from typing import Optional
from .enums import Change, Action
try:
    from asyncpg import Record, InterfaceError, UniqueViolationError, create_pool
    from asyncpg.pool import Pool
except ImportError:
    Record = None
    Pool = None
    print('asyncpg not installed, PostgresSQL function not available.')


def parse_record(record: Record) -> Optional[tuple]:
    """
    Parse a asyncpg Record object to a tuple of values
    :param record: the asyncpg Record object
    :return: the tuple of values if it's not None, else None
    """
    try:
        return tuple(record.values())
    except AttributeError:
        return None


async def make_tables(pool: Pool, schema: str):
    """
    Make tables used for caching if they don't exist.
    :param pool: the connection pool.
    :param schema: the schema name.
    """
    await pool.execute('CREATE SCHEMA IF NOT EXISTS {};'.format(schema))

    spam = """
    CREATE TABLE IF NOT EXISTS {}.spam (
        userid BIGINT,
        logtime TIMESTAMP DEFAULT current_timestamp,
    );""".format(schema)

    roles = """
    CREATE TABLE IF NOT EXISTS {}.roles (
      serverid BIGINT,
      userid BIGINT,
      change SMALLINT,
      logtime TIMESTAMP,
      PRIMARY KEY (serverid, userid, change)
    );""".format(schema)

    moderation = """
    CREATE TABLE IF NOT EXISTS {}.moderation (
      serverid BIGINT,
      modid BIGINT,
      targetid BIGINT,
      action SMALLINT,
      logtime TIMESTAMP DEFAULT current_timestamp,
      PRIMARY KEY (serverid, modid, targetid, action)
    );
    """.format(schema)

    emojis = """
    CREATE TABLE IF NOT EXISTS {}.emojis (
        id BIGINT,
        name TEXT,
        message_id BIGINT,
        channel_id BIGINT,
        channel_name TEXT,
        user_id BIGINT,
        user_name TEXT,
        reaction BOOLEAN,
        logtime TIMESTAMP DEFAULT current_timestamp,
        PRIMARY KEY(id, message_id, user_id, reaction)
    );
    """.format(schema)

    messages = """
    CREATE TABLE IF NOT EXISTS {}.messages (
      serverid BIGINT,
      messageid BIGINT UNIQUE,
      authorid BIGINT,
      authorname TEXT,
      channelid BIGINT,
      channelname TEXT,
      pinned BOOLEAN,
      content VARCHAR(2000),
      createdat TIMESTAMP,
      PRIMARY KEY (serverid, messageid, authorid, channelid)
    );
    """.format(schema)

    servers = """
    CREATE TABLE IF NOT EXISTS {}.servers (
      serverid BIGINT,
      assignableroles varchar ARRAY,
      filterwordswhite varchar ARRAY,
      filterwordsblack varchar ARRAY,
      blacklistchannels integer ARRAY,
      r9kchannels integer ARRAY,
      addtime TIMESTAMP DEFAULT current_timestamp,
      PRIMARY KEY (serverid)
    );""".format(schema)

    await pool.execute(roles)
    await pool.execute(moderation)
    await pool.execute(emojis)
    await pool.execute(messages)
    await pool.execute(servers)


class PostgresController():
    """
    We will use the schema 'nanochan' for the db
    """
    __slots__ = ('pool', 'schema', 'logger')

    def __init__(self, pool: Pool, logger, schema: str = 'nanochan'):
        self.pool = pool
        self.schema = schema
        self.logger = logger

    @classmethod
    async def get_instance(cls, logger=None, connect_kwargs: dict = None,
                           pool: Pool = None, schema: str = 'nanochan'):
        """
        Get a new instance of `PostgresController`
        This method will create the appropriate tables needed.
        :param logger: the logger object.
        :param connect_kwargs:
            Keyword arguments for the
            :func:`asyncpg.connection.connect` function.
        :param pool: an existing connection pool.
        One of `pool` or `connect_kwargs` must not be None.
        :param schema: the schema name used. Defaults to `minoshiro`
        :return: a new instance of `PostgresController`
        """
        assert logger, (
            'Please provide a logger to the data_controller'
        )
        assert connect_kwargs or pool, (
            'Please either provide a connection pool or '
            'a dict of connection data for creating a new '
            'connection pool.'
        )
        if not pool:
            try:
                pool = await create_pool(**connect_kwargs)
                logger.info('Connection pool made.')
            except InterfaceError as e:
                logger.error(str(e))
                raise e
        logger.info('Creating tables...')
        await make_tables(pool, schema)
        logger.info('Tables created.')
        return cls(pool, logger, schema)

    async def insert_rolechange(self, server_id: int, user_id: int,
                                changetype: Change):
        """
        Inserts into the roles table a new rolechange
        :param user_id: the id of the user changed
        :param changetype: The type of change that occured
        """
        sql = """
        INSERT INTO {}.roles VALUES ($1, $2, $3);
        """.format(self.schema)

        await self.pool.execute(sql,server_id, user_id, changetype.value)

    async def insert_modaction(self, server_id: int, mod_id: int,
                               target_id: int, action_type: Action):
        """
        Inserts into the roles table a new rolechange
        :param mod_id: the id of the mod that triggered the action
        :param target_id: the id of user that action was performed on
        :param action_type: The type of change that occured
        """
        sql = """
        INSERT INTO {}.moderation VALUES ($1, $2, $3);
        """.format(self.schema)

        await self.pool.execute(
            sql, server_id, mod_id, target_id, action_type.value)

    async def add_server(self, server_id: int):
        """
        Inserts into the server table a new server
        :param server_id: the id of the server added
        """
        sql = """
        INSERT INTO {}.servers VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (serverid)
        DO nothing;
        """.format(self.schema)

        await self.pool.execute(sql, server_id, [], [], [], [], [])

    async def add_whitelist_word(self, server_id: int, word: str):
        """
        Adds a word that is allowed on the whitelist channels
        :param server_id: the id of the server to add the word to
        :param word: word to add
        """
        return

    async def add_message(self, message):
        """
        Adds a message to the database
        :param message: the discord message object to add
        """
        sql = """
        INSERT INTO {}.messages VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (messageid)
        DO nothing;
        """.format(self.schema)
        await self.pool.execute(
            sql,
            message.guild.id,
            message.id,
            message.author.id,
            message.author.name,
            message.channel.id,
            message.channel.name,
            message.pinned,
            message.clean_content,
            message.created_at
        )

    async def add_emoji(self, emoji, message_id, user, channel, is_reaction):
        """
        Adds emoji to emoji tracking table
        :param emoji: discord emoji to add
        """
        sql = """
        INSERT INTO {}.emojis VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """.format(self.schema)
        try:
            await self.pool.execute(
                sql,
                emoji.id,
                emoji.name,
                message_id,
                channel.id,
                channel.name,
                user.id,
                user.name,
                is_reaction
            )
        except UniqueViolationError:
            pass
    
    async def get_emoji_count(self, emoji, days_to_subtract, logger):
        """
        Returns the amount of the single emoji that were found in the last days
        """
        sql = """
        SELECT count(id) FROM {}.emojis
        WHERE id = $1 AND logtime > $2;
        """.format(self.schema)

        date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        try:
            return await self.pool.fetchval(sql, emoji.id, date_delta)
        except Exception as e:
            logger.warning(f'Error retrieving emoji count: {e}')
            return None

    async def add_blacklist_word(self, server_id: int, word: str):
        """
        Adds a word that is not allowed on the server
        :param server_id: the id of the server to add the word to
        :param word: word to add
        """
        return

    async def add_message_delete(self, user_id: int):
        """
        Logs a message deletion into the db
        """
        sql = """
        INSERT INTO {}.spam VALUES ($1);
        """.format(self.schema)
        await self.pool.execute(sql, user_id)

    async def get_message_delete(self, user_id: int):
        """
        Returns count of message deletions
        """
        sql = """
        SELECT COUNT(*) FROM {}.spam
        WHERE userid = $1;
        """.format(self.schema)
        return await self.pool.fetchrow(sql, user_id)


    async def add_whitelist_channel(self, server_id: int, channel_id: int):
        """
        Adds a channel that will delete all but the messages containing a
        string in the 'whitelist' column of the server row
        :param server_id: the id of the server to add the word to
        :param word: word to add
        """
        return

    async def add_r9k_channel(self, server_id: int, channel_id: int):
        """
        this would be a cool thing to have
        """
        return
