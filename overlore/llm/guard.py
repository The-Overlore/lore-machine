import json
from typing import Any, Awaitable, Callable, Generic, Type, TypeVar

from pydantic import BaseModel
from rich import print

# Define a type variable that can be any subclass of BaseModel
T = TypeVar("T", bound=BaseModel)


class AsyncGuard(Generic[T]):
    def __init__(self, output_type: Type[T]):
        self.output_type: Type[T] = output_type

    async def call_llm_with_guard(
        self,
        api_function: Callable[[str, str, Any, Any], Awaitable[str]],
        instructions: str,
        prompt: str,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        instructions += (
            "\n Here's the JSON schema you should follow. Use that format for your output. It's very important that you"
            " follow it."
            + json.dumps(self.output_type.model_json_schema())
        )

        print(instructions)
        print(prompt)
        data = await api_function(
            *args,
            **kwargs,
            prompt=prompt,  # type: ignore[call-arg]
            instructions=instructions,
            response_format={"type": "json_object"},
        )
        validated_output: T = self.output_type.model_validate_json(data)
        print(validated_output.model_dump())

        return validated_output
