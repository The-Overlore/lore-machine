from __future__ import annotations

from sqlite3 import Connection
from threading import Lock
from typing import Any, Generic, TypeVar, cast

import sqlean

T = TypeVar("T", bound="BaseDatabaseHandler")


class BaseDatabaseHandler(Generic[T]):
    path: str
    db: Connection
    # _instance = None
    _instances: dict[type[T], T] = {}
    lock = Lock()

    def _lock(self) -> None:
        self.lock.acquire(blocking=True, timeout=1000)

    def _release(self) -> None:
        self.lock.release()

    # @classmethod
    def __init__(self) -> None:
        raise RuntimeError("Call instance() instead")

    def _load_sqlean(self, path: str, extentions: list[str]) -> Connection:
        conn: Connection = sqlean.connect(path)
        conn.enable_load_extension(True)
        for ext in extentions:
            conn.execute("SELECT load_extension(?)", (ext,))
        return conn

    # TO FIX: Any
    def _insert(self, query: str, values: tuple[Any]) -> int:
        self._lock()
        cursor = self.db.cursor()
        cursor.execute(query, values)
        self.db.commit()
        added_id = cursor.lastrowid if cursor.lastrowid else 0
        self._release()
        return added_id

    def _use_initial_queries(self) -> None:
        raise NotImplementedError("This method should be implemented by subclasses")

    # def init(self, path: str) -> BaseDatabaseHandler:
    #     db_first_launch = not os.path.exists(path)
    #     self.db = self.__load_sqlean(path)
    #     if db_first_launch:
    #         self.__use_initial_queries()
    #     return self

    # @classmethod
    # def instance(cls) -> BaseDatabaseHandler:
    #     if cls._instance is None:
    #         print(f"Creating {cls.__name__} interface")
    #         cls._instance = cls.__new__(cls)
    #     return cls._instance

    @classmethod
    def instance(cls: type[T]) -> T:
        if cls not in cls._instances:
            print(f"Creating {cls.__name__} interface")
            cls._instances[cls] = cls.__new__(cls)
            # Initialize the instance if needed
            # For example, you might call an init method here (not __init__)
            # cls._instances[cls].init()
        return cast(T, cls._instances[cls])
