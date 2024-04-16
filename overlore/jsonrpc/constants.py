from overlore.config import BootConfig
from overlore.jsonrpc.methods.generate_discussion.entrypoint import Context as GenerateDiscussionContext
from overlore.jsonrpc.methods.generate_discussion.entrypoint import (
    generate_discussion,
)
from overlore.jsonrpc.methods.get_npc_backstory.entrypoint import Context as GetNpcBackstoryContext
from overlore.jsonrpc.methods.get_npc_backstory.entrypoint import (
    get_npc_backstory,
)
from overlore.jsonrpc.methods.spawn_npc.entrypoint import Context as SpawnNpcContext
from overlore.jsonrpc.methods.spawn_npc.entrypoint import spawn_npc
from overlore.jsonrpc.types import JsonRpcMethod
from overlore.katana.client import KatanaClient
from overlore.llm.client import AsyncOpenAiClient
from overlore.llm.guard import AsyncGuard
from overlore.torii.client import ToriiClient
from overlore.types import DialogueThoughts, Discussion, NpcProfile


def setup_json_rpc_methods(config: BootConfig) -> list[JsonRpcMethod]:
    json_rpc_methods: list[JsonRpcMethod] = [
        create_generate_discussion_method(config=config),
        create_spawn_npc_method(config=config),
        create_get_npc_backstory_method(),
    ]

    return json_rpc_methods


def create_generate_discussion_method(config: BootConfig) -> JsonRpcMethod:
    return JsonRpcMethod(
        context=GenerateDiscussionContext(
            discussion_guard=AsyncGuard(
                output_type=Discussion,
            ),
            dialogue_thoughts_guard=AsyncGuard(output_type=DialogueThoughts),
            llm_client=AsyncOpenAiClient(),
            torii_client=ToriiClient(url=config.env["TORII_GRAPHQL"]),
            katana_client=KatanaClient(url=config.env["KATANA_URL"]),
        ),
        method=generate_discussion,
    )


def create_spawn_npc_method(config: BootConfig) -> JsonRpcMethod:
    return JsonRpcMethod(
        context=SpawnNpcContext(
            guard=AsyncGuard(output_type=NpcProfile),
            llm_client=AsyncOpenAiClient(),
            torii_client=ToriiClient(url=config.env["TORII_GRAPHQL"]),
            katana_client=KatanaClient(url=config.env["KATANA_URL"]),
            lore_machine_pk=config.env["LOREMACHINE_PRIVATE_KEY"],
        ),
        method=spawn_npc,
    )


def create_get_npc_backstory_method() -> JsonRpcMethod:
    return JsonRpcMethod(context=GetNpcBackstoryContext(), method=get_npc_backstory)
