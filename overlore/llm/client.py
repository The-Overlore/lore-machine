from abc import ABC, abstractmethod
from typing import Any, cast

import openai

from overlore.errors import ErrorCodes


class LlmClient(ABC):
    """Interface used to define how an LLM client should behave"""

    @abstractmethod
    async def request_embedding(self, input_str: str, *args: Any, **kwargs: Any) -> list[float]:
        """Request an embedding of the input string"""
        pass

    @abstractmethod
    async def request_prompt_completion(self, input_str: str, instructions: str, *args: Any, **kwargs: Any) -> str:
        """Request the completion of an input to a LLM"""
        pass


class AsyncOpenAiClient(LlmClient):
    client: openai.AsyncOpenAI

    def __init__(self) -> None:
        self.client = openai.AsyncClient()

    async def request_embedding(self, input_str: str, *args: Any, **kwargs: Any) -> list[float]:
        response = await self.client.embeddings.create(input=input_str, **kwargs)
        return response.data[0].embedding

    async def request_prompt_completion(self, input_str: str, *args: Any, **kwargs: Any) -> str:
        if "instructions" not in kwargs:
            raise RuntimeError(ErrorCodes.LLM_VALIDATOR_ERROR)
        instructions = kwargs["instructions"]
        del kwargs["instructions"]
        response = await self.client.chat.completions.create(
            *args,
            messages=[
                {
                    "role": "user",
                    "content": input_str,
                },
                {"role": "system", "content": instructions},
            ],
            **kwargs,
        )
        msg = cast(str, response.choices[0].message.content)
        return msg
