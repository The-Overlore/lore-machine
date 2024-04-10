from enum import Enum


class ErrorCodes(Enum):
    INVALID_REALM_ENTITY_ID = 1
    LACK_OF_NPCS = 2
    NPC_ENTITY_ID_NOT_FOUND = 3
    KATANA_UNAVAILABLE = 4
    TORII_UNAVAILABLE = 5
    LLM_VALIDATOR_ERROR = 6
    INVALID_TOWN_HALL_INPUT = 7
    NO_DATA_AVAILABLE = 8
