"""
Database utility functions.
"""
from datetime import datetime, timedelta
from typing import Optional
import random
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
    :param record: theasyncpg Record object
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
        team BIGINT,
        PRIMARY KEY (userid)
    );""".format(schema)

    channel_index = """
    CREATE TABLE IF NOT EXISTS {}.channel_index (
        message_id BIGINT,
        host_channel BIGINT,
        target_channel BIGINT,
        PRIMARY KEY (host_channel, target_channel, message_id)
    );
    """.format(schema)

    channel_react = """
    CREATE TABLE IF NOT EXISTS {0}.channel_react (
        user_id BIGINT,
        host_channel BIGINT,
        message_id BIGINT,
        target_channel BIGINT,
        PRIMARY KEY (user_id, host_channel, target_channel),
        FOREIGN KEY (host_channel, target_channel, message_id) REFERENCES {0}.channel_index (host_channel, target_channel, message_id) ON DELETE CASCADE
    );
    """.format(schema)

    reaction_spam = """
    CREATE TABLE IF NOT EXISTS {}.reaction_spam (
        user_id BIGINT,
        message_id BIGINT,
        logtime TIMESTAMP DEFAULT current_timestamp,
        PRIMARY KEY (logtime)
    );
    """.format(schema)

    reports = """
    CREATE TABLE IF NOT EXISTS {}.user_reports (
        report_id SERIAL,
        user_id BIGINT,
        message_id BIGINT,
        responder_id BIGINT DEFAULT null,
        logtime TIMESTAMP DEFAULT current_timestamp,
        response_time TIMESTAMP DEFAULT null,
        PRIMARY KEY (report_id)
    );
    """.format(schema)

    db_entries = (reacts, fightclub, spam, roles, clovers, emojis, servers, channel_index, reaction_spam, reports, channel_react)
    for db_entry in db_entries:
        await pool.execute(db_entry)


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
        if days_to_subtract != -1:
            date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        else:
            date_delta = datetime.utcnow() - timedelta(days=9999)
        try:
            return await self.pool.fetchval(sql, emoji.id, date_delta)
        except Exception as e:
            logger.warning(f'Error retrieving emoji count: {e}')
            return None

    async def get_user_emojis(self, user, days_to_subtract):
        """
        Returns a dict with stats about the user (probably)
        """
        user_sql = """
        SELECT * FROM {}.emojis
        WHERE user_id = $1 AND logtime > $2;
        """.format(self.schema)
        target_sql = """
        SELECT * FROM {}.emojis
        WHERE target_id = $1 AND logtime > $2 AND reaction = True;
        """.format(self.schema)
        if days_to_subtract != -1:
            date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        else:
            date_delta = datetime.utcnow() - timedelta(days=9999)
        user_stats = await self.pool.fetch(user_sql, user.id, date_delta)
        target_stats = await self.pool.fetch(target_sql, user.id, date_delta)
        ret_dict = {'user': user_stats, 'target': target_stats}
        return ret_dict

    async def get_emoji_stats(self, emoji, days_to_subtract):
        """
        Returns a dict with stats about the emoji
        """
        sql = """
        SELECT * FROM {}.emojis
        WHERE emoji_id = $1 AND logtime > $2;
        """.format(self.schema)
        if days_to_subtract != -1:
            date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        else:
            date_delta = datetime.utcnow() - timedelta(days=9999)
        return await self.pool.fetch(sql, emoji.id, date_delta)

    async def get_top_post_by_emoji(self, emoji, days_to_subtract, channel_id):
        """
        Returns the id for the message with highest reacts of given emoi
        """
        if days_to_subtract != -1:
            date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        else:
            date_delta = datetime.utcnow() - timedelta(days=9999)
        if channel_id:
            sql = """
            SELECT message_id as id, channel_id as ch_id, count(message_id) AS count
            FROM {}.emojis
            WHERE emoji_id = $1 AND logtime > $2 AND reaction = true AND channel_id = $3
            GROUP BY message_id, channel_id
            ORDER BY count DESC
            LIMIT 3
            """.format(self.schema)
            return await self.pool.fetch(sql, emoji.id, date_delta, int(channel_id))
        else:
            sql = """
            SELECT message_id as id, channel_id as ch_id, count(message_id) AS count
            FROM {}.emojis
            WHERE emoji_id = $1 AND logtime > $2 AND reaction = true
            GROUP BY message_id, channel_id
            ORDER BY count DESC
            LIMIT 3
            """.format(self.schema)
            return await self.pool.fetch(sql, emoji.id, date_delta)

    async def get_top_post_by_emoji_and_user(self, user_id, emoji, days_to_subtract, channel_id):
        """
        Returns the id for the message with highest reacts of given emoi for a user
        """
        if days_to_subtract != -1:
            date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        else:
            date_delta = datetime.utcnow() - timedelta(days=9999)
        if channel_id:
            sql = """
            SELECT message_id as id, channel_id as ch_id, count(message_id) AS count
            FROM {}.emojis
            WHERE emoji_id = $1 AND logtime > $2 AND reaction = true AND channel_id = $3
            AND target_id = $4
            GROUP BY message_id, channel_id
            ORDER BY count DESC
            LIMIT 3
            """.format(self.schema)
            return await self.pool.fetch(sql, emoji.id, date_delta, int(channel_id), int(user_id))
        else:
            sql = """
            SELECT message_id as id, channel_id as ch_id, count(message_id) AS count
            FROM {}.emojis
            WHERE emoji_id = $1 AND logtime > $2 AND reaction = true AND target_id = $3
            GROUP BY message_id, channel_id
            ORDER BY count DESC
            LIMIT 3
            """.format(self.schema)
            return await self.pool.fetch(sql, emoji.id, date_delta, int(user_id))

    async def get_top_post_by_reacts(self, days_to_subtract, channel_id):
        """
        Returns the id for the message with highest reacts of given emoi
        """
        if days_to_subtract != -1:
            date_delta = datetime.utcnow() - timedelta(days=days_to_subtract)
        else:
            date_delta = datetime.utcnow() - timedelta(days=9999)
        if channel_id:
            sql = """
            SELECT message_id as id, channel_id as ch_id, count(message_id) AS count
            FROM {}.emojis
            WHERE logtime > $1 AND reaction = true AND channel_id = $2
            GROUP BY message_id, channel_id
            ORDER BY count DESC
            LIMIT 3
            """.format(self.schema)
            return await self.pool.fetch(sql, date_delta, int(channel_id))
        else:
            sql = """
            SELECT message_id as id, channel_id as ch_id, count(message_id) AS count
            FROM {}.emojis
            WHERE logtime > $1 AND reaction = true
            GROUP BY message_id, channel_id
            ORDER BY count DESC
            LIMIT 3
            """.format(self.schema)
            return await self.pool.fetch(sql, date_delta)

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

    async def add_fightclub_member(self, member, team):
        """
        Adds a user to the fight club db
        """
        sql = """
        INSERT INTO {}.fightclub VALUES ($1, $2, 1200, 0, 0, 0, 0, $3)
        ON CONFLICT (userid)
        DO NOTHING;
        """.format(self.schema)

        await self.pool.execute(sql, member.id, member.name, team)
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

    """
    Channel Message React Stuff
    """
    async def add_channel_message(self, message_id, target_channel, host_channel):
        """
        Adds a link in the database
        """
        sql = """
        INSERT INTO {}.channel_index (message_id, host_channel, target_channel) VALUES ($1, $2, $3);
        """.format(self.schema)
        
        await self.pool.execute(sql, message_id, host_channel, target_channel)

    async def get_message_info(self, host_channel, target_channel):
        """
        returns the info on a message
        """
        sql = """
        SELECT message_id FROM {}.channel_index
        WHERE host_channel = $1 AND target_channel = $2;
        """.format(self.schema)

        try:
            return await self.pool.fetchval(sql, host_channel, target_channel)
        except:
            return None

    async def get_all_channels(self):
        """
        Returns all of the reaction channels
        """
        sql = """
        SELECT target_channel, message_id, host_channel FROM {}.channel_index;
        """.format(self.schema)

        try:
            return await self.pool.fetch(sql)
        except:
            return None

    async def get_target_channel(self, host_channel, message_id):
        """
        Returns the target channel of a message
        """
        sql = """
        SELECT target_channel FROM {}.channel_index
        WHERE host_channel = $1 AND message_id = $2;
        """.format(self.schema)

        try:
            return await self.pool.fetchval(sql, host_channel, message_id)
        except:
            return None

    async def rem_channel_message(self, target_channel, host_channel):
        """
        Deletes a link from the database
        """
        sql = """
        DELETE from {}.channel_index
        WHERE host_channel = $1 AND target_channel = $2;
        """.format(self.schema)

        await self.pool.execute(sql, host_channel, target_channel)

    async def get_chanreacts_fromuser(self, user_id):
        """
        Returns all of the reaction channels id from new db
        """
        sql = """
            SELECT target_channel FROM {}.channel_react WHERE user_id = $1;
        """.format(self.schema)

        try:
            return await self.pool.fetch(sql, user_id)
        except:
            return None

    async def get_chanreacts_fromchan(self, host_channel, target_channel):
        """
        Returns all of the reaction channels id from new db
        """
        sql = """
            SELECT user_id FROM {}.channel_react WHERE host_channel = $1 AND target_channel = $2;
        """.format(self.schema)

        try:
            return await self.pool.fetch(sql, host_channel, target_channel)
        except:
            return None

    async def add_user_chanreact(self, user_ids, host_channel, message_id, target_channel):
        """
        Returns all of the reaction channels
        """
        sql = """
            INSERT INTO {}.channel_react (user_id, host_channel, message_id, target_channel)  VALUES ($1, $2, $3, $4);
            """.format(self.schema)

        for user_id in str(user_ids).split(','):
            try:
                await self.pool.execute(sql, int(user_id), host_channel, message_id, target_channel)
            except:
                continue
        return True

    async def rm_user_chanreact(self, user_id, target_channel, host_channel):
        """
        Returns all of the reaction channels
        """
        sql = """
            DELETE FROM {}.channel_react WHERE user_id = $1 AND target_channel = $2 AND host_channel = $3;
            """.format(self.schema)

        return await self.pool.execute(sql, user_id, target_channel, host_channel)

    async def rm_channel_chanreact(self, target_channel, host_channel):
        """
        Returns all of the reaction channels
        """
        sql = """
            DELETE FROM {}.channel_react WHERE target_channel = $1 AND host_channel = $2;
            """.format(self.schema)

        return await self.pool.execute(sql, target_channel, host_channel)

    """
    User Reaction Spam Stuff
    """

    async def add_user_reaction(self, user_id, message_id):
        """
        Logs a reaction to the db
        """
        sql = """
        INSERT INTO {}.reaction_spam VALUES ($1, $2);
        """.format(self.schema)

        sql2 = """
        SELECT COUNT(*) FROM {}.reaction_spam
        WHERE user_id = $1 AND message_id = $2;
        """.format(self.schema)

        await self.pool.execute(sql, user_id, message_id)
        return await self.pool.fetchval(sql2, user_id, message_id)

    async def reset_user_reactions(self):
        """
        Resets tracker for reactions
        """

        sql = """
        DELETE FROM {}.reaction_spam;
        """.format(self.schema)
        await self.pool.execute(sql)

    """
    Report Stuff
    """

    async def add_user_report(self, user_id):
        """
        Adds a user report
        """

        sql = """
        INSERT INTO {}.user_reports (report_id, user_id) VALUES (DEFAULT, $1)
        RETURNING report_id;
        """.format(self.schema)

        return await self.pool.fetchval(sql, user_id)

    async def set_report_message_id(self, report_id, message_id):
        """
        Sets the message_id of the report
        """

        sql = """
        UPDATE {}.user_reports 
        SET message_id = $1
        WHERE report_id = $2;
        """.format(self.schema)
        
        await self.pool.execute(sql, message_id, report_id)

    async def add_user_report_response(self, report_id, responder_id):
        """
        Adds a response to a message
        """

        sql = """
        UPDATE {}.user_reports 
        SET response_time = current_timestamp, responder_id = $1
        WHERE report_id = $2;
        """.format(self.schema)
        
        await self.pool.execute(sql, responder_id, report_id)
        

    async def get_user_report(self, report_id):
        """
        Returns a user_report
        """

        sql = """
        SELECT * FROM {}.user_reports
        WHERE report_id = $1;
        """.format(self.schema)

        return await self.pool.fetch(sql, report_id)
