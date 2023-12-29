from enum import Enum

COMPLETED_TRADE_EVENT = "0x27319ec70e0f69f3988d0a1a75dd2cc3715d4d7a60acec45b51fe577a5f2bf1"
TRANSFER_EVENT = "0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"


class Queries(Enum):
    PENDINGTRADES = """
    tradeModels(where: {taker_idEQ: "0"}) {
        edges {
        node {
            entity {
            id
            keys
            updatedAt
            }
        }
        }
    }"""

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


class Subscriptions(Enum):
    EVENT_EMITTED = """
          subscription {{
                eventEmitted(keys: ["{event_hash}", "*", "*", "*"]) {{
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
    COMPLETED_TRADE_EVENT_EMITTED = EVENT_EMITTED.format(event_hash=COMPLETED_TRADE_EVENT)
