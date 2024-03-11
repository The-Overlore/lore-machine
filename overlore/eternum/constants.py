from __future__ import annotations

import logging
from enum import Enum
from typing import TypedDict, cast

from overlore.eternum.types import RealmPosition
from overlore.utils import open_json_file


class RealmGeodata(TypedDict):
    xy: list[float]
    name: str


logger = logging.getLogger("overlore")


ORDERS = [
    "power",
    "anger",
    "brilliance",
    "detection",
    "enlightenment",
    "fox",
    "fury",
    "giants",
    "perfection",
    "reflection",
    "skill",
    "titans",
    "twins",
    "vitriol",
    "rage",
    "protection",
]


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
    geodata: list[RealmGeodata]

    @classmethod
    def instance(cls) -> Realms:
        if cls._instance is None:
            logger.debug("Creating Realms constants class")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def load_geodata(self, path: str) -> list[RealmGeodata]:
        geodata_file = open_json_file(path)
        features: list[RealmGeodata] = geodata_file["features"]
        return features

    def init(self, path: str = "./data/realms_geodata.json") -> Realms:
        self.geodata = self.load_geodata(path)
        return self

    def order_by_order_id(self, i: int) -> str:
        return ORDERS[i - 1]

    def name_by_id(self, i: int) -> str:
        if i <= 0 or i > 8000 or self.geodata[i - 1].get("xy") is None:
            raise RuntimeError("Error with input or geodata")
        return str(self.geodata[i - 1]["name"])

    def position_by_id(self, i: int) -> RealmPosition:
        if i <= 0 or i > 8000 or self.geodata[i - 1].get("xy") is None:
            raise RuntimeError("Error with input or geodata")
        xy: list[float] = cast(list[float], self.geodata[i - 1]["xy"])
        ret: tuple[float, float] = (
            float(xy[0]),
            float(xy[1]),
        )
        return ret
