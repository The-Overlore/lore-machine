from __future__ import annotations

import json
import logging
from typing import TypedDict, cast

from .constants import ORDERS
from .types import RealmPosition

logger = logging.getLogger("overlore")


class RealmGeodata(TypedDict):
    xy: list[float]
    name: str


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
        with open(path) as file:
            geodata_file = json.load(file)
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
