"""
Запуск:
    python main.py           # обычный запуск
    python main.py --pages 5 # указать количество страниц для парсинга книг
    python main.py --stats   # только показать статистику БД
"""

import argparse
import sys
import os

# Добавляем корневую папку в путь чтобы импорты работали
sys.path.insert(0, os.path.dirname(__file__))

from extract.source_api import extract as extract_fakestore
from extract.source_scraper import extract as extract_books
from transform.transformer import transform
from load.loader import load, query_stats


def run_etl(book_pages: int = 3):
    """Запускает полный цикл ETL."""
    print("\n" + "-"*50)
    print(" ЗАПУСК ETL-ПРОЦЕССА")
    print("-"*50 + "\n")

    # EXTRACT
    print("ЭТАП 1: EXTRACT (Извлечение данных)\n")
    try:
        fakestore_raw = extract_fakestore()
    except Exception as e:
        print(f"❌ FakeStore API недоступен: {e}")
        fakestore_raw = []

    try:
        books_raw = extract_books(max_pages=book_pages)
    except Exception as e:
        print(f"❌ Books парсер недоступен: {e}")
        books_raw = []

    if not fakestore_raw and not books_raw:
        print("❌ Оба источника недоступны. Прерываем ETL.")
        return

    # TRANSFORM 
    print("\nЭТАП 2: TRANSFORM (Нормализация данных)\n")
    unified_items = transform(fakestore_raw, books_raw)

    # LOAD 
    print("\nЭТАП 3: LOAD (Загрузка в базу данных)\n")
    load(unified_items)

    # Итоговая статистика
    query_stats()

    print("ETL-процесс успешно завершён!\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск ETL")
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Количество страниц для парсинга books.toscrape.com (по умолчанию: 3)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Показать только статистику БД без запуска ETL"
    )
    args = parser.parse_args()

    if args.stats:
        query_stats()
    else:
        pages = max(1, args.pages)
        if pages != args.pages:
            print("❌ --pages должен быть >= 1. Используем значение 1.")
        run_etl(book_pages=pages)
