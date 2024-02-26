from overlore.config import BootConfig
from overlore.llm.open_ai import OpenAIHandler
from overlore.spawn.mocks import MOCK_PROFILE
from overlore.sqlite.npc_spawn_db import NpcSpawnDatabase
from overlore.sqlite.types import StoredNpcProfile
from overlore.utils import str_to_json


def extract_npc_profile(prompt: str) -> dict[str, str]:
    extracted_data = {}
    keys = ["Name", "Surname", "Character Trait", "Sex", "Description"]

    for key in keys:
        start_index = prompt.find(key + ":")
        if start_index != -1:
            end_index = prompt.find("\n", start_index)
            if end_index == -1:
                end_index = len(prompt)
            line = prompt[start_index:end_index]

            _, value = line.split(":", 1)
            extracted_data[key] = value.strip()
        else:
            extracted_data[key] = ""

    if all(value != "" for value in extracted_data.values()):
        return extracted_data
    else:
        return {"Error": "Missing character information."}


async def handle_npc_spawn_request(message: str, config: BootConfig) -> StoredNpcProfile | str:
    npc_spawn_db = NpcSpawnDatabase.instance()
    gpt_interface = OpenAIHandler.instance()

    try:
        data = str_to_json(message)
    except Exception as error:
        return f"Failure to handle npc spawn request: {error}"

    realm_id = int(data.get("realm_id"))

    entry = npc_spawn_db.fetch_npc_spawn_by_realm(realm_id)
    if entry is not None:
        return entry

    if config.mock is True:
        profile = (realm_id, *MOCK_PROFILE)
        npc_spawn_db.insert_npc_spawn(profile)
    else:
        prompt = await gpt_interface.generate_npc_profile()
        character_info = extract_npc_profile(prompt)

        if "Error" in character_info:
            # Raise error instead ?
            error_msg = character_info["Error"]
            return f"Error extracting NPC profile: {error_msg}"

        npc_spawn_db.insert_npc_spawn(
            (
                realm_id,
                character_info["Name"] + " " + character_info["Surname"],
                character_info["Trait"],
                character_info["Sex"],
                character_info["Summary"],
            )
        )
    res = npc_spawn_db.fetch_npc_spawn_by_realm(realm_id)
    if res is None:
        return "Failure to handle npc spawn request"
    return res
