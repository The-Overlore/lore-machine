from typing import Any, cast

from overlore.eternum.constants import Realms, ResourceIds, Winner
from overlore.eternum.types import ResourceAmounts, Villager
from overlore.llm.constants import (
    AGENT_TEMPLATE,
    ROLE,
    SEX,
)
from overlore.sqlite.constants import EventType
from overlore.sqlite.types import StoredEvent
from overlore.utils import get_enum_name_by_value, str_to_json


class NaturalLanguageFormatter:
    def _resources_to_nl(self, resources: ResourceAmounts) -> str:
        resources_strings: list[str] = []
        for resource in resources:
            resource_str = str(resource["amount"])
            resource_str += " " + get_enum_name_by_value(ResourceIds, resource["type"])
            resources_strings.append(resource_str)
        return ", ".join(resources_strings)

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
            winner_name = active_realm_name if (winner == Winner.Attacker.value) else passive_realm_name
            loser_name = passive_realm_name if (winner == Winner.Attacker.value) else active_realm_name
            nl += f"Winner is {winner_name}. Loser is {loser_name}. "
            nl += f"Damages taken by {loser_name}: {metadata['damage']}. "
        return nl

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
        return nl

    def _npc_to_nl(self, npc: Villager) -> str:
        sex: int = cast(int, npc["sex"])
        role: int = cast(int, npc["role"])
        return AGENT_TEMPLATE.format(
            name=npc["name"],
            sex=SEX[sex],
            role=ROLE[role],
        )

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

    def npcs_to_nl(self, villagers: list[Villager]) -> str:
        return "\n".join(self._npc_to_nl(npc) for npc in villagers)

    def events_to_nl(self, events: list[StoredEvent]) -> str:
        return "\n".join(self._event_to_nl(event) for event in events)
