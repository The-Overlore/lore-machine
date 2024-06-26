from enum import Enum
from typing import TypeAlias, TypedDict

RealmPosition: TypeAlias = tuple[float, float]


AttackingEntityIds: TypeAlias = list[int]


class ResourceAmount(TypedDict):
    resource_type: int
    amount: int


ResourceAmounts: TypeAlias = list[ResourceAmount]


class Winner(Enum):
    Attacker = 0
    Target = 1
