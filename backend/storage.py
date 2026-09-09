import asyncio
from datetime import date, datetime
import json
import logging
import os
from typing import Dict, List, Optional, Tuple

from models import Category, CategoryCreate, Currency, Expense, ExpenseCreate, ExpenseSummary

logger = logging.getLogger("expense_backend.storage")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# ---------------------------------------------------------------------------
# In-Memory Default Data (Active when DATABASE_URL is not set or in tests)
# ---------------------------------------------------------------------------

DEFAULT_CURRENCIES: Dict[str, Currency] = {
    "USD": Currency(code="USD", name="US Dollar", symbol="$", exchange_rate=1.0, is_default=True),
    "INR": Currency(code="INR", name="Indian Rupee", symbol="₹", exchange_rate=84.0, is_default=False),
    "EUR": Currency(code="EUR", name="Euro", symbol="€", exchange_rate=0.92, is_default=False),
    "JPY": Currency(code="JPY", name="Japanese Yen", symbol="¥", exchange_rate=150.0, is_default=False),
    "GBP": Currency(code="GBP", name="British Pound", symbol="£", exchange_rate=0.78, is_default=False),
    "CNY": Currency(code="CNY", name="Chinese Yuan", symbol="¥", exchange_rate=7.2, is_default=False),
}

DEFAULT_CATEGORIES_DATA = [
    ("Food", "utensils", "#FF5722"),
    ("Groceries", "shopping-cart", "#4CAF50"),
    ("Transport", "car", "#2196F3"),
    ("Shopping", "shopping-bag", "#E91E63"),
    ("Entertainment", "film", "#9C27B0"),
    ("Utilities", "zap", "#FF9800"),
    ("Health", "heart-pulse", "#E53935"),
    ("Travel", "plane", "#00BCD4"),
    ("Education", "book-open", "#3F51B5"),
    ("Personal", "user", "#795548"),
    ("Online", "globe", "#009688"),
    ("Other", "more-horizontal", "#607D8B"),
]

_currencies: Dict[str, Currency] = {k: v.model_copy() for k, v in DEFAULT_CURRENCIES.items()}
_categories: List[Category] = [
    Category(id=i + 1, name=name, icon=icon, color=color, is_active=True)
    for i, (name, icon, color) in enumerate(DEFAULT_CATEGORIES_DATA)
]
_expenses: List[Expense] = []
_next_id = 1
_next_category_id = len(_categories) + 1
_pool = None


def reset_in_memory():
    """Resets in-memory stores for isolated testing."""
    global _expenses, _next_id, _categories, _next_category_id, _currencies
    _expenses = []
    _next_id = 1
    _currencies = {k: v.model_copy() for k, v in DEFAULT_CURRENCIES.items()}
    _categories = [
        Category(id=i + 1, name=name, icon=icon, color=color, is_active=True)
        for i, (name, icon, color) in enumerate(DEFAULT_CATEGORIES_DATA)
    ]
    _next_category_id = len(_categories) + 1


def is_db_connected() -> bool:
    return _pool is not None


# ---------------------------------------------------------------------------
# Database Initialization & Migrations (PostgreSQL)
# ---------------------------------------------------------------------------

