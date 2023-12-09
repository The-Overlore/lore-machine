# NPC PARAMS
SEX = {0: "male", 1: "female"}
ROLE = {0: "farmer", 1: "miner", 2: "fisherman", 3: "merchant", 4: "trader", 5: "soldier"}
HUNGER = {
    0: "starving",
    1: "famished",
    2: "ravenous",
    3: "hungry",
    4: "peckish",
    5: "content",
    6: "satisfied",
    7: "full",
    8: "stuffed",
    9: "overfed",
}
HAPPINESS = {
    0: "miserable",
    1: "unhappy",
    2: "slightly content",
    3: "content",
    4: "happy",
    5: "joyful",
    6: "delighted",
    7: "ecstatic",
    8: "blissful",
    9: "euphoric",
}
BELLIGERENT = {
    0: "peaceful",
    1: "calm",
    2: "slightly agitated",
    3: "agitated",
    4: "hostile",
    5: "combative",
    6: "antagonistic",
    7: "belligerent",
    8: "furious",
    9: "enraged",
}

# PROMPT TEMPLATES, ! UNTESTED !
WORLD_SYSTEM_TEMPLATE = """You will have to create a discussion between the characters that will be given to you as input. Format the conversation like so: <name>:<phrase>
     The settings are as follows:
     - The world is called Eternum
     - The realm in which the characters live is called {realm_name}
     - The realm's main priorities are as follows:
     * sustaining its population through wheat, farming and fishing
     * collecting various ressources such as wood and various minerals
     * maintaining a robust military defense against potential threats from foreign realms
     The current state of the realm are as follows:
     - {realmState_happiness}
     - {realmState_defense}
     You will also have to account for the events that took place during the day. There will be four types of events: Trade completed, War began, War won, War lost. For each event, look at the following criterias and make these events more or less important in the discussions between characters. Trade completed: how much of ressource was given compared to what was received. War began: how many soldiers were sent to war (> 100 is very important). War won: soldier losses and how much gold was brought back. Lost war: casualties (> 100 is important)
     The events are the following: {events}
     """

AGENT_TEMPLATE = """{name}, a {sex} {role}. He/she is currently {happiness}, {hunger} and {belligerent}."""
