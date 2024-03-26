from __future__ import annotations

import os
from sqlite3 import Connection
from typing import Any, Callable

import sqlean

PreloadFunction = Callable[[Connection], None]
FunctionCallable = Callable[..., Any | None]
CustomFunction = tuple[str, int, FunctionCallable]

THREADSAFE = "THREADSAFE=1"


class BaseDatabase:
    db: Connection

    def __init__(self) -> None:
        raise RuntimeError(f"{self.__class__.__name__}: call _init from child")

    def _load_extensions(self, extensions: list[str]) -> None:
        for ext in extensions:
            self.db.load_extension(ext)

    def _insert(self, query: str, values: tuple[Any, ...]) -> int:
        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()
        added_id = cursor.lastrowid if cursor.lastrowid else 0
        return added_id

    def _update(self, query: str, values: tuple[Any, ...]) -> int:
        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()
        updated_entries_count = cursor.rowcount
        return updated_entries_count

    def _delete(self, query: str, values: tuple[Any, ...]) -> None:
        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()

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
        self,
        path: str,
        extensions: list[str],
        first_boot_queries: list[str],
        functions: list[CustomFunction],
        preload: PreloadFunction,
    ) -> None:
        db_first_launch = not os.path.exists(path)

        self.db: Connection = sqlean.connect(path, check_same_thread=False)
        threadsafety = self.db.execute(
            """
            select * from pragma_compile_options
            where compile_options like 'THREADSAFE=%'
            """
        ).fetchone()[0]
        if threadsafety != THREADSAFE:
            raise SystemError("SQlean is not configured for thread safety")

        self.db.enable_load_extension(True)
        preload(self.db)
        self._load_extensions(extensions)
        self.db.enable_load_extension(False)

        if db_first_launch:
            self._use_first_boot_queries(first_boot_queries)
        self.create_db_functions(functions)
