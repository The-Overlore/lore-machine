import json
import logging
from typing import cast

from websockets import WebSocketServerProtocol

from overlore.config import BootConfig
from overlore.npcs.spawn import spawn_npc
from overlore.townhall.logic import handle_townhall_request
from overlore.types import EnumEncoder, MsgType, WsErrorResponse, WsResponse, WsSpawnNpcResponse, WsTownhallResponse
from overlore.utils import get_ws_msg_type, str_to_json

logger = logging.getLogger("overlore")


async def handle_client_connection(websocket: WebSocketServerProtocol, config: BootConfig) -> None:
    async for message in websocket:
        response: WsResponse | None = None
        if message is None:
            continue
        try:
            msg = str_to_json(cast(str, message))
        except Exception as error:
            response = {
                "msg_type": MsgType.ERROR,
                "data": cast(
                    WsErrorResponse,
                    {
                        "reason": f"Failure to generate a dialog: {error}",
                    },
                ),
            }

        ws_msg_type = get_ws_msg_type(msg)
        data = msg["data"]
        if ws_msg_type == MsgType.TOWNHALL.value:
            logger.debug("generating townhall")
            (townhall_id, townhal, _, _) = await handle_townhall_request(data, config)
            response = {
                "msg_type": MsgType.TOWNHALL,
                "data": cast(WsTownhallResponse, {"townhall_id": townhall_id, "townhall": townhal}),
            }
        elif ws_msg_type == MsgType.SPAWN_NPC.value:
            logger.debug("spawning NPC")
            (npc, signature) = await spawn_npc(data, config)
            response = {
                "msg_type": MsgType.SPAWN_NPC,
                "data": cast(WsSpawnNpcResponse, {"npc": npc, "signature": signature}),
            }

        logger.debug(response)
        await websocket.send(json.dumps(response, cls=EnumEncoder))
