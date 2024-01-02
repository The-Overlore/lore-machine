import pytest

from overlore.db.handler import DatabaseHandler


@pytest.mark.asyncio
async def test_combat_outcome_event():
    db = DatabaseHandler.instance().init()
    test_message = {
        "eventEmitted": {
            "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
            "keys": [
                "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                "0x4b",
                "0x49",
                "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
            ],
            "data": ["0x1", "0x53", "0x0", "0x0", "0x0", "0x65a1bec0"],
            "createdAt": "2024-01-02 12:35:45",
        }
    }
    db_id = db.process_event(test_message)
    actual = db.get_by_id(db_id)
    expected = {
        "attacker_realm_id": 75,
        "target_realm_entity_id": 73,
        "attacking_entity_ids": [],
        "stolen_resources": [],
        "winner": 0,
        "damage": 0,
        "ts": 1705098944,
    }
    assert actual == expected


@pytest.mark.asyncio
async def test_trade_completed_event():
    db = DatabaseHandler.instance().init()
    test_message = {
        "eventEmitted": {
            "id": "0x00000000000000000000000000000000000000000000000000000000000001cf:0x0000:0x0023",
            "keys": [
                "0x27319ec70e0f69f3988d0a1a75dd2cc3715d4d7a60acec45b51fe577a5f2bf1",
                "0x7d",
                "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
            ],
            "data": ["0x4b", "0x49", "0x1", "0x8", "0x3e8", "0x1", "0x1", "0x3e8", "0x65a1dafd"],
            "createdAt": "2024-01-02 14:36:14",
        }
    }
    db_id = db.process_event(test_message)
    actual = db.get_by_id(db_id)
    expected = {
        "trade_id": 125,
        "maker_id": 75,
        "taker_id": 73,
        "resources_maker": [{"type": 8, "amount": 1}],
        "resources_taker": [{"type": 1, "amount": 1}],
        "ts": 1705106173,
    }
    assert actual == expected