async def init_db(max_retries: int = 5, retry_delay: float = 1.0):
    global _pool
    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        logger.info("DATABASE_URL not set. Running with in-memory storage.")
        return

    # Normalise postgres:// to postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    from psycopg_pool import AsyncConnectionPool

    for attempt in range(1, max_retries + 1):
        try:
            pool = AsyncConnectionPool(db_url, min_size=1, max_size=10, open=False)
            await pool.open()

            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    # 1. Currency Table
                    await cur.execute("""
                        CREATE TABLE IF NOT EXISTS currency (
                            code VARCHAR(3) PRIMARY KEY,
                            name VARCHAR(50) NOT NULL,
                            symbol VARCHAR(10) NOT NULL,
                            exchange_rate NUMERIC(14, 6) NOT NULL DEFAULT 1.000000 CHECK (exchange_rate > 0),
                            is_default BOOLEAN NOT NULL DEFAULT FALSE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );

                        CREATE INDEX IF NOT EXISTS idx_currency_code ON currency(code);

                        INSERT INTO currency (code, name, symbol, exchange_rate, is_default) VALUES
                        ('USD', 'US Dollar', '$', 1.0000, true),
                        ('INR', 'Indian Rupee', '₹', 84.0000, false),
                        ('EUR', 'Euro', '€', 0.9200, false),
                        ('JPY', 'Japanese Yen', '¥', 150.0000, false),
                        ('GBP', 'British Pound', '£', 0.7800, false),
                        ('CNY', 'Chinese Yuan', '¥', 7.2000, false)
                        ON CONFLICT (code) DO NOTHING;
                    """)

                    # 2. Category Table (Case-insensitive unique name + soft-delete is_active)
                    await cur.execute("""
                        CREATE TABLE IF NOT EXISTS category (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(50) NOT NULL,
                            icon VARCHAR(50) NOT NULL DEFAULT 'help-circle',
                            color VARCHAR(20) NOT NULL DEFAULT '#607D8B',
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );

                        CREATE UNIQUE INDEX IF NOT EXISTS idx_category_unique_lower_name ON category (LOWER(TRIM(name)));
                        CREATE INDEX IF NOT EXISTS idx_category_is_active ON category(is_active);

                        INSERT INTO category (name, icon, color) VALUES
                        ('Food', 'utensils', '#FF5722'),
                        ('Groceries', 'shopping-cart', '#4CAF50'),
                        ('Transport', 'car', '#2196F3'),
                        ('Shopping', 'shopping-bag', '#E91E63'),
                        ('Entertainment', 'film', '#9C27B0'),
                        ('Utilities', 'zap', '#FF9800'),
                        ('Health', 'heart-pulse', '#E53935'),
                        ('Travel', 'plane', '#00BCD4'),
                        ('Education', 'book-open', '#3F51B5'),
                        ('Personal', 'user', '#795548'),
                        ('Online', 'globe', '#009688'),
                        ('Other', 'more-horizontal', '#607D8B')
                        ON CONFLICT (LOWER(TRIM(name))) DO NOTHING;
                    """)

                    # 3. Expenses Table & Migration DO Block
                    await cur.execute("""
                        CREATE TABLE IF NOT EXISTS expenses (
                            id SERIAL PRIMARY KEY,
                            description TEXT NOT NULL,
                            amount DOUBLE PRECISION NOT NULL CHECK (amount > 0),
                            currency_code VARCHAR(3) NOT NULL DEFAULT 'USD' REFERENCES currency(code) ON DELETE RESTRICT,
                            category_id INT NOT NULL REFERENCES category(id) ON DELETE RESTRICT,
                            date DATE NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );

                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'expenses' AND column_name = 'currency_code'
                            ) THEN
                                ALTER TABLE expenses ADD COLUMN currency_code VARCHAR(3) DEFAULT 'USD' REFERENCES currency(code) ON DELETE RESTRICT;
                            END IF;

                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'expenses' AND column_name = 'category_id'
                            ) THEN
                                ALTER TABLE expenses ADD COLUMN category_id INT REFERENCES category(id) ON DELETE RESTRICT;
                            END IF;

                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'expenses' AND column_name = 'category'
                            ) THEN
                                INSERT INTO category (name)
                                SELECT DISTINCT e.category
                                FROM expenses e
                                WHERE LOWER(TRIM(e.category)) NOT IN (SELECT LOWER(TRIM(name)) FROM category)
                                ON CONFLICT (LOWER(TRIM(name))) DO NOTHING;

                                UPDATE expenses e
                                SET category_id = c.id
                                FROM category c
                                WHERE LOWER(TRIM(e.category)) = LOWER(TRIM(c.name))
                                  AND e.category_id IS NULL;

                                UPDATE expenses SET category_id = (SELECT id FROM category WHERE LOWER(TRIM(name)) = 'other' LIMIT 1)
                                WHERE category_id IS NULL;

                                ALTER TABLE expenses ALTER COLUMN category_id SET NOT NULL;
                                ALTER TABLE expenses ALTER COLUMN currency_code SET NOT NULL;
                                ALTER TABLE expenses DROP COLUMN category;
                            END IF;
                        END $$;
                    """)

                    # 4. Indices on Expenses (including Recommendation #6 Expression Indices)
                    await cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
                        CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON expenses(category_id);
                        CREATE INDEX IF NOT EXISTS idx_expenses_currency_code ON expenses(currency_code);
                        CREATE INDEX IF NOT EXISTS idx_expenses_date_category ON expenses(date, category_id);

                        CREATE INDEX IF NOT EXISTS idx_expenses_year_month ON expenses (
                            EXTRACT(YEAR FROM date),
                            EXTRACT(MONTH FROM date)
                        );
                        CREATE INDEX IF NOT EXISTS idx_expenses_year_month_cat ON expenses (
                            EXTRACT(YEAR FROM date),
                            EXTRACT(MONTH FROM date),
                            category_id
                        );
                        CREATE INDEX IF NOT EXISTS idx_expenses_iso_year_week ON expenses (
                            EXTRACT(ISOYEAR FROM date),
                            EXTRACT(WEEK FROM date)
                        );
                    """)

                    # 5. SQL Views for Expenses and Summaries
                    await cur.execute("""
                        CREATE OR REPLACE VIEW view_expenses_detailed AS
                        SELECT
                            e.id,
                            e.description,
                            e.amount::FLOAT AS amount,
                            e.currency_code,
                            curr.name AS currency_name,
                            curr.symbol AS currency_symbol,
                            curr.exchange_rate::FLOAT AS exchange_rate,
                            ROUND((e.amount / curr.exchange_rate)::numeric, 2)::FLOAT AS amount_usd,
                            e.date,
                            EXTRACT(YEAR FROM e.date)::INT AS year,
                            EXTRACT(MONTH FROM e.date)::INT AS month,
                            EXTRACT(DAY FROM e.date)::INT AS day,
                            EXTRACT(WEEK FROM e.date)::INT AS iso_week,
                            EXTRACT(ISOYEAR FROM e.date)::INT AS iso_year,
                            c.id AS category_id,
                            c.name AS category,
                            c.icon AS category_icon,
                            c.color AS category_color,
                            c.is_active AS category_is_active
                        FROM expenses e
                        JOIN category c ON e.category_id = c.id
                        JOIN currency curr ON e.currency_code = curr.code;

                        CREATE OR REPLACE VIEW view_expense_summary_all AS
                        SELECT
                            COALESCE(ROUND(SUM(amount_usd)::numeric, 2)::FLOAT, 0.0) AS total,
                            COUNT(*)::INT AS count,
                            'USD' AS currency,
                            '$' AS currency_symbol,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', id,
                                        'description', description,
                                        'amount', amount,
                                        'currency', currency_code,
                                        'currency_symbol', currency_symbol,
                                        'amount_usd', amount_usd,
                                        'category', category,
                                        'category_id', category_id,
                                        'category_icon', category_icon,
                                        'category_color', category_color,
                                        'date', date
                                    ) ORDER BY date DESC, id DESC
                                ) FILTER (WHERE id IS NOT NULL),
                                '[]'::json
                            ) AS expenses
                        FROM view_expenses_detailed;

                        CREATE OR REPLACE VIEW view_expense_summary_daily AS
                        SELECT
                            date,
                            COALESCE(ROUND(SUM(amount_usd)::numeric, 2)::FLOAT, 0.0) AS total,
                            COUNT(*)::INT AS count,
                            'USD' AS currency,
                            '$' AS currency_symbol,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', id,
                                        'description', description,
                                        'amount', amount,
                                        'currency', currency_code,
                                        'currency_symbol', currency_symbol,
                                        'amount_usd', amount_usd,
                                        'category', category,
                                        'category_id', category_id,
                                        'category_icon', category_icon,
                                        'category_color', category_color,
                                        'date', date
                                    ) ORDER BY id DESC
                                ) FILTER (WHERE id IS NOT NULL),
                                '[]'::json
                            ) AS expenses
                        FROM view_expenses_detailed
                        GROUP BY date;

                        CREATE OR REPLACE VIEW view_expense_summary_weekly AS
                        SELECT
                            iso_year AS year,
                            iso_week AS week,
                            COALESCE(ROUND(SUM(amount_usd)::numeric, 2)::FLOAT, 0.0) AS total,
                            COUNT(*)::INT AS count,
                            'USD' AS currency,
                            '$' AS currency_symbol,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', id,
                                        'description', description,
                                        'amount', amount,
                                        'currency', currency_code,
                                        'currency_symbol', currency_symbol,
                                        'amount_usd', amount_usd,
                                        'category', category,
                                        'category_id', category_id,
                                        'category_icon', category_icon,
                                        'category_color', category_color,
                                        'date', date
                                    ) ORDER BY date ASC, id ASC
                                ) FILTER (WHERE id IS NOT NULL),
                                '[]'::json
                            ) AS expenses
                        FROM view_expenses_detailed
                        GROUP BY iso_year, iso_week;

                        CREATE OR REPLACE VIEW view_expense_summary_monthly AS
                        SELECT
                            year,
                            month,
                            COALESCE(ROUND(SUM(amount_usd)::numeric, 2)::FLOAT, 0.0) AS total,
                            COUNT(*)::INT AS count,
                            'USD' AS currency,
                            '$' AS currency_symbol,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', id,
                                        'description', description,
                                        'amount', amount,
                                        'currency', currency_code,
                                        'currency_symbol', currency_symbol,
                                        'amount_usd', amount_usd,
                                        'category', category,
                                        'category_id', category_id,
                                        'category_icon', category_icon,
                                        'category_color', category_color,
                                        'date', date
                                    ) ORDER BY date ASC, id ASC
                                ) FILTER (WHERE id IS NOT NULL),
                                '[]'::json
                            ) AS expenses
                        FROM view_expenses_detailed
                        GROUP BY year, month;

                        CREATE OR REPLACE VIEW view_expense_summary_yearly AS
                        SELECT
                            year,
                            COALESCE(ROUND(SUM(amount_usd)::numeric, 2)::FLOAT, 0.0) AS total,
                            COUNT(*)::INT AS count,
                            'USD' AS currency,
                            '$' AS currency_symbol,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', id,
                                        'description', description,
                                        'amount', amount,
                                        'currency', currency_code,
                                        'currency_symbol', currency_symbol,
                                        'amount_usd', amount_usd,
                                        'category', category,
                                        'category_id', category_id,
                                        'category_icon', category_icon,
                                        'category_color', category_color,
                                        'date', date
                                    ) ORDER BY date ASC, id ASC
                                ) FILTER (WHERE id IS NOT NULL),
                                '[]'::json
                            ) AS expenses
                        FROM view_expenses_detailed
                        GROUP BY year;

                        CREATE OR REPLACE VIEW view_expense_summary_category AS
                        SELECT
                            category_id,
                            category,
                            category_icon,
                            category_color,
                            category_is_active,
                            COALESCE(ROUND(SUM(amount_usd)::numeric, 2)::FLOAT, 0.0) AS total,
                            COUNT(*)::INT AS count,
                            'USD' AS currency,
                            '$' AS currency_symbol,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', id,
                                        'description', description,
                                        'amount', amount,
                                        'currency', currency_code,
                                        'currency_symbol', currency_symbol,
                                        'amount_usd', amount_usd,
                                        'category', category,
                                        'category_id', category_id,
                                        'category_icon', category_icon,
                                        'category_color', category_color,
                                        'date', date
                                    ) ORDER BY date DESC, id DESC
                                ) FILTER (WHERE id IS NOT NULL),
                                '[]'::json
                            ) AS expenses
                        FROM view_expenses_detailed
                        GROUP BY category_id, category, category_icon, category_color, category_is_active;

                        CREATE OR REPLACE VIEW view_expense_summary_monthly_category AS
                        SELECT
                            year,
                            month,
                            category_id,
                            category,
                            category_icon,
                            category_color,
                            COALESCE(ROUND(SUM(amount_usd)::numeric, 2)::FLOAT, 0.0) AS total,
                            COUNT(*)::INT AS count,
                            'USD' AS currency,
                            '$' AS currency_symbol,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', id,
                                        'description', description,
                                        'amount', amount,
                                        'currency', currency_code,
                                        'currency_symbol', currency_symbol,
                                        'amount_usd', amount_usd,
                                        'category', category,
                                        'category_id', category_id,
                                        'category_icon', category_icon,
                                        'category_color', category_color,
                                        'date', date
                                    ) ORDER BY date ASC, id ASC
                                ) FILTER (WHERE id IS NOT NULL),
                                '[]'::json
                            ) AS expenses
                        FROM view_expenses_detailed
                        GROUP BY year, month, category_id, category, category_icon, category_color;
                    """)

                    # 6. Combined Multi-Filter Parameterized Function
                    await cur.execute("""
                        CREATE OR REPLACE FUNCTION fn_expense_summary(
                            p_year INT DEFAULT NULL,
                            p_month INT DEFAULT NULL,
                            p_iso_week INT DEFAULT NULL,
                            p_start_date DATE DEFAULT NULL,
                            p_end_date DATE DEFAULT NULL,
                            p_categories TEXT[] DEFAULT NULL,
                            p_currency VARCHAR(3) DEFAULT 'USD'
                        )
                        RETURNS TABLE (
                            total FLOAT,
                            count INT,
                            currency VARCHAR(3),
                            currency_symbol VARCHAR(10),
                            expenses JSON
                        ) AS $$
                        DECLARE
                            v_symbol VARCHAR(10);
                            v_rate FLOAT;
                        BEGIN
                            SELECT s.symbol, s.exchange_rate::FLOAT INTO v_symbol, v_rate
                            FROM currency s WHERE s.code = p_currency;

                            IF v_symbol IS NULL THEN
                                v_symbol := '$';
                                v_rate := 1.0;
                            END IF;

                            RETURN QUERY
                            WITH filtered AS (
                                SELECT v.*
                                FROM view_expenses_detailed v
                                WHERE (p_year IS NULL OR v.year = p_year)
                                  AND (p_month IS NULL OR v.month = p_month)
                                  AND (p_iso_week IS NULL OR v.iso_week = p_iso_week)
                                  AND (p_start_date IS NULL OR v.date >= p_start_date)
                                  AND (p_end_date IS NULL OR v.date <= p_end_date)
                                  AND (
                                      p_categories IS NULL
                                      OR LOWER(v.category) = ANY(
                                          SELECT LOWER(TRIM(c)) FROM unnest(p_categories) c
                                      )
                                  )
                            )
                            SELECT
                                COALESCE(ROUND((SUM(f.amount_usd) * v_rate)::numeric, 2)::FLOAT, 0.0) AS total,
                                COUNT(f.id)::INT AS count,
                                p_currency AS currency,
                                v_symbol AS currency_symbol,
                                COALESCE(
                                    json_agg(
                                        json_build_object(
                                            'id', f.id,
                                            'description', f.description,
                                            'amount', f.amount,
                                            'currency', f.currency_code,
                                            'currency_symbol', f.currency_symbol,
                                            'amount_usd', f.amount_usd,
                                            'category', f.category,
                                            'category_id', f.category_id,
                                            'category_icon', f.category_icon,
                                            'category_color', f.category_color,
                                            'date', f.date
                                        ) ORDER BY f.date DESC, f.id DESC
                                    ) FILTER (WHERE f.id IS NOT NULL),
                                    '[]'::json
                                ) AS expenses
                            FROM filtered f;
                        END;
                        $$ LANGUAGE plpgsql STABLE;
                    """)

                await conn.commit()

            _pool = pool
            logger.info("PostgreSQL database, views, and functions successfully initialized.")
            return
        except Exception as e:
            logger.warning("Failed to connect to PostgreSQL on attempt %d: %s", attempt, e)
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Could not connect to PostgreSQL after %d attempts. Falling back to in-memory.", max_retries)


async def close_db():
    global _pool
    if _pool is not None:
        try:
            await _pool.close()
            logger.info("PostgreSQL connection pool closed.")
        except Exception as e:
            logger.warning("Error closing PostgreSQL pool: %s", e)
        finally:
            _pool = None


# ---------------------------------------------------------------------------
# Currency Operations
# ---------------------------------------------------------------------------

async def get_currencies() -> List[Currency]:
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT code, name, symbol, exchange_rate::FLOAT, is_default, updated_at
                    FROM currency
                    ORDER BY is_default DESC, code ASC
                """)
                rows = await cur.fetchall()
                return [
                    Currency(
                        code=r[0],
                        name=r[1],
                        symbol=r[2],
                        exchange_rate=float(r[3]),
                        is_default=r[4],
                        updated_at=r[5],
                    )
                    for r in rows
                ]
    return list(_currencies.values())


