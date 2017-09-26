import datetime

from typing import Callable, Dict, Iterable

addedCooldown: datetime.timedelta = datetime.timedelta(minutes=15)
liveCooldown: datetime.timedelta = datetime.timedelta(minutes=5)


def urlMultiTwitch(twitches: Iterable[str]) -> str:
    return 'http://multitwitch.tv/' + '/'.join(twitches)


def urlKadgar(twitches: Iterable[str]) -> str:
    return 'http://kadgar.net/live/' + '/'.join(twitches)


def urlSpeedrunTv(twitches: Iterable[str]) -> str:
    return 'http://speedrun.tv/' + '/'.join(twitches)


def urlKbmod(twitches: Iterable[str]) -> str:
    return 'http://kbmod.com/multistream/' + '/'.join(twitches)


multiUrls: Dict[str, Callable[[Iterable[str]], str]] = {
    'multitwitch': urlMultiTwitch,
    'kadgar': urlKadgar,
    'speedruntv': urlSpeedrunTv,
    'kbmod': urlKbmod,
    }
default: str = 'multitwitch'


def raceMultiTwitch(twitches: Iterable[str], raceid: str) -> str:
    return 'http://multitwitch.tv/' + '/'.join(twitches)


def raceKadgar(twitches: Iterable[str], raceid: str) -> str:
    return 'http://kadgar.net/live/' + '/'.join(twitches)


def raceSpeedrunTv(twitches: Iterable[str], raceid: str) -> str:
    return 'http://speedrun.tv/race:' + raceid + '/' + '/'.join(twitches)


def raceKbmod(twitches: Iterable[str], raceid: str) -> str:
    return 'http://kbmod.com/multistream/' + '/'.join(twitches)


raceUrls: Dict[str, Callable[[Iterable[str], str], str]] = {
    'multitwitch': raceMultiTwitch,
    'kadgar': raceKadgar,
    'speedruntv': raceSpeedrunTv,
    'kbmod': raceKbmod,
    }
