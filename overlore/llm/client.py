import openai


class LlmClient:
    """Interface used to define how an LLM client should behave"""

    def request_embedding(self, _input: str) -> list[float]:
        """Request an embedding of the input string"""
        pass

    def request_prompt_completion(_input: str) -> str:
        """Request the completion of an input to a LLM"""
        print("ewwewewe")
        pass


class AsyncOpenAiClient:
    client: openai.AsyncOpenAI

    def __init__(self):
        self.client = openai.AsyncClient()

    async def request_prompt_completion(self, input_str: str, instructions: str, *args, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            *args,
            **kwargs,
            messages=[
                {
                    "role": "user",
                    "content": input_str,
                },
                {"role": "system", "content": instructions},
            ],
        )
        msg = response.choices[0].message.content
        return msg

    async def request_embedding(self, input_str, **kwargs) -> list[float]:
        response = await self.client.embeddings.create(input=input_str, **kwargs)
        return response.data[0].embedding
