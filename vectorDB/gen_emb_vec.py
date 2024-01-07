from openai import OpenAI

export OPENAI_API_KEY=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


def create_embedding(input, model="text-embedding-ada-002"):
    client = OpenAI()
    input = input.replace("\n", " ")
    return client.embeddings.create(input = [input], model=model).data[0].embedding


input="" # GPT generated summaries

embeddeding = create_embedding(input)

# Write {input, embedding} to mock_embedded_vectors.json 
# !! append to file, no overwriting