async def get_currency(code: str) -> Optional[Currency]:
    c_code = code.upper().strip()
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT code, name, symbol, exchange_rate::FLOAT, is_default, updated_at FROM currency WHERE code = %s",
                    (c_code,),
                )
                row = await cur.fetchone()
                if row:
                    return Currency(
                        code=row[0],
                        name=row[1],
                        symbol=row[2],
                        exchange_rate=float(row[3]),
                        is_default=row[4],
                        updated_at=row[5],
                    )
                return None
    return _currencies.get(c_code)


async def update_currency_rates(rates: Dict[str, float]) -> List[Currency]:
    """
    Updates exchange rates for currencies present in the database.
    """
    now = datetime.now()
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                for code, rate in rates.items():
                    if rate > 0:
                        await cur.execute(
                            """
                            UPDATE currency
                            SET exchange_rate = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE code = %s
                            """,
                            (rate, code.upper().strip()),
                        )
            await conn.commit()
        return await get_currencies()

    for code, rate in rates.items():
        c_code = code.upper().strip()
        if c_code in _currencies and rate > 0:
            _currencies[c_code].exchange_rate = float(rate)
            _currencies[c_code].updated_at = now
    return list(_currencies.values())


# ---------------------------------------------------------------------------
# Category Operations
# ---------------------------------------------------------------------------

