from typing import TypeAlias

RealmPosition: TypeAlias = tuple[float, float]

ResourceAmount: TypeAlias = dict[str, int]

ResourceAmounts: TypeAlias = list[ResourceAmount]

AttackingEntityIds: TypeAlias = list[int]

Npc: TypeAlias = dict[str, int | str | dict[str, int | str]]
