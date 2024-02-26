import logging
from typing import Any

from overlore.utils import open_json_file

logger = logging.getLogger("overlore")

MOCK_VILLAGERS = [
    {
        "entityId": "0x371b96bc40f0a933f41da3af6999dfe1c8079fb1004c874f6e1022efb6af567",
        "realmEntityId": 92,
        "characteristics": {"age": 25, "role": 1, "sex": 0},
        "characterTrait": "Smartass",
        "name": "John",
    },
    {
        "entityId": "0x44e494923bc21faf42778b2432683cf8206cd331826e89e45298de0df854f52",
        "realmEntityId": 92,
        "characteristics": {"age": 45, "role": 0, "sex": 1},
        "characterTrait": "Helpful",
        "name": "Emma",
    },
    {
        "entityId": "0x493619825a69dfc0fca6523f2714ded59c434c62d2d480d64439b96d9767006",
        "realmEntityId": 92,
        "characteristics": {"age": 60, "role": 1, "sex": 0},
        "characterTrait": "egotistical",
        "name": "Fred",
    },
    {
        "entityId": "0xcbcd5931acd6625981947fd91d9ea41dfbee0211518b8954cddbffdad30f11",
        "realmEntityId": 92,
        "characteristics": {"age": 15, "role": 0, "sex": 0},
        "characterTrait": "neurotic",
        "name": "Sally",
    },
    {
        "entityId": "0xDEADBAAF",
        "realmEntityId": 92,
        "characteristics": {"age": 28, "role": 1, "sex": 1},
        "characterTrait": "friendly",
        "name": "Matilda",
    },
]

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


def load_mock_events() -> Any:
    events = open_json_file("./data/events.json")
    # Use a list comprehension to extract eventEmitted details
    processed_events = [
        [event.get("data", {}).get("eventEmitted", {}) for event in event_group] for event_group in events
    ]

    return processed_events