async def get_categories(active_only: bool = True) -> List[Category]:
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                if active_only:
                    await cur.execute("SELECT id, name, icon, color, is_active FROM category WHERE is_active = TRUE ORDER BY id ASC")
                else:
                    await cur.execute("SELECT id, name, icon, color, is_active FROM category ORDER BY id ASC")
                rows = await cur.fetchall()
                return [
                    Category(
                        id=r[0],
                        name=r[1],
                        icon=r[2],
                        color=r[3],
                        is_active=r[4],
                    )
                    for r in rows
                ]
    return [c for c in _categories if not active_only or c.is_active]


async def get_category_by_id(category_id: int) -> Optional[Category]:
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, name, icon, color, is_active FROM category WHERE id = %s",
                    (category_id,),
                )
                r = await cur.fetchone()
                if r:
                    return Category(id=r[0], name=r[1], icon=r[2], color=r[3], is_active=r[4])
                return None
    for c in _categories:
        if c.id == category_id:
            return c
    return None


async def get_category_by_name(name: str) -> Optional[Category]:
    clean = name.strip()
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, name, icon, color, is_active FROM category WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) LIMIT 1",
                    (clean,),
                )
                r = await cur.fetchone()
                if r:
                    return Category(id=r[0], name=r[1], icon=r[2], color=r[3], is_active=r[4])
                return None
    for c in _categories:
        if c.name.strip().lower() == clean.lower():
            return c
    return None


