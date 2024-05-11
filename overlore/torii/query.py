import logging
from enum import Enum

from overlore.torii.constants import EventType

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

    REALM_ENTITY_ID_BY_NPC_ENTITY_ID = """
        query {{
            entityOwnerModels (where: {{entity_id: "{npc_entity_id}"}}) {{
                    edges {{
                        node {{
                            entity_owner_id
                        }}
                }}
            }}
        }}
    """

    REALM_ID_BY_REALM_ENTITY_ID = """
        query {{
            realmModels (where: {{entity_id: "{realm_entity_id}"}}) {{
                edges {{
                    node {{
                        realm_id
                    }}
                }}
            }}
        }}
    """

    ORDER_ACCEPTED_EVENT_QUERY = EVENTS.format(event_hash=EventType.ORDER_ACCEPTED.value)
    COMBAT_OUTCOME_EVENT_QUERY = EVENTS.format(event_hash=EventType.COMBAT_OUTCOME.value)
