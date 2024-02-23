from typing import TypeAlias

from overlore.eternum.types import AttackingEntityIds, RealmPosition, ResourceAmounts

EventKeys: TypeAlias = list[str]

EventData: TypeAlias = EventKeys

ToriiRealm: TypeAlias = dict[str, int]

ToriiEvent: TypeAlias = dict[str, str | EventKeys | EventData]

ToriiEmittedEvent: TypeAlias = dict[str, ToriiEvent]

SyncEvents: TypeAlias = dict[str, dict[str, str | EventKeys | EventData]]

ParsedEvent: TypeAlias = dict[str, str | int | RealmPosition | ResourceAmounts | AttackingEntityIds | float]

RealmData: TypeAlias = dict[str, str | int | list[int]]

TownhallData: TypeAlias = dict[str, str | RealmData]
