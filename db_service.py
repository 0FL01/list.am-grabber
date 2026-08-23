import sqlite3
from pathlib import Path

from models import Item, RentalListing


class SQLiteDBHandler:
    """Работа с БД sqlite"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SQLiteDBHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_name="database.db"):
        if not hasattr(self, "_initialized"):
            self.db_name = db_name
            self._create_table()
            self._initialized = True

    def _create_table(self):
        """Создает таблицу viewed, если она не существует."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS viewed (
                    id INTEGER,
                    price INTEGER
                )
                """
            )
            conn.commit()

    def add_record(self, ad: Item):
        """Добавляет новую запись в таблицу viewed."""

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO viewed (id, price) VALUES (?, ?)",
                (ad.id, ad.priceDetailed.value),
            )
            conn.commit()

    def add_record_from_page(self, ads: list[Item]):
        """Добавляет несколько записей в таблицу viewed."""
        records = [(ad.id, ad.priceDetailed.value) for ad in ads]

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO viewed (id, price)
                VALUES (?, ?)
                """,
                records,
            )
            conn.commit()

    def record_exists(self, record_id, price):
        """Проверяет, существует ли запись с заданными id и price."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM viewed WHERE id = ? AND price = ?",
                (record_id, price),
            )
            return cursor.fetchone() is not None


class ListingStateStore:
    _BASELINE_MARKER = "__baseline__"

    def __init__(self, db_name: str):
        self.db_name = db_name
        Path(db_name).parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    def _create_table(self) -> None:
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS listing_state (
                    listing_id TEXT PRIMARY KEY,
                    price_key TEXT NOT NULL
                )
                """
            )

    def is_initialized(self) -> bool:
        return self.get_price_key(self._BASELINE_MARKER) is not None

    def initialize(self, listings: list[RentalListing]) -> None:
        records = [(listing.id, listing.price_key) for listing in listings]
        records.append((self._BASELINE_MARKER, "1"))
        with sqlite3.connect(self.db_name) as conn:
            conn.executemany(
                """
                INSERT INTO listing_state (listing_id, price_key)
                VALUES (?, ?)
                ON CONFLICT(listing_id) DO UPDATE SET price_key = excluded.price_key
                """,
                records,
            )

    def get_price_key(self, listing_id: str) -> str | None:
        with sqlite3.connect(self.db_name) as conn:
            row = conn.execute(
                "SELECT price_key FROM listing_state WHERE listing_id = ?",
                (listing_id,),
            ).fetchone()
        return row[0] if row else None

    def save(self, listing: RentalListing) -> None:
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(
                """
                INSERT INTO listing_state (listing_id, price_key)
                VALUES (?, ?)
                ON CONFLICT(listing_id) DO UPDATE SET price_key = excluded.price_key
                """,
                (listing.id, listing.price_key),
            )
