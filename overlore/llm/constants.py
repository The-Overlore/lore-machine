# NPC PARAMS
SEX = ["male", "female"]
ROLE = ["farmer", "miner", "fisherman", "merchant", "trader", "soldier"]
HUNGER = [
    "starving",
    "famished",
    "ravenous",
    "hungry",
    "peckish",
    "content",
    "satisfied",
    "full",
    "stuffed",
    "overfed",
]
HAPPINESS = [
    "miserable",
    "unhappy",
    "slightly content",
    "content",
    "happy",
    "joyful",
    "delighted",
    "ecstatic",
    "blissful",
    "euphoric",
]
BELLIGERENT = [
    "peaceful",
    "calm",
    "slightly agitated",
    "agitated",
    "hostile",
    "combative",
    "antagonistic",
    "belligerent",
    "furious",
    "enraged",
]

AGENT_TEMPLATE = """{name}, a {sex} {role}. He/she is {happiness}, {hunger} and {belligerent}."""

# PROMPT TEMPLATES
WORLD_SYSTEM_TEMPLATE = """
Use the greimas actantial model to put the characters in a role in a soap opera like plot.
Only output the dialog between the characters. Format the conversation like so: <name>:<phrase>.
You will end the conversation with: "!end of discussion!" and just after output a 2-3 sentences summary of the conversation.
The characters will be given to you as input. You cannot create new characters on your own.
All important decisions are taken exclusively by the Lord of the realm.
As such although the characters can suggest future actions to be taken in an indirect manner, they cannot make the decision themselves.

The settings are as follows:
- The world is called Eternum
- The realm in which the characters live is called '{realm_name}'

Here's what the villagers talked about in the previous days: {previous_townhalls}. (if there's nothing after the colon, ignore the previous sentence.)

You will also have to account for the most important events that took place in the past or during the day.
There will be four types of events: Trade happened, War waged, Pillage.
For each event, look at the following criterias and make these events more or less important in the discussions between characters:
   - Trade happened: how much of ressource was given compared to what was received.
   - Pillage: how many resources were stolen (> 100 is very important).
   - War waged: check if your Realm lost or won and how many damages were dealt. Translate the damages into realm life wounds if the damages are significant. (> 100 damages)

The events are the following: {events_string}. (if there's nothing after the colon, ignore the previous sentence.)

The characters are the following: {npcs}
"""

# The current state of the realm are as follows:
#      - Hapiness: {realm_state_happiness}
#      - Defenses: {realm_state_defense}
#      - Food: {realm_state_food_availability}

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