async def create_category(data: CategoryCreate) -> Category:
    global _next_category_id
    clean_name = data.name.strip()
    icon = data.icon or "help-circle"
    color = data.color or "#607D8B"

    existing = await get_category_by_name(clean_name)
    if existing is not None:
        raise ValueError(f"Category '{clean_name}' already exists.")

    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO category (name, icon, color)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, icon, color, is_active
                    """,
                    (clean_name, icon, color),
                )
                r = await cur.fetchone()
            await conn.commit()
            return Category(id=r[0], name=r[1], icon=r[2], color=r[3], is_active=r[4])

    new_cat = Category(
        id=_next_category_id,
        name=clean_name,
        icon=icon,
        color=color,
        is_active=True,
    )
    _categories.append(new_cat)
    _next_category_id += 1
    return new_cat


async def delete_category(category_id: int) -> bool:
    """Soft-delete a category by setting is_active = FALSE."""
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE category SET is_active = FALSE WHERE id = %s RETURNING id",
                    (category_id,),
                )
                r = await cur.fetchone()
            await conn.commit()
            return r is not None

    for c in _categories:
        if c.id == category_id:
            c.is_active = False
            return True
    return False


async def activate_category(category_id: int) -> bool:
    """Reactivate a category by setting is_active = TRUE."""
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE category SET is_active = TRUE WHERE id = %s RETURNING id",
                    (category_id,),
                )
                r = await cur.fetchone()
            await conn.commit()
            return r is not None

    for c in _categories:
        if c.id == category_id:
            c.is_active = True
            return True
    return False


async def resolve_category(name_or_id: str) -> Category:
    """
    Resolves category from either numeric ID string or category name.
    If category does not exist, it is auto-created for backward compatibility.
    """
    clean = str(name_or_id).strip()
    if clean.isdigit():
        cat = await get_category_by_id(int(clean))
        if cat:
            return cat

    cat = await get_category_by_name(clean)
    if cat:
        return cat

    # Auto-create unknown category with defaults
    return await create_category(CategoryCreate(name=clean))


# ---------------------------------------------------------------------------
# Expense Operations
# ---------------------------------------------------------------------------

def _row_to_expense(row) -> Expense:
    return Expense(
        id=row[0],
        description=row[1],
        amount=round(float(row[2]), 2),
        currency=row[3],
        currency_symbol=row[4],
        amount_usd=round(float(row[5]), 2) if row[5] is not None else None,
        category=row[6],
        category_id=row[7],
        category_icon=row[8],
        category_color=row[9],
        date=row[10],
    )


async def get_all() -> List[Expense]:
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, description, amount, currency_code, currency_symbol, amount_usd,
                           category, category_id, category_icon, category_color, date
                    FROM view_expenses_detailed
                    ORDER BY date DESC, id DESC
                """)
                rows = await cur.fetchall()
                return [_row_to_expense(r) for r in rows]
    return list(_expenses)


