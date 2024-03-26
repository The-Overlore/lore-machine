from sqlite3 import Connection

import pytest
import sqlean

from overlore.sqlite.base_db import BaseDatabase
from tests.utils.base_db_test_utils import (
    given_insert_values,
    given_update_values,
    insert_data_into_db,
    insert_query,
    select_query,
    update_query,
)


@pytest.fixture
def db():
    db = BaseDatabase.__new__(BaseDatabase)
    db._init(":memory:", [], ["CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)"], [], lambda db: None)
    yield db
    db.close_conn()


def test_execute_query(db):
    insert_data_into_db(db)

    results = db.execute_query("SELECT * FROM test_table", ())

    assert len(results) == len(given_insert_values)


def test_insert(db):
    for item in given_insert_values:
        added_rowid = db._insert(insert_query, (item["value"],))
        retrieved_entry = db.execute_query(select_query, (added_rowid,))[0][0]

        assert item["rowid"] == added_rowid, f"Expected rowid {item['rowid']}, got {added_rowid}"
        assert item["value"] == retrieved_entry, f"Expected value '{item['value']}', got '{retrieved_entry}'"


def test_update(db):
    insert_data_into_db(db)

    for item in given_update_values:
        updated_rows_count = db._update(update_query, (item["value"], item["rowid"]))
        retrieved_entry = db.execute_query(select_query, (item["rowid"],))[0][0]

        assert updated_rows_count == 1, f"Expected 1 updated row, got {updated_rows_count}"
        assert item["value"] == retrieved_entry, f"Expected value '{item['value']}', got '{retrieved_entry}'"


def test_close_conn(db):
    db.close_conn()
    with pytest.raises(sqlean.dbapi2.ProgrammingError):
        db.execute_query("SELECT 1", ())


def test_custom_function(db):
    def test_func(x):
        return x * 2

    db.create_db_functions([("test_func", 1, test_func)])

    db.execute_query("CREATE TABLE test_func_table (id INTEGER PRIMARY KEY, value INTEGER)", ())
    db.execute_query("INSERT INTO test_func_table (value) VALUES (10)", ())
    result = db.execute_query("SELECT test_func(value) FROM test_func_table WHERE id = 1", ())[0][0]

    assert result == 20, f"Expected custom function result 20, got {result}"


def test_error_handling(db):
    # Test with a malformed query
    with pytest.raises(sqlean.dbapi2.OperationalError):
        db.execute_query("SELEC * FROM test_table", ())

    # Test updating a non-existent record
    updated_count = db._update("UPDATE test_table SET value = ? WHERE id = ?", ("new_value", 9999))
    assert updated_count == 0, "Expected updated_count 0 for non-existent record"

    # Test fetching from a non-existent table
    with pytest.raises(sqlean.dbapi2.OperationalError):
        db.execute_query("SELECT * FROM non_existent_table", ())


def test_load_extensions(db):
    extension_name = "mod_spatialite"

    db.db.enable_load_extension(True)
    db._load_extensions([extension_name])
    db.db.enable_load_extension(False)

    result = db.execute_query("SELECT AddGeometryColumn('test_geom', 'the_geom', 4326, 'POINT', 'XY', 0)", ())
    assert result is not None, "Extension function did not execute correctly"


def test_first_boot_queries(db):
    first_boot_query = "CREATE TABLE IF NOT EXISTS first_boot_test (id INTEGER PRIMARY KEY, value TEXT)"

    db._use_first_boot_queries([first_boot_query])

    tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='first_boot_test';", ())
    assert len(tables) > 0, "First boot table was not created"


def test_preload_function(db):
    def preload(db: Connection):
        db.execute("CREATE TABLE preload_test (id INTEGER PRIMARY KEY, value TEXT)")

    db._init(":memory:", [], [], [], preload)

    tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='preload_test';", ())
    assert len(tables) > 0, "Preload table was not created"


def test_thread_safety_configuration(db):
    threadsafety = db.execute_query("PRAGMA compile_options;", ())
    assert any("THREADSAFE=1" in option for option, in threadsafety), "Database is not configured for thread safety"


def test_init_call(db):
    with pytest.raises(RuntimeError):
        db.__init__()
