from __future__ import annotations

from typing import TypedDict

from openai import BaseModel

from overlore.jsonrpc.methods.get_npcs_backstory.types import BackstoryWithEntityId
from overlore.sqlite.npc_db import NpcDatabase


class Context(TypedDict):
    pass


class MethodParams(BaseModel):
    npc_entity_ids: list[int]


class SuccessResponse(TypedDict):
    backstories_with_entity_ids: list[BackstoryWithEntityId]


class NpcBackstoryGetter:
    context: Context
    params: MethodParams

    @classmethod
    def create(cls, context: Context, params: MethodParams) -> NpcBackstoryGetter:
        self = cls.__new__(cls)

        self.context = context
        self.params = params

        return self

    def __init__(self) -> None:
        raise RuntimeError("Call create() instead")

    def create_response(self) -> SuccessResponse:
        npc_db = NpcDatabase.instance()

        query_ret = npc_db.fetch_npcs_backstories(self.params.npc_entity_ids)

        backstories_with_entity_ids = [
            BackstoryWithEntityId(npc_entity_id=item[0], backstory=item[1]) for item in query_ret
        ]

        return SuccessResponse(backstories_with_entity_ids=backstories_with_entity_ids)
