import logging
from enum import Enum
from typing import Any, cast

import requests
from starknet_py.cairo.felt import decode_shortstring

from overlore.graphql.constants import EventType
from overlore.types import Npc
from overlore.utils import unpack_characteristics

logger = logging.getLogger("overlore")


class Queries(Enum):
    EVENTS = """
    query events {{
        events(keys:["{event_hash}"]) {{
            edges {{
                node {{
                    id
                    keys
                    data
                    createdAt
                    transactionHash
                }}
            }}
        }}
    }}
    """

    OWNER = """
    query owners {{
            ownerModels (where: {{entity_id: "{entity_id}"}}){{
            edges {{
                node {{
                    address
                }}
            }}
        }}
    }}
    """

    NPC_BY_CURRENT_REALM_ENTITY_ID = """
    query {{
        npcModels (where: {{current_realm_entity_id: "{realm_entity_id}"}}){{
            edges {{
                node {{
                    entity_id
                    character_trait
                    full_name
                    current_realm_entity_id
                    characteristics
                }}
            }}
        }}
    }}
    """

    ORDER_ACCEPTED_EVENT_QUERY = EVENTS.format(event_hash=EventType.ORDER_ACCEPTED.value)
    COMBAT_OUTCOME_EVENT_QUERY = EVENTS.format(event_hash=EventType.COMBAT_OUTCOME.value)


def run_torii_query(torii_endpoint: str, query: str) -> Any:
    data = None
    try:
        response = requests.post(torii_endpoint, json={"query": query}, timeout=5)
        json_response = response.json()
        data = json_response["data"]
    except KeyError as e:
        logger.exception("KeyError accessing %s in JSON response: %s", e, json_response)
    if data is None:
        raise RuntimeError(f"Failed to run query {json_response['errors']}")
    return data


def get_npcs_by_realm_entity_id(torii_endpoint: str, realm_entity_id: int) -> list[Npc]:
    query_results = run_torii_query(
        torii_endpoint=torii_endpoint,
        query=Queries.NPC_BY_CURRENT_REALM_ENTITY_ID.value.format(realm_entity_id=realm_entity_id),
    )
    npcs = [
        cast(
            Npc,
            {
                "character_trait": decode_shortstring(int(query_result["node"]["character_trait"], base=16)),
                "full_name": decode_shortstring(int(query_result["node"]["full_name"], base=16)),
                "description": "",
                "characteristics": unpack_characteristics(int(query_result["node"]["characteristics"], base=16)),
            },
        )
        for query_result in query_results["npcModels"]["edges"]
    ]
    return npcs
