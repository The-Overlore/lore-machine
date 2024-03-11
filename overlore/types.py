# mypy: disable-error-code="call-arg"
from enum import Enum
from json.encoder import JSONEncoder
from typing import Any, Optional, TypedDict

from guardrails.validators import TwoWords, ValidChoices, ValidLength, ValidRange
from pydantic import BaseModel, Field
from starknet_py.hash.utils import ECSignature

from overlore.eternum.types import RealmPosition
from overlore.npcs.constants import ROLES

roles_str = ", ".join([f"{index} for {role}" for index, role in enumerate(ROLES)])


EventKeys = list[str]
EventData = list[str]


class ToriiDataNode(TypedDict):
    keys: EventKeys
    data: EventData
    createdAt: str
    transactionHash: Optional[str]


class ToriiEmittedEvent(TypedDict):
    eventEmitted: ToriiDataNode


class ParsedEvent(TypedDict):
    torii_event_id: str
    event_type: int
    active_realm_entity_id: int
    active_realm_id: int
    passive_realm_entity_id: int
    importance: float
    ts: int
    passive_realm_id: int
    active_pos: RealmPosition
    passive_pos: RealmPosition
    type_dependent_data: str


class Characteristics(BaseModel):
    age: int = Field(description="Age of the character", validators=ValidRange(min=15, max=65))
    role: int = Field(
        description=f"Job of the NPC. {roles_str}",
        validators=[ValidChoices(choices=[index for index, role in enumerate(ROLES)], on_fail="reask")],
    )
    sex: int = Field(
        description="Sex of the NPC. (0 for male, 1 for female)",
        validators=[ValidChoices(choices=[0, 1], on_fail="reask")],
    )


class Npc(BaseModel):
    character_trait: str = Field(
        description="Trait of character that defines the NPC. One word max.",
        validators=[
            ValidLength(min=5, max=31, on_fail="fix"),
        ],
    )

    full_name: str = Field(
        description='First name and last name of the NPC. Don\'t use words in the name such as "Wood"',
        validators=[ValidLength(min=5, max=31), TwoWords(on_fail="reask")],
    )

    description: str = Field(
        description="Description of the NPC",
    )
    characteristics: Characteristics = Field(description="Various characteristics")


class DialogueSegment(BaseModel):
    full_name: str = Field(description="Full name of the NPC saying the sentence.")
    dialogue_segment: str = Field(description="What the NPC says")


class Townhall(BaseModel):
    dialogue: list[DialogueSegment] = Field(
        description="Discussion that was held by the NPCs. Make each NPC speak twice"
    )
    summary: str = Field(
        description="A summary of the dialogue, outlining each NPC's contributions and reactions to the event"
    )
    plot_twist: str = Field(
        description="The plot twist that you introduced in the dialogue. Only output one sentence for the plot twist."
    )


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
    dialogue: list[DialogueSegment]


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
