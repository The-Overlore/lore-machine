import json
import logging
from typing import Any, Callable

import responses
import respx

from overlore.config import BootConfig
from overlore.llm.constants import GUARD_RAILS_HUB_URL

logger = logging.getLogger("overlore")

MOCK_VILLAGERS = [
    {
        "entityId": "0x371b96bc40f0a933f41da3af6999dfe1c8079fb1004c874f6e1022efb6af567",
        "realmEntityId": 92,
        "characteristics": {"age": 25, "role": 1, "sex": 0},
        "character_trait": "Smartass",
        "full_name": "John Travolta",
    },
    {
        "entityId": "0x44e494923bc21faf42778b2432683cf8206cd331826e89e45298de0df854f52",
        "realmEntityId": 92,
        "characteristics": {"age": 45, "role": 0, "sex": 1},
        "character_trait": "Helpful",
        "full_name": "Emma Watson",
    },
    {
        "entityId": "0x493619825a69dfc0fca6523f2714ded59c434c62d2d480d64439b96d9767006",
        "realmEntityId": 92,
        "characteristics": {"age": 60, "role": 1, "sex": 0},
        "character_trait": "egotistical",
        "full_name": "Fred Freddy",
    },
    {
        "entityId": "0xcbcd5931acd6625981947fd91d9ea41dfbee0211518b8954cddbffdad30f11",
        "realmEntityId": 92,
        "characteristics": {"age": 15, "role": 0, "sex": 0},
        "character_trait": "neurotic",
        "full_name": "Sally Lauw",
    },
    {
        "entityId": "0xDEADBAAF",
        "realmEntityId": 92,
        "characteristics": {"age": 28, "role": 1, "sex": 1},
        "character_trait": "friendly",
        "full_name": "Matilda Marron",
    },
]

MOCK_KATANA_RESPONSE = {
    "jsonrpc": "2.0",
    "result": {
        "status": "ACCEPTED_ON_L1",
        "block_hash": "0x38937c85771a65ee96dd2fcd37f28a159b7c9f553c17807fd30feae68506a67",
        "parent_hash": "0x0",
        "block_number": 0,
        "new_root": "0x0",
        "timestamp": 0,
        "sequencer_address": "0x1",
        "l1_gas_price": {"price_in_strk": "0x0", "price_in_wei": "0x174876e800"},
        "starknet_version": "0.12.2",
        "transactions": [],
    },
    "id": 1,
}

MOCK_EMBEDDINGS_RESPONSE = {
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "index": 0,
            "embedding": [-0.006929283495992422, -0.005336422007530928, -4.547132266452536e-05, -0.024047505110502243],
        }
    ],
    "model": "text-embedding-3-small",
    "usage": {"prompt_tokens": 5, "total_tokens": 5},
}

MOCK_COMPLETION_RESPONSE = {
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": """```json
                    {
                    "dialogue": [
                        {
                        "full_name": "Walter Dominguez",
                        "dialogue_segment": "Can't believe those Nisku folks didn't see the dragon coming. Should've been prepared for anything in war!"
                        },
                        {
                        "full_name": "Walter Dominguez",
                        "dialogue_segment": "And now, there's talk of a water nymph? We need to tread carefully, could be an ally or another curse."
                        },
                        {
                        "full_name": "Octavius Cassius",
                        "dialogue_segment": "The victory was hard-earned. But this news of a water nymph has me worried. What if she's mightier than the dragon?"
                        },
                        {
                        "full_name": "Octavius Cassius",
                        "dialogue_segment": "I suggest we send a diplomatic party to Merrow Creek, see if the nymph has any intentions towards lel Kúbklor."
                        },
                        {
                        "full_name": "Charlotte Blacksmith",
                        "dialogue_segment": "Our courage won the war, but now, we must show wisdom. That nymph could hold key alliances or fatal threats."
                        },
                        {
                        "full_name": "Charlotte Blacksmith",
                        "dialogue_segment": "Let's not forget, the magic that controls a dragon could sway a nymph. We must be cautious and respectful."
                        },
                        {
                        "full_name": "Lucas Mason",
                        "dialogue_segment": "War's over but the peace feels uneasy. With all this talk of mythical creatures, what's next for us miners?"
                        },
                        {
                        "full_name": "Lucas Mason",
                        "dialogue_segment": "Imagine, working in the mines one day and running into a water nymph the next. This realm's becoming unpredictable."
                        },
                        {
                        "full_name": "Alistair Warren",
                        "dialogue_segment": "The war may have brought us victory, but the talk of this nymph stirs the pot. My nets have felt lighter since she was spotted."
                        },
                        {
                        "full_name": "Alistair Warren",
                        "dialogue_segment": "Perhaps, we can strike a deal with the nymph. Might turn the tides of fortune for lel Kúbklor if she's on our side."
                        }
                    ],
                    "summary": "The NPCs of lel Kúbklor discuss the recent victory over Nisku and the emergence of a water nymph near Merrow Creek. Walter expresses shock at Nisku's lack of preparation and caution towards the nymph. Octavius reflects on the victory and proposes diplomacy wit
                    the nymph. Charlotte emphasizes the need for wisdom in dealing with the nymph, aware of the potential dangers and benefits. Lucas highlights the unpredictability the nymph brings to his daily life as a miner. Alistair sees an opportunity in the nymph's appearance, suggestin
                    that an alliance could benefit their realm.",
                    "plot_twist": "Alistair secretly knows the water nymph, hinting at a potential undisclosed alliance or past encounter."
                    }
                    ```""",
                "role": "assistant",
            },
            "logprobs": None,
        }
    ],
    "created": 1677664795,
    "id": "chatcmpl-7QyqpwdfhqwajicIEznoc6Q47XAyW",
    "model": "gpt-3.5-turbo-0613",
    "object": "chat.completion",
    "usage": {"completion_tokens": 17, "prompt_tokens": 57, "total_tokens": 74},
}


@respx.mock
async def with_mock_responses(func: Callable, config: BootConfig, *args: Any) -> None:
    try:
        with responses.RequestsMock() as rsps:
            open_ai_completion_url = "https://api.openai.com/v1/chat/completions"
            open_ai_embeddings_url = "https://api.openai.com/v1/embeddings"
            respx.post(open_ai_completion_url).respond(content=json.dumps(MOCK_COMPLETION_RESPONSE))
            respx.post(open_ai_embeddings_url).respond(content=json.dumps(MOCK_EMBEDDINGS_RESPONSE))

            rsps.add(rsps.POST, config.env["KATANA_URL"], body=json.dumps(MOCK_KATANA_RESPONSE), status=200)
            rsps.add_passthru(GUARD_RAILS_HUB_URL)
            await func(*args)
    except AssertionError:
        # if we don't do all requests to the added urls, responses lib throws an error
        pass
