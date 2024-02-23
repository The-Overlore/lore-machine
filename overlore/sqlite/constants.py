from enum import Enum


class EventType(Enum):
    ORDER_ACCEPTED = 0
    COMBAT_OUTCOME = 1


class Profile(Enum):
    "REALMID = 0,AGE = 1, NAME = 2, SEX = 3, ROLE = 4, TRAIT = 5, SUMMARY = 6"
    REALMID = 0
    NAME = 1
    SEX = 2
    ROLE = 3
    TRAIT = 4
    SUMMARY = 5
