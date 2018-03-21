"""
Database utility functions.
"""
from datetime import datetime, timedelta
from typing import Optional
from .enums import Change
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

    reacts = """
    CREATE TABLE IF NOT EXISTS {}.reacts (
        id SERIAL,
        trigger TEXT UNIQUE,
        reaction TEXT,
        created_at TIMESTAMP DEFAULT current_timestamp,
        PRIMARY KEY (id, trigger)
    );
    """.format(schema)

    clovers = """
    CREATE TABLE IF NOT EXISTS {}.clovers (
        userid BIGINT,
        logtime TIMESTAMP DEFAULT current_timestamp,
        PRIMARY KEY (logtime)
    )
    """.format(schema)

    spam = """
    CREATE TABLE IF NOT EXISTS {}.spam (
        userid BIGINT,
        logtime TIMESTAMP DEFAULT current_timestamp,
        PRIMARY KEY (logtime)
    );""".format(schema)

    roles = """
    CREATE TABLE IF NOT EXISTS {}.roles (
      serverid BIGINT,
      userid BIGINT,
      change SMALLINT,
      logtime TIMESTAMP,
      PRIMARY KEY (serverid, userid, change)
    );""".format(schema)

    emojis = """
    CREATE TABLE IF NOT EXISTS {}.emojis (
        emoji_id BIGINT,
        emoji_name TEXT,
        message_id BIGINT,
        channel_id BIGINT,
        channel_name TEXT,
        user_id BIGINT,
        user_name TEXT,
        target_id BIGINT,
        target_name TEXT,
        reaction BOOLEAN,
        animated BOOLEAN,
        logtime TIMESTAMP DEFAULT current_timestamp,
        PRIMARY KEY(emoji_id, message_id, user_id, reaction, animated)
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

    fightclub = """
    CREATE TABLE IF NOT EXISTS {}.fightclub (
        userid BIGINT,
        username varchar,
        elo INT,
        aggrowins INT,
        aggroloss INT,
        defwins INT,
        defloss INT,
        PRIMARY KEY (userid)
    );""".format(schema)

    channels = """
    CREATE TABLE IF NOT EXISTS {}.channels (
        message_id BIGINT,
        channel_id BIGINT,
        channels ANYARRAY,
        reactions INT,
        PRIMARY KEY (message_id)
    );""".format(schema)

    await pool.execute(reacts)
    await pool.execute(fightclub)
    await pool.execute(spam)
    await pool.execute(roles)
    await pool.execute(clovers)
    await pool.execute(emojis)
    await pool.execute(servers)
    await pool.execute(channels)


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

        await self.pool.execute(sql, server_id, user_id, changetype.value)

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

    async def add_emoji(self, emoji, message_id, user, target, channel, is_reaction, is_animated):
        """
        Adds emoji to emoji tracking table
        :param emoji: discord emoji to add
        """
        sql = """
        INSERT INTO {}.emojis VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
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
                target.id,
                target.name,
                is_reaction,
                is_animated
            )
        except UniqueViolationError:
            pass
    
    async def get_emoji_count(self, emoji, days_to_subtract, logger):
        """
        Returns the amount of the single emoji that were found in the last days
        """
        sql = """
        SELECT count(emoji_id) FROM {}.emojis
        WHERE emoji_id = $1 AND logtime > $2;
        """.format(self.schema)

        date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        try:
            return await self.pool.fetchval(sql, emoji.id, date_delta)
        except Exception as e:
            logger.warning(f'Error retrieving emoji count: {e}')
            return None

    async def get_user_emojis(self, user):
        """
        Returns a dict with stats about the user (probably)
        """
        user_sql = """
        SELECT * FROM {}.emojis
        WHERE user_id = $1;
        """.format(self.schema)
        target_sql = """
        SELECT * FROM {}.emojis
        WHERE target_id = $1 AND reaction = True;
        """.format(self.schema)

        user_stats = await self.pool.fetch(user_sql, user.id)
        target_stats = await self.pool.fetch(target_sql, user.id)
        ret_dict = {'user': user_stats, 'target': target_stats}
        return ret_dict

    async def get_emoji_stats(self, emoji):
        """
        Returns a dict with stats about the emoji
        """
        sql = """
        SELECT * FROM {}.emojis
        WHERE emoji_id = $1;
        """.format(self.schema)
        return await self.pool.fetch(sql, emoji.id)

    """
    Spam stuff
    """

    async def add_message_delete(self, user_id: int):
        """
        Logs a message deletion into the db
        """
        sql = """
        INSERT INTO {}.spam VALUES ($1);
        """.format(self.schema)
        await self.pool.execute(sql, user_id)

    async def get_message_deleted(self, user_id: int):
        """
        Returns count of message deletions
        """
        sql = """
        SELECT COUNT(*) FROM {}.spam
        WHERE userid = $1;
        """.format(self.schema)
        return await self.pool.fetchval(sql, user_id)

    async def reset_message_deleted(self):
        """
        Deletes all items form spam table
        """
        sql = """
        DELETE FROM {}.spam;
        """.format(self.schema)
        await self.pool.execute(sql)

    """
    Clover DB stuff
    """

    async def add_new_clover(self, member):
        """
        Adds a user to the clover db
        """
        sql = """
        INSERT INTO {}.clovers VALUES ($1);
        """.format(self.schema)
        await self.pool.execute(sql, member.id)

    async def get_all_clovers(self):
        """
        """
        sql = """
        SELECT * FROM {}.clovers;
        """.format(self.schema)
        records = await self.pool.fetch(sql)
        clover_list = []
        for record in records:
            clover_list.append(record['userid'])
        return clover_list

    async def get_all_prunable(self):
        """
        Gets all clovers who applied clover days before
        """
        sql = """
        SELECT * from {}.clovers 
        WHERE logtime::date <= (now() - '3 days'::interval);
        """.format(self.schema)
        delete_sql = """
        DELETE from {}.clovers 
        WHERE logtime::date <= (now() - '3 days'::interval);
        """.format(self.schema)
        records = await self.pool.fetch(sql)
        await self.pool.execute(delete_sql)
        prune_list = []
        for record in records:
            prune_list.append(record['userid'])
        return prune_list

    """
    Custom Reactions below
    """

    async def get_all_triggers(self):
        """
        Returns list of triggers
        """
        sql = """
        SELECT trigger FROM {}.reacts;
        """.format(self.schema)
        trigger_list = []
        records = await self.pool.fetch(sql)
        for rec in records:
            trigger_list.append(rec['trigger'])
        return trigger_list

    async def rem_reaction(self, trigger):
        """
        REmoves a value from the reacts DB
        """
        sql = """
        DELETE FROM {}.reacts WHERE trigger = $1;
        """.format(self.schema)

        await self.pool.execute(sql, trigger)

    async def add_reaction(self, trigger, reaction):
        """
        sets or updates a reaction
        """
        sql = """
        INSERT INTO {}.reacts (trigger, reaction) VALUES ($1, $2)
        ON CONFLICT (trigger)
        DO UPDATE SET
        reaction = $3 WHERE {}.reacts.trigger = $4;
        """.format(self.schema, self.schema)

        await self.pool.execute(sql, trigger, reaction, reaction, trigger)

    async def get_reaction(self, trigger):
        """
        returns a reaction TEXT
        """
        sql = """
        SELECT reaction FROM {}.reacts
        WHERE trigger = $1;
        """.format(self.schema)
        return await self.pool.fetchval(sql, trigger)

    """
    Fightclub DB stuff
    """

    async def add_fightclub_member(self, member):
        """
        Adds a user to the fight club db
        """
        sql = """
        INSERT INTO {}.fightclub VALUES ($1, $2, 1200, 0, 0, 0, 0)
        ON CONFLICT (userid)
        DO NOTHING;
        """.format(self.schema)

        await self.pool.execute(sql, member.id, member.name)
        return await self.get_fightclub_member(member)

    async def update_fightclub_member(self, member, data):
        """
        Updates a row with new data
        """
        sql = """
        UPDATE {}.fightclub
        SET elo = $1, aggrowins = $2, aggroloss = $3, defwins = $4, defloss = $5
        WHERE userid = $6;
        """.format(self.schema)

        await self.pool.execute(
            sql,
            data['elo'],
            data['aggrowins'],
            data['aggroloss'],
            data['defwins'],
            data['defloss'],
            member.id)

    async def add_fightclub_win(self, aggro, member, score):
        """
        Adds a win to a user in fight club
        """
        stats = dict(await self.get_fightclub_member(member))
        stats['elo'] = stats['elo'] + score
        if aggro:
            stats['aggrowins'] += 1
        else:
            stats['defwins'] += 1

        await self.update_fightclub_member(member, stats)

    async def add_fightclub_loss(self, aggro, member, score):
        """
        Adds a win to a user in fight club
        """
        stats = dict(await self.get_fightclub_member(member))
        stats['elo'] += score
        if aggro:
            stats['aggroloss'] += 1
        else:
            stats['defloss'] += 1

        await self.update_fightclub_member(member, stats)

    async def get_fightclub_member(self, member):
        """
        Returns a users info in dict format
        """
        sql = """
        SELECT * FROM {}.fightclub 
        WHERE userid = $1;
        """.format(self.schema)

        return await self.pool.fetchrow(sql, member.id)

    async def get_fightclub_stats(self):
        """
        Returns a dict of every fightclub member
        """
        sql = """
        SELECT * FROM {}.fightclub;
        """.format(self.schema)
        records = await self.pool.fetch(sql)
        ret_list = []
        for record in records:
            ret_list.append(dict(record))
        return ret_list


    async def add_channel_message(self, message_id, channels):
        """
        Adds a message and its related channels to the DB
        """
        sql = """
        INSERT INTO {}.channels VALUES ($1, $2, 0);
        """.format(self.schema)

        await self.pool.execute(sql, message_id, channels)

    async def add_and_get_message(self, channel_id, channel):
        """
        Adds a channel and returns the message id
        """
        sql = """
        SELECT message_id FROM {}.channels
        WHERE channel_id = $2;
        """.format(self.schema)

        react_sql = """
        SELECT reactions FROM {}.channels
        WHERE channel_id = $2;
        """.format(self.schema)

        try:
            await self.add_perm_channel(channel_id, channel)
        except Exception:
            return None
        message_id = await self.pool.fetchval(sql, channel_id)
        reactions = await self.pool.fetchval(react_sql, channel_id)
        ret_dict = {'message_id': message_id, 'reacts': reactions}
        return ret_dict

    async def add_perm_channel(self, channel_id, channel):
        """
        Adds a channel to a preexisting message
        """
        sql = """
        UPDATE {}.channels
        SET channels = array_append(channels, $1)
        WHERE channel_id = $2;
        """.format(self.schema)

        sql = """
        UPDATE {}.channels
        SET reactions = reactions + 1
        WHERE channel_id = $2;
        """.format(self.schema)

        await self.pool.execute(sql, channel, channel_id)

    async def rem_perm_channel(self, channel_id, channel):
        """
        Removes a channel from a preexisting message
        """
        sql = """
        UPDATE {}.channels
        SET channels = array_remove(channels, $1)
        WHERE channel_id = $2
        """.format(self.schema)

        await self.pool.execute(sql, channel, channel_id)