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

AGENT_TEMPLATE = """{name}, a {sex} {role}. He/she is {happiness}, {hunger} and {belligerent}."""

# PROMPT TEMPLATES
WORLD_SYSTEM_TEMPLATE = """
     Use the greimas actantial model to put any of the characters in a role in a soap opera like plot. 
     Describe the configuration before the generated dialogue and have the dialogue play out the configuration.
     The characters will be given to you as input.
     You cannot create new characters on your own.
     Format the conversation like so: <name>:<phrase> and end it with the following phrase: "The town meeting is now over"
     Do note that all decisions are taken exclusively by the Lord of the realm. 
     As such although the characters can suggest future actions to be taken in an indirect manner, they cannot make the decision themselves.
     
     The settings are as follows:
     - The world is called Eternum
     - The realm in which the characters live is called '{realm_name}'
     - The realm's main priorities are as follows:
        * sustaining its population through wheat farming and fishing, or making trades to buy them from other realms.
        * collecting various ressources such as wood and various minerals. These ressources are to be used either invest buildings for the realm or to trade with other realms.
        * maintaining a robust military defense against potential threats from foreign realms
        * defending its relic from foreign realms
        * waging war with other realms to rob them of their ressources and relics
     
     The current state of the realm are as follows:
     - Hapiness: {realm_state_happiness}
     - Defenses: {realm_state_defense}
     - Food: {realm_state_food_availability}
     - Relic: {realm_state_relic_presence}

     You will also have to account for the events that took place in the past or during the day. 
     There will be four types of events: Trade completed, War began, War won, War lost. 
     For each event, look at the following criterias and make these events more or less important in the discussions between characters:
        - Trade completed: how much of ressource was given compared to what was received. 
        - War began: how many soldiers were sent to war (> 100 is very important). 
        - War won: soldier losses and how much gold was brought back. 
        - Lost war: casualties (> 100 is important)

     The events are the following: {events}
     
     The characters are the following: {characters}
    """

# WIP
#   -> During the speech, {name} maintains a demeanor that is {happiness}, {hunger} and {belligerent}. ## Prompt reuses specified states
#   -> Discusses the significance of recent events: {events}. ## Should be modeled around their role
AGENT_CREATION_TEMPLATE = """
    {name}, a {sex} {role}, has just arrived in {realm_name} to settle.
    Upon entering the realm, {name} addresses the lord with the following matters: 

    1. Expresses gratitude for the warm welcome and hospitality extended by the realm.
    2. Highlights the skills and contributions he/she brings as a {role}.
    3. Explain his background and where he comes from.
    4. Discusses the significance of recent events: {events}.

    During the speech, {name} maintains a demeanor that is {happiness}, {hunger} and {belligerent}.

    Format the speech like so: <name>:<speech>.
"""
