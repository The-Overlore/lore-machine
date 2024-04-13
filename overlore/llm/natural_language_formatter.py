import json
from typing import Any, cast

from overlore.constants import ROLES, SEX
from overlore.eternum.realms import Realms
from overlore.eternum.types import ResourceAmounts, Winner
from overlore.llm.constants import (
    AGENT_TEMPLATE,
)
from overlore.sqlite.constants import EventType
from overlore.sqlite.types import StoredEvent
from overlore.types import NpcEntity
from overlore.utils import get_resource_name_by_id


class LlmFormatter:
    def _resources_to_nl(self, resources: ResourceAmounts) -> str:
        resources_strings: list[str] = []
        for resource in resources:
            resource_str = str(resource["amount"])
            resource_str += " " + get_resource_name_by_id(resource["resource_type"])
            resources_strings.append(resource_str)
        return ", ".join(resources_strings)

    def _combat_outcome_to_nl(self, event: StoredEvent) -> str:
        # type_specific_data:
        #   for COMBAT_OUTCOME: {attacking_entity_ids: [id, ...], stolen_resources:  [{type: x, amount: y}, ...], winner: ATTACKER/TARGER, damage: x}
        nl = ""
        realms = Realms.instance()
        int(str(event[2]))
        active_realm_id = int(str(event[3]))
        int(str(event[4]))
        passive_realm_id = int(str(event[5]))
        active_realm_name = realms.name_by_id(active_realm_id)
        passive_realm_name = realms.name_by_id(passive_realm_id)

        type_specific_data: dict[Any, Any] = json.loads(str(event[8]))

        if type_specific_data["damage"] == 0:
            nl += f"Pillage of realm {passive_realm_name} by realm {active_realm_name}. "
            stolen_resources = self._resources_to_nl(type_specific_data["stolen_resources"])
            nl += f"Stolen resources are {stolen_resources}."
        else:
            nl += f"{active_realm_name} went to war against {passive_realm_name}. "
            winner = type_specific_data["winner"]
            winner_name = active_realm_name if (winner == Winner.Attacker.value) else passive_realm_name
            loser_name = passive_realm_name if (winner == Winner.Attacker.value) else active_realm_name
            nl += f"The winner was {winner_name} while {loser_name} lost the war. "
            if type_specific_data["damage"] < 100:
                nl += "It was a small battle. "
            elif type_specific_data["damage"] < 200:
                nl += "The battle was quite bloody. "
            else:
                nl += "The battle was a bloodshed. "
        return nl

    def _order_accepted_to_nl(self, event: StoredEvent) -> str:
        # TODO: https://github.com/The-Overlore/lore-machine/issues/26
        # type_specific_data:
        #   for ORDER_ACCEPTED: {resources_maker: [{type: x, amount: y}, ...], resources_taker:  [{type: x, amount: y}, ...], }
        realms = Realms.instance()

        int(str(event[2]))
        active_realm_id = int(str(event[3]))
        int(str(event[4]))
        passive_realm_id = int(str(event[5]))
        active_realm_name = realms.name_by_id(active_realm_id)
        passive_realm_name = realms.name_by_id(passive_realm_id)

        type_specific_data: dict[Any, Any] = json.loads(str(event[8]))
        resources_taker = self._resources_to_nl(type_specific_data["resources_taker"])
        resources_maker = self._resources_to_nl(type_specific_data["resources_maker"])
        nl = f"Trade happened: between the realms of {active_realm_name} and {passive_realm_name}. "
        nl += f"{active_realm_name} will get {resources_taker}. "
        nl += f"{passive_realm_name} will get {resources_maker}. "

        return nl

    def _npc_to_nl(self, npc: NpcEntity) -> str:
        realms = Realms.instance()

        characteristics = npc["characteristics"]

        age: int = cast(int, characteristics["age"])  # type: ignore[index]
        role: str = cast(str, ROLES[characteristics["role"]])  # type: ignore[index]
        sex: str = cast(str, SEX[characteristics["sex"]])  # type: ignore[index]

        name: str = cast(str, npc["full_name"])

        origin_realm: str = realms.name_by_id(npc["origin_realm_id"])

        return AGENT_TEMPLATE.format(name=name, sex=sex, role=role, age=age, origin_realm=origin_realm)

    def event_to_nl(self, event: StoredEvent) -> str:
        #  event
        #  0      1     2                       3                4                        5                 6           7   8                     9,0        9,1        10,0       10,1
        # [rowid, type, active_realm_entity_id, active_realm_id, passive_realm_entity_id, passive_realm_id, importance, ts, type_specific_data, (X_active, Y_active), (X_passive, Y_passive)]
        event_type = event[1]
        if event_type == EventType.COMBAT_OUTCOME.value:
            return self._combat_outcome_to_nl(event=event)
        elif event_type == EventType.ORDER_ACCEPTED.value:
            return self._order_accepted_to_nl(event=event)
        else:
            raise RuntimeError("Unknown event type")

    def npcs_to_nl(self, villagers: list[NpcEntity]) -> str:
        return "\n".join(self._npc_to_nl(npc) for npc in villagers)
