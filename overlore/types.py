from typing import TypeAlias

from overlore.eternum.types import AttackingEntityIds, RealmPosition, ResourceAmounts

EventKeys: TypeAlias = list[str]
EventData: TypeAlias = list[str]
ToriiEvent: TypeAlias = dict[str, dict[str, str | EventKeys | EventData]]
ParsedEvent: TypeAlias = dict[str, int | RealmPosition | ResourceAmounts | AttackingEntityIds | float]


RealmData: TypeAlias = dict[str, str | int | list[int]]
TownhallData: TypeAlias = dict[str, str | RealmData]
