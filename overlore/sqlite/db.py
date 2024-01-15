from __future__ import annotations

import os
from sqlite3 import Connection
from threading import Lock
from typing import Any, Callable

import sqlean

FunctionCallable = Callable[..., Any | None]
CustomFunction = tuple[str, int, FunctionCallable]


class Database:
    db: Connection
    lock = Lock()

    def _lock(self) -> None:
        self.lock.acquire(blocking=True, timeout=1000)

    def _release(self) -> None:
        self.lock.release()

    def __init__(self) -> None:
        raise RuntimeError(f"{self.__class__.__name__}: call instance() instead")

    def _load_extensions(self, extensions: list[str]) -> None:
        self.db.enable_load_extension(True)
        for ext in extensions:
            self.db.load_extension(ext)
        self.db.enable_load_extension(False)

    def _insert(self, query: str, values: tuple[Any, ...]) -> int:
        self._lock()
        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()
        added_id = cursor.lastrowid if cursor.lastrowid else 0
        self._release()
        return added_id

    def _use_first_boot_queries(self, queries: list[str]) -> None:
        for query in queries:
            self.db.execute(query)

    def execute_query(self, query: str, params: tuple[Any, ...]) -> list[Any]:
        cursor = self.db.cursor()
        cursor.execute(query, params)
        records = cursor.fetchall()
        return records

    def close_conn(self) -> None:
        self.db.close()

    def create_db_functions(self, functions: list[CustomFunction]) -> None:
        for func in functions:
            self.db.create_function(name=func[0], narg=func[1], func=func[2])

    def _init(
        self, path: str, extensions: list[str], first_boot_queries: list[str], functions: list[CustomFunction]
    ) -> None:
        self.db: Connection = sqlean.connect(path)
        self._load_extensions(extensions)
        db_first_launch = not os.path.exists(path)
        if db_first_launch:
            self._use_first_boot_queries(first_boot_queries)
        self.create_db_functions(functions)
