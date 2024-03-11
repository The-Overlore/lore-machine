import json
import logging
from typing import cast

from websockets import WebSocketServerProtocol

from overlore.config import BootConfig
from overlore.npcs.spawn import spawn_npc
from overlore.townhall.request import handle_townhall_request
from overlore.types import EnumEncoder, MsgType, WsErrorResponse, WsResponse, WsSpawnNpcResponse
from overlore.utils import get_ws_msg_type, str_to_json

logger = logging.getLogger("overlore")


async def handle_client_connection(websocket: WebSocketServerProtocol, config: BootConfig) -> None:
    async for message in websocket:
        response: WsResponse | None = None
        if message is None:
            continue
        try:
            msg = str_to_json(cast(str, message))
            ws_msg_type = get_ws_msg_type(msg)
            data = msg["data"]
            if ws_msg_type == MsgType.TOWNHALL.value:
                logger.debug("generating townhall")
                response = WsResponse(
                    msg_type=MsgType.TOWNHALL,
                    data=handle_townhall_request(data, config),
                )
            elif ws_msg_type == MsgType.SPAWN_NPC.value:
                logger.debug("spawning NPC")
                (npc, signature) = spawn_npc(data, config)
                response = {
                    "msg_type": MsgType.SPAWN_NPC,
                    "data": cast(WsSpawnNpcResponse, {"npc": npc, "signature": signature}),
                }

        except Exception as error:
            response = {
                "msg_type": MsgType.ERROR,
                "data": cast(
                    WsErrorResponse,
                    {
                        "reason": f"Failure to generate ws response: {error}",
                    },
                ),
            }

        await websocket.send(json.dumps(response, cls=EnumEncoder))
