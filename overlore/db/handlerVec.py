from __future__ import annotations

import json
import math
import os
import struct
from sqlite3 import Connection
from threading import Lock
from typing import Any

import sqlean
from openai import OpenAI


class VectorDatabaseHandler:
    path: str
    db: Connection
    _instance = None

    # create a lock
    lock = Lock()

    def __lock(self):
        self.lock.acquire(blocking=True, timeout=1000)

    def __release(self):
        self.lock.release()

    @classmethod
    def instance(cls) -> VectorDatabaseHandler:
        if cls._instance is None:
            print("Creating vector db interface")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def __load_sqlean(self, path: str) -> Connection:
        conn = sqlean.connect(path)
        # TODO Do we have to load the extension everytime we start up or only once when the db is first created?
        conn.enable_load_extension(True)
        conn.execute('SELECT load_extension("vector0")')
        conn.execute('SELECT load_extension("vss0")')
        return conn

    def __use_initial_queries(self) -> None:
        self.db.execute(
            """
                CREATE TABLE IF NOT EXISTS townhall (
                    discussion text
                );
            """
        )
        self.db.execute(
            """
                CREATE VIRTUAL TABLE vss_townhall using vss0(
                    embedding(1536)
                );
            """
        )

    def __insert(self, query: str, values: tuple) -> int:
        self.__lock()
        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()
        added_id = cursor.lastrowid
        self.__release()
        return added_id

    def __create_openai_embedding(self, text, model="text-embedding-ada-002"):
        client = OpenAI()
        text = text.replace("\n", " ")
        return client.embeddings.create(input=[text], model=model).data[0].embedding

    def __calculate_cosine_similarity(self, v1, v2):
        dot_prod = 0.0
        v1_sqr_sum = 0.0
        v2_sqr_sum = 0.0

        for i in range(len(v1)):
            dot_prod += v1[i] * v2[i]
            v1_sqr_sum += v1[i] ** 2
            v2_sqr_sum += v2[i] ** 2

        return dot_prod / (math.sqrt(v1_sqr_sum) * math.sqrt(v2_sqr_sum))

    def __save_to_file(self, discussion, rowid, embedding):
        # Writing the discussion, embedding, and rowid to a file
        with open("Output.json", "a") as file:  # 'a' mode appends to the file without overwriting existing data
            data_to_save = {"rowid": rowid, "discussion": discussion, "embedding": embedding}
            json.dump(data_to_save, file)
            file.write("\n")  # Add a newline to separate entries

    def init(self, path: str = "./vector.db") -> VectorDatabaseHandler:
        db_first_launch = not os.path.exists(path)
        self.db = self.__load_sqlean(path)
        if db_first_launch:
            self.__use_initial_queries()
        return self

    def serialize(self, vector: list[float]) -> bytes:
        """serializes a list of floats into a compact "raw bytes" format"""
        return struct.pack("%sf" % len(vector), *vector)

    def insert(self, discussion):
        discussion = discussion.strip()
        rowid = self.__insert("INSERT INTO townhall (discussion) VALUES (?);", (discussion,))
        embedding = self.__create_openai_embedding(discussion)
        self.__insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

        self.__save_to_file(discussion, rowid, embedding)

    def mock_insert(self, data):
        rowid = self.__insert("INSERT INTO townhall (discussion) VALUES (?);", (data["discussion"],))
        embedding = data["embedding"]
        self.__insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

    def get_all(self, printEnabled=False) -> Any:
        query = "SELECT * from townhall"
        cursor = self.db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()

        query_vss = """SELECT * from vss_townhall"""
        cursor = self.db.cursor()
        cursor.execute(query_vss)
        records_vss = cursor.fetchall()

        if printEnabled:
            print("Printing each row\n")
            for row, row_vss in zip(records, records_vss):
                for elem, elem_vss in zip(row, row_vss):
                    print(elem)
                    print("\n")
                    print(elem_vss[:10], end="")
                    print("...")
                print("\n\n")
            return records, records_vss
        return len(records), len(records_vss)

    def query_nn(self, query_embedding, limit=5):
        # SQLite version 3.41+
        # cur.execute("""
        #     select rowid, distance from vss_townhall
        #     where vss_search(embedding, ?)
        #     limit 5
        # """, (json.dumps(query_embedding),))
        # results = cur.fetchall()
        # return results

        # SQLite version < 3.41
        cursor = self.db.cursor()
        cursor.execute(
            """
            select rowid, distance from vss_townhall
            where vss_search(
                embedding,
                vss_search_params(
                    ?,
                    ?
                )
            )
            """,
            (json.dumps(query_embedding), limit),
        )
        results = cursor.fetchall()
        return results

    def query_cosine_similarity(self, query_embedding):
        cursor = self.db.cursor()
        cursor.execute(
            """
            select rowid, embedding from vss_townhall
            """
        )
        results = cursor.fetchall()

        # print("Cosine similarity")
        res = []
        for row in results:
            res.append({row[0]: self.__calculate_cosine_similarity(query_embedding, row[1])})
            # print(f"{row[0]}: {res}")

        # print(res)
        return res

    def find_lowest_second_param(self, data):
        # Find the dictionary with the lowest value
        lowest_dict = min(data, key=lambda x: list(x.values())[0])
        # Return the key of this dictionary
        return list(lowest_dict.keys())[0]

    def find_closest_to_one(self, data):
        # Initialize a variable to store the closest value and its key
        closest_key = None
        closest_value = float("-inf")  # Start with the lowest possible value

        for d in data:
            # Extract key and value from the dictionary
            key, value = list(d.items())[0]

            # Check if this value is closer to 1 than the current closest value
            if closest_value < value <= 1:
                closest_value = value
                closest_key = key

        return closest_key

    def vss_version(self):
        cursor = self.db.cursor()
        (version,) = cursor.execute("select vss_version()").fetchone()
        return version
