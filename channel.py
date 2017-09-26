import random
from datetime import datetime, timedelta  # noqa: F401
from typing import Any, List, Optional, Tuple, cast  # noqa: F401

import aioodbc.cursor  # noqa: F401

from bot import utils
from lib.api import twitch
from lib.data import ChatCommandArgs
from lib.helper.chat import not_feature

from . import library


@not_feature('nomultitwitch')
async def commandMultiTwitch(args: ChatCommandArgs) -> bool:
    '''
    Example Commands:
    !multitwitch << gives a link of linked multitwitch, available to everyone
    !multitwitch kadgar << available to everyone
    !multitwitch preference kadgar << available to everyone
    !multitwitch add
    !multitwitch add kappa
    !multitwitch drop
    !multitwitch reset
    !multitwitch remove kappa
    !multitwitch remove
    !multitwitch event kappa << owner command, does not perform auto removal

    The command should automatically remove inactive streams of more than
    5 minutes or 15 minutes after the initial add if stream hasnt started
    '''

    # TODO: mypy fix after https://github.com/python/mypy/issues/1855

    currentTime: datetime = utils.now()
    cursor: aioodbc.cursor
    query: str
    params: Tuple[Any, ...]
    paramsM: List[Tuple[Any, ...]]
    row: Tuple[Any, ...]
    group: str
    groupO: Optional[str]
    groups: List[Tuple[Any, ...]]
    event: Optional[bool]
    async with await args.database.cursor() as cursor:
        if (len(args.message) < 2 or not args.permissions.moderator
                or args.message.lower[1] in library.multiUrls):
            cooldown: timedelta = timedelta(seconds=30)
            if args.permissions.moderator:
                cooldown = timedelta(seconds=10)
            if (not args.permissions.broadcaster
                    and 'multitwitch' in args.chat.sessionData):
                since: timedelta
                since = currentTime - args.chat.sessionData['multitwitch']
                if since < cooldown:
                    return False

            query = 'SELECT twitchgroup FROM multitwitch WHERE broadcaster=?'
            await cursor.execute(query, (args.chat.channel,))
            groupO = (await cursor.fetchone() or [None])[0]
            twitches: List[str] = []
            if groupO:
                query = '''
SELECT broadcaster, addedTime, lastLive FROM multitwitch
    WHERE twitchgroup=? ORDER BY isEvent DESC, addedTime ASC
'''
                async for row in await cursor.execute(query, (groupO,)):
                    broadcaster: str
                    added: datetime
                    live: datetime
                    broadcaster, added, live = row
                    if live is None:
                        if currentTime - added > library.addedCooldown:
                            continue
                    else:
                        if currentTime - live > library.liveCooldown:
                            continue
                    twitches.append(broadcaster)
            if not twitches:
                args.chat.send(f'https://www.twitch.tv/{args.chat.channel}')
                if args.permissions.moderator:
                    args.chat.send('''\
Just do !multitwitch add <twitch user> to create/start a multitwitch link''')
                args.chat.sessionData['multitwitch'] = currentTime
                return True

            default: str = await args.database.getChatProperty(
                args.chat.channel, 'multitwitch', library.default, str)
            preference: str = await args.database.getChatProperty(
                args.nick, 'multitwitch', default, str)
            if (len(args.message) >= 2
                    and args.message.lower[1] in library.multiUrls):
                preference = args.message.lower[1]
            if len(twitches) == 1:
                args.chat.send('https://www.twitch.tv/' + twitches[0])
            elif preference in library.multiUrls:
                args.chat.send(library.multiUrls[preference](twitches))
            else:
                args.chat.send(library.multiUrls[library.default](twitches))
            args.chat.sessionData['multitwitch'] = currentTime
            return True

        if args.message.lower[1] == 'preference':
            if len(args.message) < 2:
                await args.database.setChatProperty(args.nick, 'multitwitch',
                                                    None)
            elif args.message.lower[2] in library.multiUrls:
                await args.database.setChatProperty(args.nick, 'multitwitch',
                                                    args.message.lower[2])
            else:
                args.chat.send('Unrecognized multitwitch site')

        if not args.permissions.moderator:
            return False

        if args.message.lower[1] == 'add':
            other: str
            if len(args.message) < 3:
                other = args.nick
            else:
                other = args.message.lower[2]
                if not await twitch.is_valid_user(other):
                    args.chat.send(f'{other} is not a valid Twitch user')
                    return True
            if other == args.chat.channel:
                args.chat.send('You cannot add yourself for multitwitch link')
                return True
            query = '''
SELECT broadcaster, twitchgroup, isEvent FROM multitwitch
    WHERE broadcaster IN (?, ?)'''
            params = args.chat.channel, other
            groups = [row async for row in await cursor.execute(query, params)]
            if len(groups) == 0:
                alphabet = ('0123456789'
                            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                            'abcdefghijklmnopqrstuvwxyz')
                group = ''.join(random.choice(alphabet) for i in range(7))
                query = '''
INSERT INTO multitwitch (broadcaster, twitchgroup, addedTime)
    VALUES (?, ?, ?)'''
                paramsM = [(args.chat.channel, group, currentTime),
                           (other, group, currentTime)]
                await cursor.executemany(query, paramsM)
                args.chat.send(f'''\
Created a multitwitch for {args.chat.channel} and {other}''')
            elif len(groups) == 1:
                group = groups[0][1]
                toAdd: str
                done: str
                toAdd = args.chat.channel if groups[0][0] == other else other
                done = args.chat.channel if groups[0][0] != other else other
                query = '''
INSERT INTO multitwitch (broadcaster, twitchgroup, addedTime)
    VALUES (?, ?, ?)'''
                await cursor.execute(query, (toAdd, group, currentTime))
                args.chat.send(f'''\
Added {toAdd} to the multitwitch of {done} and others''')
            else:
                group = groups[0][1]
                g: Tuple[str, str, bool]
                for g in cast(List[Tuple[str, str, bool]], groups):
                    if g[2]:
                        group = g[1]
                        break
                query = '''
UPDATE multitwitch SET twitchgroup=? WHERE twitchgroup=?'''
                paramsM = [(g[1], group) for g in groups if g[1] != group]
                if not paramsM:
                    args.chat.send(f'''\
{args.chat.channel} and {other} are already in the same multitwitch''')
                    return True
                await cursor.executemany(query, paramsM)
                args.chat.send(f'''\
Merged the multitwitches of {args.chat.channel} and {other}''')
            await args.database.commit()

        if args.message.lower[1] in ['drop', 'delete', 'del' 'remove', 'rem']:
            who: str
            if len(args.message) < 3:
                who = args.chat.channel
            else:
                who = args.message.lower[2]
            query = '''
SELECT twitchgroup, isEvent FROM multitwitch
    WHERE twitchgroup=(SELECT twitchgroup FROM multitwitch WHERE broadcaster=?)
        AND broadcaster=?'''
            await cursor.execute(query, (args.chat.channel, who))
            groupO, event = await cursor.fetchone() or [None, None]  # type: ignore  # noqa: E501
            if groupO is None:
                args.chat.send(f'''\
Multitwitch of {who} does not exist or is not part of the same multitwitch of \
{args.chat.channel}''')
                return True

            query = 'SELECT COUNT(*) FROM multitwitch WHERE twitchgroup=?'
            await cursor.execute(query, (groupO,))
            if (await cursor.fetchone())[0] <= 2:
                query = 'DELETE FROM multitwitch WHERE twitchgroup=?'
                await cursor.execute(query, (groupO,))
                if args.chat.channel == who:
                    args.chat.send(f'''\
Reset the multitwitch of {args.chat.channel} and others''')
                else:
                    args.chat.send(f'''\
Reset the multitwitch of {args.chat.channel} and {who}''')
                await args.database.commit()
                return True

            if not event:
                query = 'DELETE FROM multitwitch WHERE broadcaster=?'
                await cursor.execute(query, (who,))
                if who == args.chat.channel:
                    args.chat.send(f'''\
Removed {args.chat.channel} from a multitwitch''')
                else:
                    args.chat.send(f'''\
Removed {who} from a multitwitch with {args.chat.channel}''')
                await args.database.commit()
                return True

            query = '''
SELECT COUNT(*) FROM multitwitch WHERE twitchgroup=? AND isEvent=0
UNION ALL SELECT COUNT(*) FROM multitwitch WHERE twitchgroup=? AND isEvent=1'''
            await cursor.execute(query, (groupO,) * 2)
            notEvent, = await cursor.fetchone()
            inEvent, = await cursor.fetchone()
            if notEvent > 0:
                args.chat.send(f'''\
Cannot remove {who} until all non-event users are removed''')
                return True

            query = 'DELETE FROM multitwitch WHERE broadcaster=?'
            await cursor.execute(query, (who,))
            if who == args.chat.channel:
                args.chat.send(f'''\
Removed {args.chat.channel} from a multitwitch''')
            else:
                args.chat.send(f'''\
Removed {who} from a multitwitch with {args.chat.channel}''')
            await args.database.commit()

        if args.message.lower[1] == 'reset':
            query = 'SELECT twitchgroup FROM multitwitch WHERE broadcaster=?'
            await cursor.execute(query, (args.chat.channel,))
            groupO, = await cursor.fetchone() or [None]  # type: ignore
            if groupO is None:
                args.chat.send(f'''\
Multitwitch of {args.chat.channel} does not exist''')
                return True

            query = '''
SELECT COUNT(*) FROM multitwitch WHERE twitchgroup=? AND isEvent=0
UNION ALL SELECT COUNT(*) FROM multitwitch WHERE twitchgroup=? AND isEvent=1'''
            await cursor.execute(query, (groupO,) * 2)
            notEvent, = await cursor.fetchone()
            inEvent, = await cursor.fetchone()
            if notEvent > 0 and inEvent > 1:
                query = '''
DELETE FROM multitwitch WHERE twitchgroup=? AND isEvent=0'''
                await cursor.execute(query, (groupO,))
                args.chat.send('Reset the multitwitch of non-event users')
                await args.database.commit()
                return True

            query = 'DELETE FROM multitwitch WHERE twitchgroup=?'
            await cursor.execute(query, (groupO,))
            args.chat.send(f'''\
Reset the multitwitch of {args.chat.channel} and others''')
            await args.database.commit()

        if args.message.lower[1] == 'event' and args.permissions.owner:
            if len(args.message) < 3:
                who = args.chat.channel
            else:
                who = args.message.lower[2]
            query = '''
SELECT twitchgroup, isEvent FROM multitwitch
    WHERE twitchgroup=(SELECT twitchgroup FROM multitwitch WHERE broadcaster=?)
        AND broadcaster=?'''
            await cursor.execute(query, (args.chat.channel, who))
            groupO, event = await cursor.fetchone() or [None, None]  # type: ignore  # noqa: E501
            if groupO is not None:
                query = 'UPDATE multitwitch SET isEvent=? WHERE broadcaster=?'
                await cursor.execute(query, (not event, who,))
                if not event:
                    args.chat.send(f'{who} is marked as an event multitwitch')
                else:
                    args.chat.send(
                        f'{who} is unmarked from an event multitwitch')
                await args.database.commit()
            else:
                args.chat.send(f'''\
Multitwitch of {who} does not exist or is not part of the same multitwitch of \
{args.chat.channel}''')

        return True
