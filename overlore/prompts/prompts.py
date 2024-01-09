from __future__ import annotations

from typing import Any

import requests

from overlore.prompts.constants import AGENT_TEMPLATE, BELLIGERENT, HAPPINESS, HUNGER, ROLE, SEX, WORLD_SYSTEM_TEMPLATE


class GptInterface:
    _instance = None

    @classmethod
    def instance(cls) -> GptInterface:
        if cls._instance is None:
            print("Generating GTP interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def init(self, openai_api_key: str, openai_embeddings_api_key: str) -> None:
        self.OPENAI_API_KEY = openai_api_key
        self.OPENAI_URL = "https://api.openai.com/v1/chat/completions"

        self.OPENAI_EMBEDDINGS_API_KEY = openai_embeddings_api_key
        self.OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"

        self.sex = SEX
        self.role = ROLE

    def __events_to_natural_language(self, events: list[dict[str, Any]]) -> str:
        return "".join(self.__event_to_natural_language(event) for event in events)

    def __event_to_natural_language(self, event: dict[str, Any]) -> str:
        keys = event.get("keys")
        data = event.get("data")

        if keys is None or data is None:
            raise RuntimeError("Couldn't convert event to natural language")

        if "tradeCompleted" in keys:
            return (
                f"Trade completed: {int(data[1], base=16)} {data[0]} sent for"
                f" {int(data[3], base=16)} {data[2]} received."
            )
        elif "warBegan" in keys:
            return f"War began: {int(data[0], base=16)} soldiers sent out."
        elif "warWon" in keys:
            return (
                f"War won: {int(data[0], base=16)} soldiers were killed and {int(data[1], base=16)} gold was brought"
                " back."
            )
        # WarLost
        else:
            return f"War lost: {int(data[0], base=16)} soldier were killed."

    async def generatePrompt(self, promptSystem: str, promptUser: str) -> Any:
        requestOptions = {
            "method": "POST",
            "body": {
                # frequency_penalty seems interesting. Tried 0.6 and got pretty original dialogue
                "messages": [
                    {"role": "system", "content": promptSystem},
                    {"role": "user", "content": promptUser},
                ],
                "model": "gpt-4-1106-preview",  # 3.5 for cheaper testing ?
            },
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
        }
        try:
            response = requests.post(self.OPENAI_URL, json=requestOptions["body"], headers=headers, timeout=1000)
        except Exception as error:
            print("Error:", error)
        else:
            return response.json()

    async def generateEmbedding(self, textInput: str) -> Any:
        requestOptions = {
            "method": "POST",
            "body": {
                "input": textInput,
                "model": "text-embedding-ada-002",
            },
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.OPENAI_EMBEDDINGS_API_KEY}",
        }

        try:
            response = requests.post(
                self.OPENAI_EMBEDDINGS_URL, json=requestOptions["body"], headers=headers, timeout=1000
            )
        except Exception as error:
            print("Error:", error)
        else:
            return response.json()

    def generateTownHallDiscussion(self, npc_list: list[Any], events: list[dict[str, Any]]) -> Any:
        event_string = self.__events_to_natural_language(events)
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
        return self.generatePrompt(systemPrompt, userPrompt)