async def get_expense(expense_id: int) -> Optional[Expense]:
    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, description, amount, currency_code, currency_symbol, amount_usd,
                           category, category_id, category_icon, category_color, date
                    FROM view_expenses_detailed
                    WHERE id = %s
                """, (expense_id,))
                r = await cur.fetchone()
                if r:
                    return _row_to_expense(r)
                return None

    for exp in _expenses:
        if exp.id == expense_id:
            return exp
    return None


async def add(expense: ExpenseCreate) -> Expense:
    global _next_id

    # 1. Resolve Category
    category_obj = await resolve_category(expense.category)

    # 2. Resolve Currency
    curr_code = (expense.currency or "USD").upper().strip()
    curr = await get_currency(curr_code)
    if not curr:
        curr = DEFAULT_CURRENCIES["USD"]
        curr_code = "USD"

    amount_usd = round(expense.amount / curr.exchange_rate, 2)

    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO expenses (description, amount, currency_code, category_id, date)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (expense.description, expense.amount, curr.code, category_obj.id, expense.date),
                )
                row = await cur.fetchone()
                new_id = row[0]

                await cur.execute("""
                    SELECT id, description, amount, currency_code, currency_symbol, amount_usd,
                           category, category_id, category_icon, category_color, date
                    FROM view_expenses_detailed
                    WHERE id = %s
                """, (new_id,))
                detail_row = await cur.fetchone()
            await conn.commit()
            return _row_to_expense(detail_row)

    new_expense = Expense(
        id=_next_id,
        description=expense.description,
        amount=round(float(expense.amount), 2),
        currency=curr.code,
        currency_symbol=curr.symbol,
        amount_usd=amount_usd,
        category=category_obj.name,
        category_id=category_obj.id,
        category_icon=category_obj.icon,
        category_color=category_obj.color,
        date=expense.date,
    )
    _expenses.append(new_expense)
    _next_id += 1
    return new_expense


async def update(expense_id: int, expense: ExpenseCreate) -> Optional[Expense]:
    # 1. Resolve Category
    category_obj = await resolve_category(expense.category)

    # 2. Resolve Currency
    curr_code = (expense.currency or "USD").upper().strip()
    curr = await get_currency(curr_code)
    if not curr:
        curr = DEFAULT_CURRENCIES["USD"]
        curr_code = "USD"

    amount_usd = round(expense.amount / curr.exchange_rate, 2)

    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE expenses
                    SET description = %s, amount = %s, currency_code = %s, category_id = %s, date = %s
                    WHERE id = %s
                    RETURNING id
                    """,
                    (expense.description, expense.amount, curr.code, category_obj.id, expense.date, expense_id),
                )
                row = await cur.fetchone()
                if not row:
                    return None

                await cur.execute("""
                    SELECT id, description, amount, currency_code, currency_symbol, amount_usd,
                           category, category_id, category_icon, category_color, date
                    FROM view_expenses_detailed
                    WHERE id = %s
                """, (expense_id,))
                detail_row = await cur.fetchone()
            await conn.commit()
            return _row_to_expense(detail_row)

    for i, exp in enumerate(_expenses):
        if exp.id == expense_id:
            updated = Expense(
                id=expense_id,
                description=expense.description,
                amount=round(float(expense.amount), 2),
                currency=curr.code,
                currency_symbol=curr.symbol,
                amount_usd=amount_usd,
                category=category_obj.name,
                category_id=category_obj.id,
                category_icon=category_obj.icon,
                category_color=category_obj.color,
                date=expense.date,
            )
            _expenses[i] = updated
            return updated
    return None


