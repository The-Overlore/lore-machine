# mypy: disable-error-code="call-arg"
import warnings
from enum import Enum
from json.encoder import JSONEncoder
from typing import Any, Optional, TypedDict

warnings.simplefilter(action="ignore", category=FutureWarning)
from pydantic import BaseModel, Field  # noqa: E402

from overlore.constants import ROLES  # noqa: E402
from overlore.eternum.types import RealmPosition  # noqa: E402
from overlore.sqlite.constants import EventType  # noqa: E402

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
    type_specific_data: str


class Characteristics(BaseModel):
    age: int = Field(
        description="Age of the character, between 15 and 65",
    )
    role: int = Field(
        description=f"Job of the villager. {roles_str}",
    )
    sex: int = Field(
        description="Sex of the villager. (0 for male, 1 for female)",
    )


class Backstory(BaseModel):
    backstory: str = Field(
        description=(
            "Backstory of the villager. Gives information about his past and his personality. Make it 5 sentences long"
            " minimum."
        ),
    )
    poignancy: int = Field(
        description=(
            "On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely"
            " poignant (e.g., a break up, war), rate the likely poignancy of the backstory."
        )
    )


class NpcProfile(BaseModel):
    character_trait: str = Field(
        description="Trait of character that defines the villager. One word max.",
    )

    full_name: str = Field(
        description="Name of the villager. Don't use common words in the name such as Wood",
    )

    backstory: Backstory = Field(
        description="Backstory of the villager",
    )

    characteristics: Characteristics = Field(description="Various characteristics")


class DialogueSegment(BaseModel):
    full_name: str = Field(description="Full name of the villager speaking.")
    dialogue_segment: str = Field(description="The dialogue spoken by the villager.")


class Discussion(BaseModel):
    dialogue: list[DialogueSegment] = Field(description="""Discussion held by the NPCs. Do at least 10 exchanges.""")
    input_score: int = Field(description="Note of the lord's input.")


class Thought(BaseModel):
    thought: str = Field(description="""The thought""")
    poignancy: int = Field(description="""Poignancy of the thought.""")


class NpcAndThoughts(BaseModel):
    thoughts: list[Thought] = Field(description="""Thoughts and villager's name. Make two thoughts per villager""")
    full_name: str = Field(description="Full name of the villager")


class DialogueThoughts(BaseModel):
    npcs: list[NpcAndThoughts] = Field()


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


class ParsedSpawnEvent(TypedDict):
    torii_event_id: str
    event_type: EventType
    realm_entity_id: int
    npc_entity_id: int


class NpcEntity(TypedDict):
    character_trait: str
    full_name: str
    characteristics: Characteristics
    entity_id: int
    current_realm_entity_id: int
    origin_realm_id: int
