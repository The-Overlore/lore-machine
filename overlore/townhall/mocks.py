import logging
from typing import Any, cast

from overlore.eternum.types import Villager
from overlore.utils import open_json_file

logger = logging.getLogger("overlore")

MOCK_KATANA_RESPONSE = {
    "jsonrpc": "2.0",
    "result": {
        "status": "ACCEPTED_ON_L1",
        "block_hash": "0x38937c85771a65ee96dd2fcd37f28a159b7c9f553c17807fd30feae68506a67",
        "parent_hash": "0x0",
        "block_number": 0,
        "new_root": "0x0",
        "timestamp": 0,
        "sequencer_address": "0x1",
        "l1_gas_price": {"price_in_strk": "0x0", "price_in_wei": "0x174876e800"},
        "starknet_version": "0.12.2",
        "transactions": [],
    },
    "id": 1,
}


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
