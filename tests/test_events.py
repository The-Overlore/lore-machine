import pytest

from overlore.eternum.constants import Realms
from overlore.graphql.event import process_event
from overlore.sqlite.events_db import EventsDatabase


@pytest.mark.asyncio
async def test_trade_event():
    db = EventsDatabase.instance().init(":memory:")
    db_id = process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001cf:0x0000:0x0023",
                "keys": [
                    "0x27319ec70e0f69f3988d0a1a75dd2cc3715d4d7a60acec45b51fe577a5f2bf1",
                    "0x7d",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x4b", "0x49", "0x1", "0x8", "0x1388", "0x1", "0x1", "0x1388", "0x65a1dafd"],
                "createdAt": "2024-01-02 14:36:14",
            }
        },
        db,
    )

    assert db.get_by_id(db_id) == [
        db_id,
        0,
        1.0,
        1705106173,
        '{"resources_maker": [{"type": 8, "amount": 5}], "resources_taker": [{"type": 1, "amount": 5}]}',
        (-53.6529, 47.48),
        (114.8471, 43.38),
    ]


@pytest.mark.asyncio
async def test_combat_damage():
    db = EventsDatabase.instance().init(":memory:")
    db_id = process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x64", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )
    assert db.get_by_id(db_id) == [
        db_id,
        1,
        1.0,
        1705098944,
        '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 100}',
        (-53.6529, 47.48),
        (114.8471, 43.38),
    ]
    db_id = process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x3e8", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )
    assert db.get_by_id(db_id) == [
        db_id,
        1,
        10.0,
        1705098944,
        '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 1000}',
        (-53.6529, 47.48),
        (114.8471, 43.38),
    ]


@pytest.mark.asyncio
async def test_combat_steal():
    db = EventsDatabase.instance().init(":memory:")

    db_id = process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0x2710", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )
    assert db.get_by_id(db_id) == [
        db_id,
        1,
        1.0,
        1705098944,
        '{"attacking_entity_ids": [], "stolen_resources": [{"type": 8, "amount": 10}], "winner": 0, "damage": 0}',
        (-53.6529, 47.48),
        (114.8471, 43.38),
    ]

    db_id = process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0xc350", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )
    assert db.get_by_id(db_id) == [
        db_id,
        1,
        5.0,
        1705098944,
        '{"attacking_entity_ids": [], "stolen_resources": [{"type": 8, "amount": 50}], "winner": 0, "damage": 0}',
        (-53.6529, 47.48),
        (114.8471, 43.38),
    ]


@pytest.mark.asyncio
async def test_combat_damage_stolen_resources_set():
    db = EventsDatabase.instance().init(":memory:")

    with pytest.raises(RuntimeError):
        process_event(
            {
                "eventEmitted": {
                    "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                    "keys": [
                        "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                        "0x4b",
                        "0x49",
                        "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                    ],
                    "data": ["0x1", "0x53", "0x1", "0x8", "0x2710", "0x0", "0x3e8", "0x65a1bec0"],
                    "createdAt": "2024-01-02 12:35:45",
                }
            },
            db,
        )


@pytest.mark.asyncio
async def test_get_all():
    db = EventsDatabase.instance().init(":memory:")
    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0x2710", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )
    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x1", "0x8", "0xc350", "0x0", "0x0", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )

    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x64", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )

    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001c8:0x0000:0x0002",
                "keys": [
                    "0x1736c207163ad481e2a196c0fb6394f90c66c2e2b52e0c03d4a077ac6cea918",
                    "0x4b",
                    "0x49",
                    "0x1b0a83a27a357e0574393ab06c0c774db7312a0993538cc0186d054f75ee84e",
                ],
                "data": ["0x1", "0x53", "0x0", "0x0", "0x3e8", "0x65a1bec0"],
                "createdAt": "2024-01-02 12:35:45",
            }
        },
        db,
    )

    assert db.get_all() == [
        [
            1,
            1,
            1.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [{"type": 8, "amount": 10}], "winner": 0, "damage": 0}',
            (-53.6529, 47.48),
            (114.8471, 43.38),
        ],
        [
            2,
            1,
            5.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [{"type": 8, "amount": 50}], "winner": 0, "damage": 0}',
            (-53.6529, 47.48),
            (114.8471, 43.38),
        ],
        [
            3,
            1,
            1.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 100}',
            (-53.6529, 47.48),
            (114.8471, 43.38),
        ],
        [
            4,
            1,
            10.0,
            1705098944,
            '{"attacking_entity_ids": [], "stolen_resources": [], "winner": 0, "damage": 1000}',
            (-53.6529, 47.48),
            (114.8471, 43.38),
        ],
    ]


@pytest.mark.asyncio
async def test_fetch_relevant_events_decay_time():
    db = EventsDatabase.instance().init(":memory:")

    test_message = {
        "eventEmitted": {
            "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
            "keys": [
                "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                "0x88",
                "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
            ],
            "data": ["0x4b", "0x49", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
            "createdAt": "2024-01-08 16:38:25",
        }
    }
    # store 7 events that are one day appart
    for _i in range(0, 5):
        process_event(test_message, db)
        ts = int(test_message["eventEmitted"]["data"][8], base=16)
        ts -= 86400
        test_message["eventEmitted"]["data"][8] = hex(ts)

    assert db.fetch_most_relevant(realm_position=db.realms.position_by_id(75), current_time=1704831904) == [
        (
            1,
            10.0,
        ),
        (
            2,
            9.523809523809524,
        ),
        (
            3,
            9.047619047619047,
        ),
        (
            4,
            8.571428571428571,
        ),
        (
            5,
            8.095238095238095,
        ),
    ]


@pytest.mark.asyncio
async def test_fetch_relevant_events_decay_distance():
    db = EventsDatabase.instance().init(":memory:")

    realms = Realms.instance()
    realms.geodata = realms.load_geodata("./tests/data/test_geodata.json")

    db.realms = realms
    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x6", "0x1", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        },
        db,
    )
    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x6", "0x2", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        },
        db,
    )
    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x6", "0x3", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        },
        db,
    )
    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x6", "0x4", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        },
        db,
    )
    process_event(
        {
            "eventEmitted": {
                "id": "0x00000000000000000000000000000000000000000000000000000000000001ad:0x0000:0x0023",
                "keys": [
                    "0x20e86edfa14c93309aa6559742e993d42d48507f3bf654a12d77a54f10f8945",
                    "0x88",
                    "0x63cbe849cf6325e727a8d6f82f25fad7dc7eb9433767f5c1b8c59189e36c9b6",
                ],
                "data": ["0x6", "0x5", "0x1", "0xfd", "0xc350", "0x1", "0x3", "0xc350", "0x659daba0"],
                "createdAt": "2024-01-08 16:38:25",
            }
        },
        db,
    )
    assert db.fetch_most_relevant(realm_position=db.realms.position_by_id(1), current_time=0x659DABA0) == [
        (1, 10.0),
        (2, 9.333333333333334),
        (3, 8.666666666666666),
        (4, 8.0),
        (5, 7.333333333333333),
    ]
