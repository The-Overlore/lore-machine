import pytest

from overlore.jsonrpc.methods.get_npcs_backstory.response import (
    Context,
    MethodParams,
    NpcBackstoryGetter,
    SuccessResponse,
)
from overlore.jsonrpc.methods.get_npcs_backstory.types import BackstoryWithEntityId
from overlore.sqlite.npc_db import NpcDatabase
from overlore.types import Backstory, Characteristics, NpcProfile


@pytest.mark.asyncio
async def test_get_valid_response(context: Context):
    params = MethodParams(npc_entity_ids=[NPC_VALID_ENTITY_ID])
    discussion_builder = NpcBackstoryGetter.create(context=context, params=params)
    response = discussion_builder.create_response()

    assert VALID_RESPONSE == response


@pytest.mark.asyncio
async def test_get_non_existent_npc_backstory(context: Context):
    params = MethodParams(npc_entity_ids=[NON_EXISTENT_ENTITY_ID])
    discussion_builder = NpcBackstoryGetter.create(context=context, params=params)
    response = discussion_builder.create_response()

    assert SuccessResponse(backstories_with_entity_ids=[]) == response


@pytest.mark.asyncio
async def test_get_valid_response_multiple_entity_ids(context: Context):
    params = MethodParams(npc_entity_ids=[NPC_VALID_ENTITY_ID, ANOTHER_NPC_VALID_ENTITY_ID])
    discussion_builder = NpcBackstoryGetter.create(context=context, params=params)
    response = discussion_builder.create_response()

    assert ANOTHER_VALID_RESPONSE == response


@pytest.fixture
def context():
    npc_db = NpcDatabase.instance().init(":memory:")

    npc_db.insert_npc_profile(
        realm_entity_id=1,
        npc=NpcProfile(
            character_trait="nice",
            full_name="James Brown",
            backstory=Backstory(backstory=VALID_BACKSTORY, poignancy=10),
            characteristics=Characteristics(age=27, role=3, sex=1),
        ),
    )
    npc_db.insert_npc_backstory(npc_entity_id=NPC_VALID_ENTITY_ID, realm_entity_id=1)

    npc_db.insert_npc_profile(
        realm_entity_id=2,
        npc=NpcProfile(
            character_trait="nice",
            full_name="Red",
            backstory=Backstory(backstory=ANOTHER_VALID_BACKSTORY, poignancy=10),
            characteristics=Characteristics(age=27, role=3, sex=1),
        ),
    )
    npc_db.insert_npc_backstory(npc_entity_id=ANOTHER_NPC_VALID_ENTITY_ID, realm_entity_id=2)

    context = Context()

    yield context
    npc_db.close_conn()


# TEST DATA
VALID_BACKSTORY = "A good backstory"
NPC_VALID_ENTITY_ID = 1
VALID_RESPONSE = SuccessResponse(
    backstories_with_entity_ids=[BackstoryWithEntityId(backstory=VALID_BACKSTORY, npc_entity_id=NPC_VALID_ENTITY_ID)]
)

ANOTHER_VALID_BACKSTORY = "Hahah so hilarious"
ANOTHER_NPC_VALID_ENTITY_ID = 2
ANOTHER_VALID_RESPONSE = SuccessResponse(
    backstories_with_entity_ids=[
        BackstoryWithEntityId(backstory=VALID_BACKSTORY, npc_entity_id=NPC_VALID_ENTITY_ID),
        BackstoryWithEntityId(backstory=ANOTHER_VALID_BACKSTORY, npc_entity_id=ANOTHER_NPC_VALID_ENTITY_ID),
    ]
)

NON_EXISTENT_ENTITY_ID = 9999
