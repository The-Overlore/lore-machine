import pytest
from guardrails import Guard

from overlore.config import BootConfig
from overlore.jsonrpc.methods.generate_town_hall.generate_town_hall import TownHallBuilder
from overlore.types import Townhall
from tests.jsonrpc.types import MockLlmClient


@pytest.mark.asyncio
async def test_generate_townhall_successfully():
    MockLlmClient()
    Guard.from_pydantic(output_class=Townhall, num_reasks=0)
    BootConfig()
    TownHallBuilder()
