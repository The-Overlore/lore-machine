from constants import ROLE, SEX, WORLD_SYSTEM_TEMPLATE, AGENT_TEMPLATE

class GptInterface:
    def __init__(self, openai_api_key, openai_embeddings_api_key):
        self.OPENAI_API_KEY = openai_api_key
        self.OPENAI_URL = "https://api.openai.com/v1/chat/completions"

        self.OPENAI_EMBEDDINGS_API_KEY = openai_embeddings_api_key
        self.OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"

        self.sex = SEX
        self.role = ROLE

    async def generatePrompt(self, promptSystem, promptUser):
        requestOptions = {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            },
            "body": {
                "messages": [
                    {"role": "system", "content": promptSystem},
                    {"role": "user", "content": promptUser},
                ],
                "model": "gpt-4", # 3.5 for cheaper testing ?
            },
        }

        try:
            response = requests.post(self.OPENAI_URL, json=requestOptions["body"], headers=requestOptions["headers"])
            return response.json()
        except Exception as error:
            print("Error:", error)

    
    async def generateEmbedding(self, textInput):
        requestOptions = {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.OPENAI_EMBEDDINGS_API_KEY}",
            },
            "body": {
                "input": textInput,
                "model": "text-embedding-ada-002",
            },
        }

        try:
            response = requests.post(self.OPENAI_EMBEDDINGS_URL, json=requestOptions["body"], headers=requestOptions["headers"])
            return response.json()
        except Exception as error:
            print("Error:", error)

    def generateTownHallDiscussion(self):
        systemPrompt = WORLD_SYSTEM_TEMPLATE.format(
            # Use getters for this
            realm_name = "Straejelas",
            realmState_happiness = "Happy",
            realmState_defense = "Vulnerable"
        )

        userPrompt = ""
        # Where do we get the npc_list from ?
        for npc in npc_list:
            userPrompt += AGENT_TEMPLATE.format(
                name = npc["name"],
                sex = SEX[npc.sex],
                role = ROLE[npc.role]
            )
            userPrompt += "\n"

        generatePrompt(systemPrompt, userPrompt)
