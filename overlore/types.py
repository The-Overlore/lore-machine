from enum import Enum
from typing import TypeAlias

from overlore.eternum.types import AttackingEntityIds, Npc, RealmPosition, ResourceAmounts

EventKeys: TypeAlias = list[str]

EventData: TypeAlias = EventKeys

ToriiRealm: TypeAlias = dict[str, int]

ToriiEvent: TypeAlias = dict[str, str | EventKeys | EventData]

ToriiEmittedEvent: TypeAlias = dict[str, ToriiEvent]

SyncEvents: TypeAlias = dict[str, dict[str, str | EventKeys | EventData]]

ParsedEvent: TypeAlias = dict[str, str | int | RealmPosition | ResourceAmounts | AttackingEntityIds | float]

TownhallRequestMsgData: TypeAlias = dict[str, int | str | list[Npc]]

NpcSpawnMsgData: TypeAlias = dict[str, int]

WsData: TypeAlias = TownhallRequestMsgData | NpcSpawnMsgData


class MsgType(Enum):
    TOWNHALL = 0
    SPAWN_NPC = 1
    ERROR = 255
