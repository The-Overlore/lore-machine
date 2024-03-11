import pytest

from overlore.graphql.subscriptions import process_received_event
from overlore.sqlite.events_db import EventsDatabase


def init_db() -> EventsDatabase:
    db = EventsDatabase.instance().init(":memory:")
    db.realms.init("./tests/data/test_geodata.json")
    return db


@pytest.mark.asyncio
async def test_trade_event():
    db = init_db()
    db_id = process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001cf:0x0000:0x0023",
                "keys": [
                    "0x27319ec70e0f69f3988d0a1a75dd2cc3715d4d7a60acec45b51fe577a5f2bf1",
                    "0x7d",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x4b", "0x2", "0x49", "0x1", "0x1", "0x8", "0x1388", "0x1", "0x1", "0x1388", "0x65a1dafd"],
                "createdAt": "2024-01-02 14:36:14",
            }
        }
    )
    assert db.get_by_ids([db_id,]) == [
        [
            db_id,
            0,
            73,
            1,
            75,
            2,
            1.0,
            1705106173,
            (
                '{"resources_maker": [{"resource_type": 8, "amount": 5}], "resources_taker": [{"resource_type": 1,'
                ' "amount": 5}]}'
            ),
            (0.0, 0.0),
            (0.0, 2000.0),
        ]
    ]


@pytest.mark.asyncio
async def test_combat_damage_success():
    db = init_db()
    db_id = process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x64", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )
    assert db.get_by_ids([db_id,]) == [
        [
            db_id,
            1,
            75,
            1,
            73,
            2,
            1.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 100}',
            (0.0, 0.0),
            (0.0, 2000.0),
        ]
    ]
    db_id = process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0003",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x3e8", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )
    assert db.get_by_ids([db_id,]) == [
        [
            db_id,
            1,
            75,
            1,
            73,
            2,
            10.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 1000}',
            (0.0, 0.0),
            (0.0, 2000.0),
        ]
    ]


@pytest.mark.asyncio
async def test_combat_steal():
    db = init_db()

    db_id = process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0x2710", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )
    assert db.get_by_ids([db_id,]) == [
        [
            db_id,
            1,
            75,
            1,
            73,
            2,
            1.0,
            1705098944,
            (
                '{"attacking_entity_ids": [], "stolen_resources": [{"resource_type": 8, "amount": 10}], "winner": 0,'
                ' "damage": 0}'
            ),
            (0.0, 0.0),
            (0.0, 2000.0),
        ]
    ]

    db_id = process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0003",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0xc350", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )
    assert db.get_by_ids([db_id,]) == [
        [
            db_id,
            1,
            75,
            1,
            73,
            2,
            5.0,
            1705098944,
            (
                '{"attacking_entity_ids": [], "stolen_resources": [{"resource_type": 8, "amount": 50}], "winner": 0,'
                ' "damage": 0}'
            ),
            (0.0, 0.0),
            (0.0, 2000.0),
        ]
    ]


@pytest.mark.asyncio
async def test_combat_damage_stolen_resources_set():
    init_db()

    with pytest.raises(RuntimeError):
        process_received_event(
            {
                "eventEmitted": {
                    "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                    "keys": [
                        "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                        "0x4b",
                        "0x1",
                        "0x49",
                        "0x2",
                        "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                    ],
                    "data": ["0x1", "0x53", "0x1", "0x8", "0x2710", "0x0", "0x3e8", "0x65a1bec0"],
                    "createdAt": "2024-01-02 12:35:45",
                }
            }
        )


@pytest.mark.asyncio
async def test_get_all():
    db = init_db()
    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0x2710", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )
    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0003",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0xc350", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )

    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0004",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x64", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )

    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0005",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x1",
                    "0x49",
                    "0x2",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x3e8", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        }
    )
    assert db.get_all() == [
        [
            1,
            1,
            75,
            1,
            73,
            2,
            1.0,
            1705098944,
            (
                '{"attacking_entity_ids": [], "stolen_resources": [{"resource_type": 8, "amount": 10}], "winner": 0,'
                ' "damage": 0}'
            ),
            (0.0, 0.0),
            (0.0, 2000.0),
        ],
        [
            2,
            1,
            75,
            1,
            73,
            2,
            5.0,
            1705098944,
            (
                '{"attacking_entity_ids": [], "stolen_resources": [{"resource_type": 8, "amount": 50}], "winner": 0,'
                ' "damage": 0}'
            ),
            (0.0, 0.0),
            (0.0, 2000.0),
        ],
        [
            3,
            1,
            75,
            1,
            73,
            2,
            1.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 100}',
            (0.0, 0.0),
            (0.0, 2000.0),
        ],
        [
            4,
            1,
            75,
            1,
            73,
            2,
            10.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 1000}',
            (0.0, 0.0),
            (0.0, 2000.0),
        ],
    ]


@pytest.mark.asyncio
async def test_fetch_relevant_events_decay_time():
    db = init_db()

    test_message = {
        "eventEmitted": {
            "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
            "keys": [
                "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                "0x88",
                "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
            ],
            "data": ["0x4b", "0x2", "0x49", "0x1", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
            "createdAt": "2024-01-08 16:38:25",
        }
    }
    # store 7 events that are one day appart
    for i in range(0, 5):
        process_received_event(test_message)
        test_message["eventEmitted"]["id"] = str(i)
        ts = int(test_message["eventEmitted"]["data"][8], base=16)
        ts -= 86400
        test_message["eventEmitted"]["data"][8] = hex(ts)

    assert db.fetch_most_relevant_event(realm_position=db.realms.position_by_id(2), current_time=1704831904) == [
        1,
        0,
        73,
        1,
        75,
        2,
        10.0,
        1704831904,
        (
            '{"resources_maker": [{"resource_type": 253, "amount": 50}], "resources_taker": [{"resource_type": 3,'
            ' "amount": 50}]}'
        ),
        (0.0, 0.0),
        (0.0, 2000.0),
    ]


@pytest.mark.asyncio
async def test_fetch_relevant_events_decay_distance():
    db = init_db()

    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x10", "0x6", "0x11", "0x1", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        }
    )
    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0024",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x10", "0x6", "0x11", "0x2", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        }
    )
    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0025",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x10", "0x6", "0x11", "0x3", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        }
    )
    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0026",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x10", "0x6", "0x11", "0x4", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        }
    )
    process_received_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0027",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x10", "0x6", "0x11", "0x5", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        }
    )
    assert db.fetch_most_relevant_event(realm_position=db.realms.position_by_id(1), current_time=0x659DABA0) == [
        1,
        0,
        17,
        1,
        16,
        6,
        10.0,
        1704831904,
        (
            '{"resources_maker": [{"resource_type": 253, "amount": 50}], "resources_taker": [{"resource_type": 3,'
            ' "amount": 50}]}'
        ),
        (0.0, 0.0),
        (9999.0, 9999.0),
    ]


@pytest.mark.asyncio
async def test_fetch_relevant_events_empty_db():
    db = init_db()
    assert None is db.fetch_most_relevant_event(realm_position=db.realms.position_by_id(1), current_time=0x659DABA0)
