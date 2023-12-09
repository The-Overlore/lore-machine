# NPC PARAMS
SEX = { 0: "male", 1: "female" }
ROLE = { 0: "farmer", 1: "miner", 2: "fisherman", 3: "merchant", 4: "trader", 5: "soldier" }
# HUNGER = { 0: "starving", 1: "famished", 2: "ravenous", 3: "hungry", 4: "peckish", 5: "content", 6: "satisfied", 7: "full", 8: "stuffed", 9: "overfed" }
# HAPPINESS = { 0: "miserable", 1: "unhappy", 2: "slightly Content", 3: "content", 4: "happy", 5: "joyful", 6: "delighted", 7: "ecstatic", 8: "blissful", 9: "euphoric" }
# BELLIGERENT = { 0: "peaceful", 1: "calm", 2: "agitated", 3: "irritable", 4: "hostile", 5: "combative", 6: "antagonistic", 7: "belligerent", 8: "furious", 9: "enraged" }

# PROMPT TEMPLATES, ! UNTESTED !
WORLD_SYSTEM_TEMPLATE = "You will have to create a discussion between the characters that will be given to you as input. \
    The settings are as follows: \
    - The world is called Eternum \
    - The realm in which the characters live is called {realm_name} \
    - The realm's main priorities are as follows: \
        * sustaining its population through wheat farming and fishing \
        * collecting various ressources such as wood and various minerals \
        * maintaining a robust military defense against potential threats from foreign realms \
    The current state of the realm are as follows: \
    - {realmState_happiness} \
    - {realmState_defense} \
"

AGENT_TEMPLATE = "{name}, a {sex} {role}. \
"
#He/she is currently {happiness_state}, {hunger_state} and {belligerent_state}. "