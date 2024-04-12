from enum import Enum


class EmbeddingsModel(Enum):
    TEXT_EMBEDDING_SMALL = "text-embedding-3-small"


class ChatCompletionModel(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo-0125"
    GPT_4_PREVIEW = "gpt-4-0125-preview"


GUARD_RAILS_HUB_URL = "https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com/v1/traces"

AGENT_TEMPLATE = """{name} is a {age} year old {sex} {role}. Realm of origin: {origin_realm}"""
