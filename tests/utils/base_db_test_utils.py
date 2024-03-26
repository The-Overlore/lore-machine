insert_query = "INSERT INTO test_table (value) VALUES (?)"
given_insert_values = [{"value": f"test_value {i}", "rowid": i} for i in range(1, 4)]

update_query = "UPDATE test_table SET value = ? WHERE rowid = ?;"
given_update_values = [{"value": f"updated_value {i}", "rowid": i} for i in range(1, 4)]

select_query = "SELECT value FROM test_table WHERE rowid = ?;"


def insert_data_into_db(db):
    for item in given_insert_values:
        db.execute_query(insert_query, (item["value"],))
