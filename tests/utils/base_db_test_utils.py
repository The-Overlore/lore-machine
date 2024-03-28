insert_query = "INSERT INTO test_table (value) VALUES (?)"
test_data = [{"value": f"test_value {i}", "rowid": i} for i in range(1, 4)]

update_query = "UPDATE test_table SET value = ? WHERE rowid = ?;"
test_update_data = [{"value": f"updated_value {i}", "rowid": i} for i in range(1, 4)]

select_query = "SELECT value FROM test_table WHERE rowid = ?;"


def prepare_data(db):
    for item in test_data:
        db.execute_query(insert_query, (item["value"],))
