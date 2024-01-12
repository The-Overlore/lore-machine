from __future__ import annotations

from enum import Enum
from typing import Any

from overlore.eternum.types import RealmPosition
from overlore.utils import open_json_file


class ResourceIds(Enum):
    Wood = 1
    Stone = 2
    Coal = 3
    Copper = 4
    Obsidian = 5
    Silver = 6
    Ironwood = 7
    ColdIron = 8
    Gold = 9
    Hartwood = 10
    Diamonds = 11
    Sapphire = 12
    Ruby = 13
    DeepCrystal = 14
    Ignium = 15
    EtherealSilica = 16
    TrueIce = 17
    TwilightQuartz = 18
    AlchemicalSilver = 19
    Adamantine = 20
    Mithral = 21
    Dragonhide = 22
    Lords = 253
    Wheat = 254
    Fish = 255


class Winner(Enum):
    Attacker = 0
    Target = 1


class Realms:
    _instance = None
    geodata: list[dict[str, Any]]

    @classmethod
    def instance(cls) -> Realms:
        if cls._instance is None:
            print("Creating Realms constants class")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def load_geodata(self) -> Any:
        geodata_file = open_json_file("./data/realms_geodata.json")
        return geodata_file.get("features")

    def init(self) -> Realms:
        self.geodata = self.load_geodata()
        return self

    def position_by_id(self, i: int) -> RealmPosition:
        if i <= 0 or i > 8000 or self.geodata[i - 1].get("xy") is None:
            raise RuntimeError("Error with input or geodata")
        return tuple(self.geodata[i - 1]["xy"])
