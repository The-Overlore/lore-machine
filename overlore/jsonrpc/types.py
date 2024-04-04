from typing import Any, Callable, TypedDict

from jsonrpcserver import Result


class JsonRpcMethod(TypedDict):
    method: Callable[[Any, Any], Result]
    context: Any
