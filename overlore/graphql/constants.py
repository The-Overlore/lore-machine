from enum import Enum


class EventType(Enum):
    ORDER_ACCEPTED = "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945"
    TRANSFER = "0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"
    COMBAT_OUTCOME = "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918"
    NPC_SPAWNED = "0x24334a7bb6ddb29a34bf9e534498505917deb1101efad4807ae7b2dda50f6b6"


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


class Subscriptions(Enum):
    KEY_BASED_SUB_TEMPLATE = """
          subscription {{
                eventEmitted(keys: ["{event_hash}"]) {{
                    id
                    keys
                    data
                    createdAt
                }}
            }}
        """
    ANY_EVENT_EMITTED = """
          subscription {
                eventEmitted {
                    id
                    keys
                    data
                    createdAt
                }
            }
        """
    ORDER_ACCEPTED = KEY_BASED_SUB_TEMPLATE.format(event_hash=EventType.ORDER_ACCEPTED.value)
    COMBAT_OUTCOME = KEY_BASED_SUB_TEMPLATE.format(event_hash=EventType.COMBAT_OUTCOME.value)
    NPC_SPAWNED = KEY_BASED_SUB_TEMPLATE.format(event_hash=EventType.NPC_SPAWNED.value)
