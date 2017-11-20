import socket
from datetime import datetime
from typing import Any, Dict, Optional, Tuple  # noqa: F401

import aiohttp  # noqa: F401
import aioodbc.cursor  # noqa: F401

from lib.api import twitch
from lib import cache
from lib.database import DatabaseMain

from . import library


async def checkLiveStreams(timestamp: datetime) -> None:
    data: cache.CacheStore
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with cache.get_cache() as data,\
            DatabaseMain.acquire() as db,\
            await db.cursor() as cursor:
        try:
            query: str
            channels: Dict[str, Tuple[str, bool]] = {}
            query = 'SELECT broadcaster, isEvent FROM multitwitch'
            await cursor.execute(query)
            channel: str
            event: bool
            async for channel, event in cursor:
                if not await data.twitch_load_id(channel):
                    continue
                id: Optional[str] = await data.twitch_get_id(channel)
                if id is None:
                    continue
                channels[channel] = id, event
            if not channels:
                return
            channelsList: str
            channelsList = ','.join(channels[c][0] for c in channels)
            uri: str = '/kraken/streams?channel=' + channelsList
            response: aiohttp.ClientResponse
            streamsData: Optional[Dict[str, Any]]
            response, streamsData = await twitch.get_call(None, uri)
            if response.status == 200 and streamsData is not None:
                for stream in streamsData['streams']:
                    channel = stream['channel']['name'].lower()
                    query = '''
UPDATE multitwitch SET lastLive=? WHERE broadcaster=?
'''
                    await cursor.execute(query, (timestamp, channel))

            lastLiving: datetime = timestamp - library.liveCooldown
            query = '''
DELETE FROM multitwitch WHERE lastLive<? AND isEvent=FALSE
'''
            await cursor.execute(query, (lastLiving,))
            query = '''
DELETE FROM multitwitch
    WHERE addedTime<? AND lastLive IS NULL AND isEvent=FALSE
'''
            await cursor.execute(query, (lastLiving,))
            query = '''
DELETE FROM multitwitch
    WHERE twitchgroup IN (
        SELECT twitchgroup
            FROM multitwitch
            GROUP BY twitchgroup
             HAVING COUNT(*)=1)
'''
            await cursor.execute(query)
            await db.connection.commit()
        except socket.gaierror:
            pass
