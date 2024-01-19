from typing import TypeAlias

from overlore.eternum.types import RealmPosition

StoredEvent: TypeAlias = list[int | str | RealmPosition]

StoredVector: TypeAlias = tuple[int, float]

TownhallEventResponse: TypeAlias = tuple[int | str, bool]
