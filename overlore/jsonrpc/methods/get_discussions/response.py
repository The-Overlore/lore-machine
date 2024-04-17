from __future__ import annotations

import logging
from typing import TypedDict

from openai import BaseModel

from overlore.sqlite.discussion_db import DiscussionDatabase
from overlore.sqlite.types import StorableDiscussion

logger = logging.getLogger("overlore")

I64_MAX = 2**63 - 1


class Context(TypedDict):
    pass


class MethodParams(BaseModel):
    start_time: int
    end_time: int | None = None
    realm_id: int


class SuccessResponse(TypedDict):
    discussions: list[StorableDiscussion]
    realm_id: int


class DiscussionGetter:
    discussion_db: DiscussionDatabase
    context: Context
    params: MethodParams

    @classmethod
    def create(cls, context: Context, params: MethodParams) -> DiscussionGetter:
        self = cls.__new__(cls)

        self.context = context
        self.params = params
        self.discussion_db = DiscussionDatabase.instance()

        return self

    def __init__(self) -> None:
        raise RuntimeError("Call create() instead")

    def create_response(self) -> SuccessResponse:
        discussions = self.get_discussions()
        return self.create_success_response(db_discussions=discussions)

    def get_discussions(self) -> list[StorableDiscussion]:
        start_time = self.params.start_time
        end_time = self.params.end_time if self.params.end_time else I64_MAX

        db_discussions = self.discussion_db.fetch_discussions_by_realm_id_and_ts(
            realm_id=self.params.realm_id, start_time=start_time, end_time=end_time
        )
        return db_discussions

    def create_success_response(self, db_discussions: list[StorableDiscussion]) -> SuccessResponse:
        return SuccessResponse(discussions=db_discussions, realm_id=self.params.realm_id)
