import logging
from enum import Enum
from typing import Any

import requests

from overlore.graphql.constants import EventType

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

    PENDING_TRADES = """
    statusModels(where: {valueEQ: "0"}) {
            edges{
            node {
            value
            trade_id
            }
        }
    }
    """

    TRADE = """
    tradeModels(where: {trade_id: "{id}"}, last: 30) {
            edges {
        node {
            maker_resource_chest_id
            taker_resource_chest_id
        }
        }
    }
    """

    TRADE_CHEST = """
    resourcechestModels(where: {entity_id: "{id}"}) {
        edges {
            node {
                resources_count
                entity_id
                entity {
                    keys
                    eventId
                    models {
                        __typename
                    }
                }
            }
        }
    }
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

    ALL_REALMS = """
    realmModels {
        edges {
            node {
                realm_id,
                entity_id,
            }
        }
    }
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
        logger.error("KeyError accessing %s in JSON response: %s", e, json_response)
    if data is None:
        raise RuntimeError(f"Failed to run query {json_response['errors']}")
    return data
