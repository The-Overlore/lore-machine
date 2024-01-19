from __future__ import annotations

from typing import Any

from openai import OpenAI

from overlore.llm.constants import AGENT_TEMPLATE, BELLIGERENT, HAPPINESS, HUNGER, ROLE, SEX, WORLD_SYSTEM_TEMPLATE


class OpenAIHandler:
    _instance: OpenAIHandler | None = None
    API_KEY: str | None = None
    TEXT_GEN_URL: str = "https://api.openai.com/v1/chat/completions"
    EMBEDDINGS_URL: str = "https://api.openai.com/v1/embeddings"

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls) -> OpenAIHandler:
        if cls._instance is None:
            print("Generating OpenAIHandler interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def init(self, openAI_api_key: str) -> None:
        self.API_KEY = openAI_api_key
        self.client = OpenAI(api_key=openAI_api_key)

    def _npc_to_natural_language(self, npc: Any) -> str:
        return AGENT_TEMPLATE.format(
            name=npc["name"],
            sex=SEX[npc.get("sex")],
            role=ROLE[npc.get("role")],
            happiness=HAPPINESS[npc["mood"].get("happiness")],
            hunger=HUNGER[npc["mood"].get("hunger")],
            belligerent=BELLIGERENT[npc["mood"].get("belligerent")],
        )

    def _villagers_to_natural_language(self, villagers: list[Any]) -> str:
        return "".join(self._npc_to_natural_language(npc) for npc in villagers)

    def __events_to_natural_language(self, events: list[dict[str, Any]]) -> str:
        return "".join(self.__event_to_natural_language(event) for event in events)

    def __event_to_natural_language(self, event: dict[str, Any]) -> str:
        keys = event.get("keys")
        data = event.get("data")

        if keys is None or data is None:
            raise RuntimeError("Event didn't have any keys or data")

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

    async def request_text_gen(self, system: str, user: str) -> Any:
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    async def request_embedding(self, str_input: str) -> Any:
        response = self.client.embeddings.create(
            model="text-embedding-ada-002", input=str_input, encoding_format="float"
        )
        return response.data[0].embedding

    def generate_townhall_discussion(self, villagers: list[Any], events: Any) -> Any:
        system = WORLD_SYSTEM_TEMPLATE.format(
            realm_name="Bimbamboum",
            events=self.__events_to_natural_language(events),
            characters=self._villagers_to_natural_language(villagers),
        )
        user = ""
        return self.request_text_gen(system, user)
