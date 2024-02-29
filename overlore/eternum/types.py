from typing import TypeAlias, TypedDict

RealmPosition: TypeAlias = tuple[float, float]

ResourceAmount: TypeAlias = dict[str, int]

ResourceAmounts: TypeAlias = list[ResourceAmount]

AttackingEntityIds: TypeAlias = list[int]


class NpcCharacteristics(TypedDict):
    age: int
    role: int
    sex: int


class Npc(TypedDict):
    characteristics: NpcCharacteristics
    character_trait: str
    full_name: str
    # Not used ATM
    description: str
