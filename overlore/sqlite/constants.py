from enum import Enum


class EventType(Enum):
    ORDER_ACCEPTED = 0
    COMBAT_OUTCOME = 1
    NPC_SPAWNED = 2


class Profile(Enum):
    "REALMID = 0, FULL_NAME = 1, AGE = 2, ROLE = 3,  SEX = 4, TRAIT = 5, DESCRIPTION = 6"

    REALMID = 0
    FULL_NAME = 1
    AGE = 2
    ROLE = 3
    SEX = 4
    TRAIT = 5
    DESCRIPTION = 6