async def delete(expense_id: int) -> Optional[Expense]:
    existing = await get_expense(expense_id)
    if existing is None:
        return None

    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
            await conn.commit()
        return existing

    for i, exp in enumerate(_expenses):
        if exp.id == expense_id:
            return _expenses.pop(i)
    return None


# ---------------------------------------------------------------------------
# High Performance Aggregated Summary Queries & Views
# ---------------------------------------------------------------------------

async def get_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    week: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    categories: Optional[List[str]] = None,
    currency: str = "USD",
) -> ExpenseSummary:
    """
    Computes an aggregated ExpenseSummary using PostgreSQL parameterized fn_expense_summary
    or in-memory filtering fallback.
    """
    target_currency = (currency or "USD").upper().strip()

    if _pool is not None:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT total, count, currency, currency_symbol, expenses
                    FROM fn_expense_summary(
                        p_year => %s,
                        p_month => %s,
                        p_iso_week => %s,
                        p_start_date => %s,
                        p_end_date => %s,
                        p_categories => %s,
                        p_currency => %s
                    )
                    """,
                    (year, month, week, start_date, end_date, categories, target_currency),
                )
                row = await cur.fetchone()
                if row:
                    total = float(row[0])
                    count = int(row[1])
                    curr_code = row[2]
                    curr_sym = row[3]
                    exp_data = row[4]
                    if isinstance(exp_data, str):
                        exp_data = json.loads(exp_data)
                    expenses_list = [
                        Expense(
                            id=item["id"],
                            description=item["description"],
                            amount=float(item["amount"]),
                            currency=item.get("currency", "USD"),
                            currency_symbol=item.get("currency_symbol", "$"),
                            amount_usd=float(item.get("amount_usd", item["amount"])),
                            category=item["category"],
                            category_id=item.get("category_id"),
                            category_icon=item.get("category_icon"),
                            category_color=item.get("category_color"),
                            date=item["date"] if isinstance(item["date"], date) else date.fromisoformat(item["date"]),
                        )
                        for item in exp_data
                    ]
                    return ExpenseSummary(
                        total=total,
                        count=count,
                        currency=curr_code,
                        currency_symbol=curr_sym,
                        expenses=expenses_list,
                    )

    # In-memory fallback
    curr_obj = _currencies.get(target_currency, DEFAULT_CURRENCIES["USD"])
    rate = curr_obj.exchange_rate

    filtered = list(_expenses)

    if year is not None:
        if week is not None:
            filtered = [e for e in filtered if e.date.isocalendar().year == year and e.date.isocalendar().week == week]
        elif month is not None:
            filtered = [e for e in filtered if e.date.year == year and e.date.month == month]
        else:
            filtered = [e for e in filtered if e.date.year == year]
    elif week is not None:
        filtered = [e for e in filtered if e.date.isocalendar().week == week]
    elif month is not None:
        filtered = [e for e in filtered if e.date.month == month]

    if start_date is not None:
        filtered = [e for e in filtered if e.date >= start_date]
    if end_date is not None:
        filtered = [e for e in filtered if e.date <= end_date]

    if categories:
        cat_lowers = {c.strip().lower() for c in categories if c.strip()}
        filtered = [e for e in filtered if e.category.strip().lower() in cat_lowers]

    if month is not None or week is not None:
        filtered = sorted(filtered, key=lambda e: (e.date, e.id))

    # Calculate total in base USD and convert to target currency
    total_usd = sum(e.amount_usd if e.amount_usd is not None else e.amount for e in filtered)
    total_in_currency = round(total_usd * rate, 2)

    return ExpenseSummary(
        total=total_in_currency,
        count=len(filtered),
        currency=curr_obj.code,
        currency_symbol=curr_obj.symbol,
        expenses=filtered,
    )
