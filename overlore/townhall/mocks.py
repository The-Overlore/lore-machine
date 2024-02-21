import logging
import time
from typing import Any, cast

from overlore.eternum.types import Villager
from overlore.utils import open_json_file

logger = logging.getLogger("overlore")


def load_mock_villagers() -> list[Villager]:
    return cast(list[Villager], open_json_file("./data/villagers.json"))


def load_mock_events() -> Any:
    events = open_json_file("./data/events.json")
    # Use a list comprehension to extract eventEmitted details
    processed_events = [
        [event.get("data", {}).get("eventEmitted", {}) for event in event_group] for event_group in events
    ]

    return processed_events


def fetch_villagers() -> list[Villager]:
    return load_mock_villagers()
