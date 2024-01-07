import psycopg2
from openai import OpenAI


def db_connect(port, host="localhost", database="cwastche"):
    conn = psycopg2.connect(
        port=port,
        host=host,
        database=database,
        user="postgres",
        password="postgres"
    )
    return conn

def create_embedding(input, model="text-embedding-ada-002"):
    client = OpenAI()
    input = input.replace("\n", " ")
    return client.embeddings.create(input = [input], model=model).data[0].embedding