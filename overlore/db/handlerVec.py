from __future__ import annotations

import json
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
        return client.embeddings.create(text=[text], model=model).data[0].embedding

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

        # Writing the discussion, embedding, and rowid to a file
        with open("Output.json", "a") as file:  # 'a' mode appends to the file without overwriting existing data
            data_to_save = {"rowid": rowid, "discussion": discussion, "embedding": embedding}
            json.dump(data_to_save, file)
            file.write("\n")  # Add a newline to separate entries

    def mock_insert(self, data):
        rowid = self.__insert("INSERT INTO townhall (discussion) VALUES (?);", (data["discussion"],))
        embedding = data["embedding"]
        self.__insert("INSERT INTO vss_townhall(rowid, embedding) VALUES (?, ?)", (rowid, json.dumps(embedding)))

    def get_all(self) -> Any:
        query = "SELECT * from townhall"
        cursor = self.db.cursor()
        cursor.execute(query)
        records = cursor.fetchall()

        query_vss = """SELECT * from vss_townhall"""
        cursor = self.db.cursor()
        cursor.execute(query_vss)
        records_vss = cursor.fetchall()
        print("Total rows are:  ", len(records_vss))
        print("Printing each row\n")
        for row, row_vss in zip(records, records_vss):
            for elem, elem_vss in zip(row, row_vss):
                print(elem)
                print("\n")
                print(elem_vss[:10], end="")
                print("...")
            print("\n\n")
        return records, records_vss

    def query(self, query_embedding):
        # SQLite version 3.41+
        # cur.execute("""
        #     select rowid, distance from vss_townhall
        #     where vss_search(embedding, ?)
        #     limit 5
        # """, (query_embedding,))
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
                    5
                )
            )
        """,
            (json.dumps(query_embedding),),
        )
        results = cursor.fetchall()
        return results
