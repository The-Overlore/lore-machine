import requests

from overlore.prompts.constants import AGENT_TEMPLATE, BELLIGERENT, HAPPINESS, HUNGER, ROLE, SEX, WORLD_SYSTEM_TEMPLATE


class GptInterface:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print("Generating GTP interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self, openai_api_key, openai_embeddings_api_key):
        raise RuntimeError("Call instance() instead")

    def init(self, openai_api_key, openai_embeddings_api_key):
        self.OPENAI_API_KEY = openai_api_key
        self.OPENAI_URL = "https://api.openai.com/v1/chat/completions"

        self.OPENAI_EMBEDDINGS_API_KEY = openai_embeddings_api_key
        self.OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"

        self.sex = SEX
        self.role = ROLE

    def __parse_events(self, events):
        return "".join(self.__parse_event(event) for event in events)

    def __parse_event(self, event):
        keys = event.get("keys")
        data = event.get("data")
        if "tradeCompleted" in keys:
            return (
                f"Trade completed: {int(data[1], base=16)} {data[0]} sent for"
                f" {int(data[3], base=16)} {data[2]} received."
            )
        if "warBegan" in keys:
            return f"War began: {int(data[0], base=16)} soldiers sent out."
        if "warWon" in keys:
            return (
                f"War won: {int(data[0], base=16)} soldiers were killed and {int(data[1], base=16)} gold was brought"
                " back."
            )
        if "warLost" in keys:
            return f"War lost: {int(data[0], base=16)} soldier were killed."

    async def generatePrompt(self, promptSystem, promptUser):
        requestOptions = {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            },
            "body": {
                # frequency_penalty seems interesting. Tried 0.6 and got pretty original dialogue
                "messages": [
                    {"role": "system", "content": promptSystem},
                    {"role": "user", "content": promptUser},
                ],
                "model": "gpt-4-1106-preview",  # 3.5 for cheaper testing ?
            },
        }

        try:
            response = requests.post(
                self.OPENAI_URL, json=requestOptions["body"], headers=requestOptions["headers"], timeout=1000
            )
        except Exception as error:
            print("Error:", error)
        else:
            return response.json()

    async def generateEmbedding(self, textInput):
        requestOptions = {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.OPENAI_EMBEDDINGS_API_KEY}",
            },
            "body": {
                "input": textInput,
                "model": "text-embedding-ada-002",
            },
        }

        try:
            response = requests.post(
                self.OPENAI_EMBEDDINGS_URL, json=requestOptions["body"], headers=requestOptions["headers"], timeout=1000
            )
        except Exception as error:
            print("Error:", error)
        else:
            return response.json()

    def generateTownHallDiscussion(self, npc_list, events):
        event_string = self.__parse_events(events)
        systemPrompt = WORLD_SYSTEM_TEMPLATE.format(
            # Use getters for this
            realm_name="Straejelas",
            realmState_happiness="Happy",
            realmState_defense="Vulnerable",
            events=event_string,
        )

        userPrompt = ""
        # Where do we get the npc_list from ?
        for npc in npc_list:
            mood = npc.get("mood")
            userPrompt += AGENT_TEMPLATE.format(
                name=npc["name"],
                sex=SEX[npc.get("sex")],
                role=ROLE[npc.get("role")],
                happiness=HAPPINESS[mood.get("happiness")],
                hunger=HUNGER[mood.get("hunger")],
                belligerent=BELLIGERENT[mood.get("belligerent")],
            )
            userPrompt += "\n"
        print(systemPrompt)
        print(userPrompt)
        return self.generatePrompt(systemPrompt, userPrompt)
