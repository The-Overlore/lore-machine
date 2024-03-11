from typing import Any, cast

from overlore.eternum.constants import Realms, ResourceIds, Winner
from overlore.eternum.types import ResourceAmounts
from overlore.llm.constants import (
    AGENT_TEMPLATE,
)
from overlore.sqlite.constants import EventType
from overlore.sqlite.types import StoredEvent
from overlore.types import Npc
from overlore.utils import get_enum_name_by_value, str_to_json


class LlmFormatter:
    def _resources_to_nl(self, resources: ResourceAmounts) -> str:
        resources_strings: list[str] = []
        for resource in resources:
            resource_str = str(resource["amount"])
            resource_str += " " + get_enum_name_by_value(ResourceIds, resource["resource_type"])
            resources_strings.append(resource_str)
        return ", ".join(resources_strings)

    def _combat_outcome_to_nl(self, event: StoredEvent) -> str:
        # type_dependent_data:
        #   for COMBAT_OUTCOME: {attacking_entity_ids: [id, ...], stolen_resources:  [{type: x, amount: y}, ...], winner: ATTACKER/TARGER, damage: x}
        nl = ""
        realms = Realms.instance()
        int(str(event[2]))
        active_realm_id = int(str(event[3]))
        int(str(event[4]))
        passive_realm_id = int(str(event[5]))
        active_realm_name = realms.name_by_id(active_realm_id)
        passive_realm_name = realms.name_by_id(passive_realm_id)

        type_dependent_data: dict[Any, Any] = str_to_json(str(event[8]))

        if type_dependent_data["damage"] == 0:
            nl += f"Pillage of realm {passive_realm_name} by realm {active_realm_name}. "
            stolen_resources = self._resources_to_nl(type_dependent_data["stolen_resources"])
            nl += f"Stolen resources are {stolen_resources}."
        else:
            nl += f"War waged: by {active_realm_name} against {passive_realm_name}. "
            winner = type_dependent_data["winner"]
            winner_name = active_realm_name if (winner == Winner.Attacker.value) else passive_realm_name
            loser_name = passive_realm_name if (winner == Winner.Attacker.value) else active_realm_name
            nl += f"Winner is {winner_name}. Loser is {loser_name}. "
            nl += f"Damages taken by {loser_name}: {type_dependent_data['damage']}. "
        return nl

    def _order_accepted_to_nl(self, event: StoredEvent) -> str:
        # TODO: https://github.com/The-Overlore/lore-machine/issues/26
        # type_dependent_data:
        #   for ORDER_ACCEPTED: {resources_maker: [{type: x, amount: y}, ...], resources_taker:  [{type: x, amount: y}, ...], }
        realms = Realms.instance()

        int(str(event[2]))
        active_realm_id = int(str(event[3]))
        int(str(event[4]))
        passive_realm_id = int(str(event[5]))
        active_realm_name = realms.name_by_id(active_realm_id)
        passive_realm_name = realms.name_by_id(passive_realm_id)

        type_dependent_data: dict[Any, Any] = str_to_json(str(event[8]))
        resources_taker = self._resources_to_nl(type_dependent_data["resources_taker"])
        resources_maker = self._resources_to_nl(type_dependent_data["resources_maker"])
        nl = f"Trade happened: between {active_realm_name} and {passive_realm_name} realms. "
        nl += f"{active_realm_name} will get {resources_taker}. "
        nl += f"{passive_realm_name} will get {resources_maker}. "
        return nl

    def _npc_to_nl(self, npc: Npc) -> str:
        characteristics = npc["characteristics"]  # type: ignore[index]

        age: int = cast(int, characteristics["age"])
        role: str = cast(str, characteristics["role"])
        sex: str = cast(str, characteristics["sex"])

        character_trait: str = cast(str, npc["character_trait"])  # type: ignore[index]
        name: str = cast(str, npc["full_name"])  # type: ignore[index]
        print(f"age {age} sex {sex} role {role} charac trait {character_trait}")
        return AGENT_TEMPLATE.format(name=name, sex=sex, role=role, character_trait=character_trait, age=age)

    def event_to_nl(self, event: StoredEvent) -> str:
        #  event
        #  0      1     2                       3                4                        5                 6           7   8                     9,0        9,1        10,0       10,1
        # [rowid, type, active_realm_entity_id, active_realm_id, passive_realm_entity_id, passive_realm_id, importance, ts, type_dependent_data, (X_active, Y_active), (X_passive, Y_passive)]
        event_type = event[1]
        if event_type == EventType.COMBAT_OUTCOME.value:
            return self._combat_outcome_to_nl(event=event)
        elif event_type == EventType.ORDER_ACCEPTED.value:
            return self._order_accepted_to_nl(event=event)
        else:
            raise RuntimeError("Unknown event type")

    def npcs_to_nl(self, villagers: list[Npc]) -> str:
        return "\n".join(self._npc_to_nl(npc) for npc in villagers)
