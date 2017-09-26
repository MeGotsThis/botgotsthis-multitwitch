import socket
from datetime import datetime
from typing import Any, Dict, Optional  # noqa: F401

import aiohttp  # noqa: F401
import aioodbc.cursor  # noqa: F401

import bot
import bot.utils
from lib.api import twitch
from lib import database

from . import library


async def checkLiveStreams(timestamp: datetime) -> None:
    database_: database.Database
    cursor: aioodbc.cursor.Cursor
    async with database.get_database() as database_, \
            await database_.cursor() as cursor:
        try:
            query: str
            channels: Dict[str, bool] = {}
            query = 'SELECT broadcaster, isEvent FROM multitwitch'
            await cursor.execute(query)
            channel: str
            event: bool
            async for channel, event in cursor:
                if not await bot.utils.loadTwitchId(channel):
                    continue
                if bot.globals.twitchId[channel] is None:
                    continue
                channels[channel] = event
            if not channels:
                return
            channelsList: str
            channelsList = ','.join(str(bot.globals.twitchId[c])
                                    for c in channels)
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
            await database_.connection.commit()
        except socket.gaierror:
            pass
