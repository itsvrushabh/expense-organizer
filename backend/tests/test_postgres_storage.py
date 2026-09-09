import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import storage
from models import CategoryCreate, Currency, ExpenseCreate


@pytest.fixture
def mock_pool():
    """Mock async psycopg connection pool, connection, and cursor."""
    pool = MagicMock()
    conn = MagicMock()
    cur = MagicMock()

    conn.commit = AsyncMock()
    conn.rollback = AsyncMock()

    # Setup async context managers
    pool.connection.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.connection.return_value.__aexit__ = AsyncMock(return_value=None)
    conn.cursor.return_value.__aenter__ = AsyncMock(return_value=cur)
    conn.cursor.return_value.__aexit__ = AsyncMock(return_value=None)

    cur.execute = AsyncMock()
    cur.fetchall = AsyncMock(return_value=[])
    cur.fetchone = AsyncMock(return_value=None)

    yield pool, conn, cur
    storage._pool = None


@pytest.mark.anyio
async def test_init_db_without_url():
    """When DATABASE_URL is empty, init_db should gracefully stay in in-memory mode."""
    with patch.dict(os.environ, {"DATABASE_URL": ""}):
        await storage.init_db()
        assert storage._pool is None
        assert not storage.is_db_connected()


@pytest.mark.anyio
async def test_close_db_handles_active_and_none_pool():
    """close_db should safely close active pool and handle None pool without exception."""
    # When pool is None
    storage._pool = None
    await storage.close_db()
    assert storage._pool is None

    # When pool is mock
    mock_p = MagicMock()
    mock_p.close = AsyncMock()
    storage._pool = mock_p
    await storage.close_db()
    mock_p.close.assert_awaited_once()
    assert storage._pool is None


@pytest.mark.anyio
async def test_postgres_get_currencies_with_pool(mock_pool):
    pool, conn, cur = mock_pool
    storage._pool = pool

    cur.fetchall.return_value = [
        ("USD", "US Dollar", "$", 1.0, True, "2026-09-10T00:00:00Z"),
        ("EUR", "Euro", "€", 0.92, False, "2026-09-10T00:00:00Z"),
    ]

    currencies = await storage.get_currencies()
    assert len(currencies) == 2
    assert currencies[0].code == "USD"
    assert currencies[1].code == "EUR"
    cur.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_postgres_update_currency_rates_with_pool(mock_pool):
    pool, conn, cur = mock_pool
    storage._pool = pool

    cur.fetchall.return_value = [
        ("USD", "US Dollar", "$", 1.0, True, "2026-09-10T00:00:00Z"),
        ("EUR", "Euro", "€", 0.95, False, "2026-09-10T00:00:00Z"),
    ]

    updated = await storage.update_currency_rates({"EUR": 0.95})
    assert len(updated) == 2
    assert cur.execute.await_count >= 1
    conn.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_postgres_categories_crud_with_pool(mock_pool):
    pool, conn, cur = mock_pool
    storage._pool = pool

    # 1. get_categories
    cur.fetchall.return_value = [
        (1, "Food", "utensils", "#FF5722", True),
        (2, "Transport", "car", "#2196F3", True),
    ]
    cats = await storage.get_categories(active_only=True)
    assert len(cats) == 2
    assert cats[0].name == "Food"

    # 2. create_category (first fetchone for get_category_by_name = None, second = created row)
    cur.fetchone.side_effect = [
        None,  # get_category_by_name check
        (10, "Software", "code", "#9C27B0", True),  # insert returning
        (10,),  # delete_category returning id
        (10,),  # activate_category returning id
    ]
    created = await storage.create_category(
        CategoryCreate(name="Software", icon="code", color="#9C27B0")
    )
    assert created.id == 10
    assert created.name == "Software"

    # 3. delete_category (soft delete)
    deleted = await storage.delete_category(10)
    assert deleted is True

    # 4. activate_category
    activated = await storage.activate_category(10)
    assert activated is True


@pytest.mark.anyio
async def test_postgres_expenses_crud_with_pool(mock_pool):
    pool, conn, cur = mock_pool
    storage._pool = pool

    with (
        patch("storage.resolve_category") as mock_res_cat,
        patch("storage.get_currency") as mock_get_curr,
    ):
        from models import Category

        mock_res_cat.return_value = Category(
            id=1, name="Food", icon="utensils", color="#FF5722", is_active=True
        )
        mock_get_curr.return_value = Currency(
            code="USD", name="US Dollar", symbol="$", exchange_rate=1.0, is_default=True
        )

        # 1. Add expense
        cur.fetchone.side_effect = [
            (42,),  # RETURNING id
            (
                42,
                "Dinner",
                55.0,
                "USD",
                "$",
                55.0,
                "Food",
                1,
                "utensils",
                "#FF5722",
                "2026-09-10",
            ),  # SELECT detailed
        ]
        exp = await storage.add(
            ExpenseCreate(
                description="Dinner",
                amount=55.0,
                category="Food",
                date="2026-09-10",
                currency="USD",
            )
        )
        assert exp.id == 42
        assert exp.amount == 55.0
        conn.commit.assert_awaited()

        # 2. Get expense by ID
        cur.fetchone.side_effect = None
        cur.fetchone.return_value = (
            42,
            "Dinner",
            55.0,
            "USD",
            "$",
            55.0,
            "Food",
            1,
            "utensils",
            "#FF5722",
            "2026-09-10",
        )
        fetched = await storage.get_expense(42)
        assert fetched is not None
        assert fetched.id == 42

        # 3. Update expense
        cur.fetchone.side_effect = [
            (
                42,
                "Dinner",
                55.0,
                "USD",
                "$",
                55.0,
                "Food",
                1,
                "utensils",
                "#FF5722",
                "2026-09-10",
            ),  # exists check
            (
                42,
                "Fancy Dinner",
                75.0,
                "USD",
                "$",
                75.0,
                "Food",
                1,
                "utensils",
                "#FF5722",
                "2026-09-10",
            ),  # updated view
        ]
        updated = await storage.update(
            42,
            ExpenseCreate(
                description="Fancy Dinner",
                amount=75.0,
                category="Food",
                date="2026-09-10",
                currency="USD",
            ),
        )
        assert updated is not None
        assert updated.amount == 75.0

        # 4. Delete expense
        cur.fetchone.side_effect = [
            (
                42,
                "Fancy Dinner",
                75.0,
                "USD",
                "$",
                75.0,
                "Food",
                1,
                "utensils",
                "#FF5722",
                "2026-09-10",
            ),  # old record
        ]
        deleted_exp = await storage.delete(42)
        assert deleted_exp is not None
        assert deleted_exp.id == 42


@pytest.mark.anyio
async def test_postgres_get_summary_with_pool(mock_pool):
    pool, conn, cur = mock_pool
    storage._pool = pool

    import json

    cur.fetchone.return_value = (
        120.50,
        3,
        "USD",
        "$",
        json.dumps(
            [
                {
                    "id": 1,
                    "description": "Groceries",
                    "amount": 50.0,
                    "category": "Groceries",
                    "date": "2026-09-10",
                }
            ]
        ),
    )

    summary = await storage.get_summary(year=2026, month=9, currency="USD")
    assert summary.total == 120.50
    assert summary.count == 3
    assert summary.currency == "USD"
    assert len(summary.expenses) == 1
    assert summary.expenses[0].id == 1
