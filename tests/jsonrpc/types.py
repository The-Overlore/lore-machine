from overlore.llm.client import LlmClient


class MockLlmClient(LlmClient):
    def __init__(self):
        self.number_of_tries = 0

    def request_embedding(self, _: str) -> list[float]:
        return [0.0, 0.1, 0.2]

    def request_prompt_completion(self, _: str) -> str:
        if self.number_of_tries == 0:
            return """
                    {
                        "dialogue": [
                            {
                            "full_name": "Johny Bravo",
                            "dialogue_segment": "HooHaa"
                            },
                            {
                            "full_name": "Julien Doré",
                            "dialogue_segment": "Blabla"
                            }
                        ],
                        "thoughts": [
                            {
                            "full_name": "Johny Bravo",
                            "value": "HooHaa"
                            },
                            {
                            "full_name": "Julien Doré",
                            "value": "Thought about blabla"
                            }
                        ],
                        "plotline": "Intriguing"
                    }
                """
