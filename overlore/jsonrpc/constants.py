from overlore.config import BootConfig
from overlore.jsonrpc.methods.generate_town_hall.generate_town_hall import Context as GenerateTownHallContext
from overlore.jsonrpc.methods.generate_town_hall.generate_town_hall import generate_town_hall
from overlore.jsonrpc.methods.spawn_npc.spawn_npc import Context as SpawnNpcContext
from overlore.jsonrpc.methods.spawn_npc.spawn_npc import spawn_npc
from overlore.jsonrpc.types import JsonRpcMethod
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.llm.guard import AsyncGuard
from overlore.torii.client import ToriiClient
from overlore.types import DialogueThoughts, NpcProfile, Townhall


def setup_json_rpc_methods(config: BootConfig) -> list[JsonRpcMethod]:
    json_rpc_methods: list[JsonRpcMethod] = [
        JsonRpcMethod(
            context=GenerateTownHallContext(
                town_hall_guard=AsyncGuard(
                    output_type=Townhall,
                ),
                dialogue_thoughts_guard=AsyncGuard(output_type=DialogueThoughts),
                llm_client=AsyncOpenAiClient(),
                torii_client=ToriiClient(url=config.env["TORII_GRAPHQL"]),
                katana_client=KatanaClient(url=config.env["KATANA_URL"]),
            ),
            method=generate_town_hall,
        ),
        JsonRpcMethod(
            context=SpawnNpcContext(
                guard=AsyncGuard(output_type=NpcProfile),
                llm_client=AsyncOpenAiClient(),
                torii_client=ToriiClient(url=config.env["TORII_GRAPHQL"]),
                katana_client=KatanaClient(url=config.env["KATANA_URL"]),
                lore_machine_pk=config.env["LOREMACHINE_PRIVATE_KEY"],
            ),
            method=spawn_npc,
        ),
    ]

    return json_rpc_methods
