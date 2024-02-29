from enum import Enum
from json.encoder import JSONEncoder
from typing import Any, TypedDict

from starknet_py.hash.utils import ECSignature

from overlore.eternum.types import AttackingEntityIds, Npc, RealmPosition, ResourceAmounts

EventKeys = list[str]

EventData = EventKeys

ToriiRealm = dict[str, int]

ToriiEvent = dict[str, str | EventKeys | EventData]

ToriiEmittedEvent = dict[str, ToriiEvent]

SyncEvents = dict[str, dict[str, str | EventKeys | EventData]]

ParsedEvent = dict[str, str | int | RealmPosition | ResourceAmounts | AttackingEntityIds | float]


class MsgType(Enum):
    TOWNHALL = 0
    SPAWN_NPC = 1
    ERROR = 255


class TownhallRequestMsgData(TypedDict):
    realm_id: str
    order_id: int
    npcs: list[Npc]


class NpcSpawnMsgData(TypedDict):
    realm_entity_id: int


class WsIncomingMsg(TypedDict):
    msg_type: MsgType
    data: NpcSpawnMsgData | TownhallRequestMsgData


class WsErrorResponse(TypedDict):
    reason: str


class WsSpawnNpcResponse(TypedDict):
    npc: Npc
    signature: ECSignature


class WsTownhallResponse(TypedDict):
    townhall_id: int
    townhall: str


class WsResponse(TypedDict):
    msg_type: MsgType
    data: WsSpawnNpcResponse | WsErrorResponse | WsTownhallResponse


# Custom JSON Encoder that handles Enum types
class EnumEncoder(JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value  # Return the value of the Enum member
        return JSONEncoder.default(self, obj)  # Fallback for other types


class EnvVariables(TypedDict):
    OPENAI_API_KEY: str
    TORII_GRAPHQL: str
    TORII_WS: str
    KATANA_URL: str
    HOST_ADDRESS: str
    HOST_PORT: str
    LOREMACHINE_PUBLIC_KEY: str
    LOREMACHINE_PRIVATE_KEY: str
