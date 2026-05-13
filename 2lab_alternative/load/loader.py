"""
Load: Загрузка нормализованных данных в базу данных SQLite.
Создаёт таблицу items и записывает все товары.
При повторном запуске обновляет существующие записи.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'shop.db')


def get_connection() -> sqlite3.Connection:
    """Создаёт подключение к SQLite базе данных."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # чтобы можно было обращаться по имени колонки
    return conn


def create_tables(conn: sqlite3.Connection):
    """Создаёт таблицы если их ещё нет."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            price       REAL,
            category    TEXT,
            rating      REAL,
            in_stock    INTEGER,   -- 0/1
            source      TEXT NOT NULL,
            source_url  TEXT,
            loaded_at   TEXT NOT NULL   -- дата загрузки
        )
    """)

    # Таблица для хранения истории запусков ETL
    conn.execute("""
        CREATE TABLE IF NOT EXISTS etl_runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at       TEXT NOT NULL,
            items_loaded INTEGER,
            status       TEXT
        )
    """)

    conn.commit()


def load(items: list[dict]) -> int:
    """
    Загружает список товаров в базу данных.
    Возвращает количество загруженных записей.
    """
    print(f"[Load] Загружаем {len(items)} записей в {DB_PATH}...")

    conn = get_connection()
    create_tables(conn)

    loaded_count = 0
    timestamp = datetime.now().isoformat()

    for item in items:
        # Проверяем, есть ли уже такой товар (по title + source)
        existing = conn.execute(
            "SELECT id FROM items WHERE title = ? AND source = ?",
            (item['title'], item['source'])
        ).fetchone()

        if existing:
            # Обновляем существующую запись
            conn.execute("""
                UPDATE items SET
                    price = ?, category = ?, rating = ?,
                    in_stock = ?, source_url = ?, loaded_at = ?
                WHERE id = ?
            """, (
                item['price'], item['category'], item['rating'],
                1 if item['in_stock'] else 0,
                item['source_url'], timestamp,
                existing['id']
            ))
        else:
            # Вставляем новую запись
            conn.execute("""
                INSERT INTO items (title, price, category, rating, in_stock, source, source_url, loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['title'], item['price'], item['category'],
                item['rating'], 1 if item['in_stock'] else 0,
                item['source'], item['source_url'], timestamp
            ))
            loaded_count += 1

    # Записываем информацию о запуске
    conn.execute(
        "INSERT INTO etl_runs (run_at, items_loaded, status) VALUES (?, ?, ?)",
        (timestamp, loaded_count, 'success')
    )

    conn.commit()
    conn.close()

    print(f"[Load] Готово! Новых записей: {loaded_count}. База данных: {DB_PATH}")
    return loaded_count


def query_stats():
    """Выводит статистику по загруженным данным (для проверки)."""
    conn = get_connection()
    create_tables(conn)

    total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    by_source = conn.execute(
        "SELECT source, COUNT(*) as cnt, ROUND(AVG(price), 2) as avg_price FROM items GROUP BY source"
    ).fetchall()
    by_category = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM items GROUP BY category ORDER BY cnt DESC LIMIT 5"
    ).fetchall()

    conn.close()

    print(f"\n{'='*50}")
    print(f"  СТАТИСТИКА БАЗЫ ДАННЫХ")
    print(f"{'='*50}")
    print(f"  Всего товаров: {total}")
    print(f"\n  По источникам:")
    for row in by_source:
        print(f"    {row['source']:15} — {row['cnt']} товаров, средняя цена: ${row['avg_price']}")
    print(f"\n  Топ категорий:")
    for row in by_category:
        print(f"    {row['category']:20} — {row['cnt']} товаров")
    print(f"{'='*50}\n")
