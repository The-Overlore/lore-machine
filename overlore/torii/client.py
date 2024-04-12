import json
import logging
from typing import Any, cast

import aiohttp
from starknet_py.cairo.felt import decode_shortstring

from overlore.errors import ErrorCodes
from overlore.sqlite.events_db import EventsDatabase
from overlore.torii.parsing import parse_event
from overlore.torii.query import Queries
from overlore.types import NpcEntity, ToriiDataNode
from overlore.utils import unpack_characteristics

logger = logging.getLogger("overlore")


class ToriiClient:
    def __init__(self, url: str) -> None:
        self.events_db = EventsDatabase.instance()
        self.url = url

    async def boot_sync(self) -> None:
        self.store_synced_events(
            events=await self.get_synced_events(query=Queries.ORDER_ACCEPTED_EVENT_QUERY.value),
        )
        self.store_synced_events(
            events=await self.get_synced_events(query=Queries.COMBAT_OUTCOME_EVENT_QUERY.value),
        )

    def store_synced_events(self, events: list[ToriiDataNode]) -> None:
        for event in events:
            parsed_event = parse_event(event=event)
            self.events_db.insert_event(event=parsed_event)

    async def get_synced_events(self, query: str) -> list[ToriiDataNode]:
        query_results = await self.run_torii_query(query=query)
        events = [query_result["node"] for query_result in query_results["events"]["edges"]]
        return events

    async def get_npcs_by_realm_entity_id(self, realm_entity_id: int) -> list[NpcEntity]:
        query_results = await self.run_torii_query(
            query=Queries.NPC_BY_CURRENT_REALM_ENTITY_ID.value.format(realm_entity_id=realm_entity_id),
        )
        npcs = [
            cast(
                NpcEntity,
                {
                    "character_trait": decode_shortstring(int(query_result["node"]["character_trait"], base=16)),
                    "full_name": decode_shortstring(int(query_result["node"]["full_name"], base=16)),
                    "characteristics": unpack_characteristics(int(query_result["node"]["characteristics"], base=16)),
                    "entity_id": int(query_result["node"]["entity_id"], base=16),
                    "current_realm_entity_id": int(query_result["node"]["current_realm_entity_id"], base=16),
                    "origin_realm_id": await self.get_realm_id_from_npc_entity_id(
                        int(query_result["node"]["entity_id"], base=16),
                    ),
                },
            )
            for query_result in query_results["npcModels"]["edges"]
        ]
        return npcs

    async def get_realm_id_from_npc_entity_id(self, npc_entity_id: int) -> int:
        query_result = await self.run_torii_query(
            query=Queries.REALM_ENTITY_ID_BY_NPC_ENTITY_ID.value.format(
                npc_entity_id=npc_entity_id,
            ),
        )

        query_result = await self.run_torii_query(
            query=Queries.REALM_ID_BY_REALM_ENTITY_ID.value.format(
                realm_entity_id=int(query_result["entityownerModels"]["edges"][0]["node"]["entity_owner_id"], base=16),
            ),
        )

        return int(query_result["realmModels"]["edges"][0]["node"]["realm_id"], base=16)

    async def get_realm_owner_wallet_address(self, realm_entity_id: int) -> str:
        data = await self.run_torii_query(Queries.OWNER.value.format(entity_id=realm_entity_id))

        if len(data["ownerModels"]["edges"]) == 0:
            raise RuntimeError(ErrorCodes.INVALID_REALM_ENTITY_ID)

        realm_owner_address = data["ownerModels"]["edges"][0]["node"]["address"]

        return cast(str, realm_owner_address)

    async def run_torii_query(self, query: str) -> Any:
        try:
            headers = {"Content-Type": "application/json"}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=self.url, headers=headers, data=json.dumps({"query": query}), timeout=1000
                ) as response:
                    json_response = cast(dict[str, Any], await response.json())
            data = json_response["data"]
            if data is None:
                raise RuntimeError(ErrorCodes.NO_DATA_AVAILABLE)
        except KeyError as e:
            logger.exception("KeyError accessing %s in JSON response: %s", e, response)
        except aiohttp.ClientConnectorError as err:
            raise RuntimeError(ErrorCodes.TORII_UNAVAILABLE) from err
        else:
            return data
