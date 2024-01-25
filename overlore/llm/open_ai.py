from __future__ import annotations

from typing import Any, cast

from openai import OpenAI

from overlore.eternum.constants import Realms, ResourceIds, Winner
from overlore.eternum.types import ResourceAmounts, Villager
from overlore.llm.constants import (
    AGENT_TEMPLATE,
    BELLIGERENT,
    EVENTS_EXTENSION,
    HAPPINESS,
    HUNGER,
    PREVIOUS_TOWNHALL_EXTENSION,
    ROLE,
    SEX,
    WORLD_SYSTEM_TEMPLATE,
)
from overlore.sqlite.constants import EventType
from overlore.sqlite.types import StoredEvent
from overlore.utils import get_enum_name_by_value, str_to_json


class OpenAIHandler:
    _instance: OpenAIHandler | None = None
    API_KEY: str | None = None
    TEXT_GEN_URL: str = "https://api.openai.com/v1/chat/completions"
    EMBEDDINGS_URL: str = "https://api.openai.com/v1/embeddings"
    client: OpenAI

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls) -> OpenAIHandler:
        if cls._instance is None:
            print("Generating OpenAIHandler interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def init(self, open_ai_api_key: str) -> None:
        self.API_KEY = open_ai_api_key
        self.client = OpenAI(api_key=open_ai_api_key)

    def _npc_to_nl(self, npc: Villager) -> str:
        sex: int = cast(int, npc["sex"])
        role: int = cast(int, npc["role"])
        mood: dict[str, int] = cast(dict[str, int], npc["mood"])
        happiness = mood["happiness"]
        hunger = mood["hunger"]
        belligerent = mood["belligerent"]
        return AGENT_TEMPLATE.format(
            name=npc["name"],
            sex=SEX[sex],
            role=ROLE[role],
            happiness=HAPPINESS[happiness],
            hunger=HUNGER[hunger],
            belligerent=BELLIGERENT[belligerent],
        )

    def _resources_to_nl(self, resources: ResourceAmounts) -> str:
        resources_strings: list[str] = []
        for resource in resources:
            resource_str = str(resource["amount"])
            resource_str += " " + get_enum_name_by_value(ResourceIds, resource["type"])
            resources_strings.append(resource_str)
        return ", ".join(resources_strings)

    def _order_accepted_to_nl(self, event: StoredEvent) -> str:
        # TODO: https://github.com/The-Overlore/lore-machine/issues/26
        # metadata:
        #   for ORDER_ACCEPTED: {resources_maker: [{type: x, amount: y}, ...], resources_taker:  [{type: x, amount: y}, ...], }
        realms = Realms.instance()
        active_realm_entity_id = int(str(event[2]))
        passive_realm_entity_id = int(str(event[3]))
        active_realm_name = realms.name_by_id(active_realm_entity_id)
        passive_realm_name = realms.name_by_id(passive_realm_entity_id)
        metadata: dict[Any, Any] = str_to_json(str(event[6]))
        resources_taker = self._resources_to_nl(metadata["resources_taker"])
        resources_maker = self._resources_to_nl(metadata["resources_maker"])
        nl = f"Trade happened: between {active_realm_name} and {passive_realm_name} realms. "
        nl += f"{active_realm_name} will get {resources_taker}. "
        nl += f"{passive_realm_name} will get {resources_maker}. "
        nl += "\n"
        return nl

    def _combat_outcome_to_nl(self, event: StoredEvent) -> str:
        # metadata:
        #   for COMBAT_OUTCOME: {attacking_entity_ids: [id, ...], stolen_resources:  [{type: x, amount: y}, ...], winner: ATTACKER/TARGER, damage: x}
        nl = ""
        realms = Realms.instance()
        active_realm_entity_id = int(str(event[2]))
        passive_realm_entity_id = int(str(event[3]))
        active_realm_name = realms.name_by_id(active_realm_entity_id)
        passive_realm_name = realms.name_by_id(passive_realm_entity_id)

        metadata: dict[Any, Any] = str_to_json(str(event[6]))
        if metadata["damage"] == 0:
            nl += f"Pillage of realm {passive_realm_name} by realm {active_realm_name}. "
            stolen_resources = self._resources_to_nl(metadata["stolen_resources"])
            nl += f"Stolen resources are {stolen_resources}."
        else:
            nl += f"War waged: by {active_realm_name} against {passive_realm_name}. "
            winner = metadata["winner"]
            winner = active_realm_name if winner == Winner.Attacker.value else passive_realm_name
            loser = passive_realm_name if winner == Winner.Attacker.value else active_realm_name
            nl += f"Winner is {winner}. Loser is {loser}. "
            nl += f"Damages taken by loser: {metadata['damage']}. "
        nl += "\n"
        return nl

    def npcs_to_nl(self, villagers: list[Villager]) -> str:
        return "\n".join(self._npc_to_nl(npc) for npc in villagers)

    def _events_to_nl(self, events: list[StoredEvent]) -> str:
        return "\n".join(self._event_to_nl(event) for event in events)

    def _event_to_nl(self, event: StoredEvent) -> str:
        #  event
        #  0      1     2                       3                        4           5   6         70         1          80          1
        # [rowid, type, active_realm_entity_id, passive_realm_entity_id, importance, ts, metadata, (X_active, Y_active), (X_passive, Y_passive)]
        event_type = event[1]
        if event_type == EventType.COMBAT_OUTCOME.value:
            return self._combat_outcome_to_nl(event=event)
        elif event_type == EventType.ORDER_ACCEPTED.value:
            return self._order_accepted_to_nl(event=event)
        else:
            raise RuntimeError("Unknown event type")

    async def request_prompt(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if response is None:
            raise RuntimeError("GPT interface could not request a townhall")
        return str(response.choices[0].message.content)

    async def request_embedding(self, str_input: str) -> list[float]:
        response = self.client.embeddings.create(
            model="text-embedding-ada-002", input=str_input, encoding_format="float"
        )
        return response.data[0].embedding

    async def generate_townhall_discussion(
        self,
        realms: Realms,
        realm_id: int,
        townhall_summaries: list[str],
        npc_list: list[Villager],
        events: list[StoredEvent],
    ) -> str:
        realms = Realms.instance()

        realm_name = realms.name_by_id(realm_id)

        npcs = self.npcs_to_nl(npc_list)

        systemPrompt = WORLD_SYSTEM_TEMPLATE.format(
            realm_name=realm_name, npcs=npcs, previous_townhalls=townhall_summaries
        )

        events_string = self._events_to_nl(events)
        if len(events_string) != 0:
            systemPrompt += EVENTS_EXTENSION.format(events_string=events_string)

        townhalls_string = "\n".join(list(townhall_summaries))
        if len(townhalls_string) != 0:
            systemPrompt += PREVIOUS_TOWNHALL_EXTENSION.format(townhall_summaries=townhalls_string)

        userPrompt = ""

        return await self.request_prompt(systemPrompt, userPrompt)
