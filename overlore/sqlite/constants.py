from enum import Enum


class EventType(Enum):
    ORDER_ACCEPTED = 0
    COMBAT_OUTCOME = 1


class Profile(Enum):
    "REALMID = 0,AGE = 1, NAME = 2, SEX = 3, TRAIT = 4, SUMMARY = 5"
    REALMID = 0
    NAME = 1
    SEX = 2
    TRAIT = 3
    SUMMARY = 4
