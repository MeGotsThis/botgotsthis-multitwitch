import datetime

from bot.coroutine import background
from . import tasks


async def call_check(timestamp: datetime.datetime) -> None:
    await tasks.checkLiveStreams(timestamp)


background.add_task(call_check, datetime.timedelta(minutes=1))
