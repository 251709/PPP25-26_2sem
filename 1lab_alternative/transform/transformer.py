"""
Transform: Нормализация и очистка данных из обоих источников.

Задача: привести разные форматы к единой схеме:
    title       — название товара (строка)
    price       — цена в USD (число с плавающей точкой)
    category    — категория товара (строка, нижний регистр)
    rating      — рейтинг от 1 до 5 (число или None)
    in_stock    — есть ли в наличии (True/False)
    source      — откуда данные ('fakestore' или 'books')
    source_url  — ссылка на товар (строка или None)
"""

import re

# Курс фунта к доллару
GBP_TO_USD = 1.27

RATING_MAP = {
    "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5
}


def clean_string(s: str) -> str:
    """Убирает лишние пробелы и непечатаемые символы"""
    return re.sub(r'\s+', ' ', s).strip()


def parse_gbp_price(price_raw: str) -> float | None:
    """Парсит цену вида 'Â£51.77'. Возвращает цену в USD"""
    # Убираем всё кроме цифр и точки
    cleaned = re.sub(r'[^\d.]', '', price_raw)
    try:
        gbp = float(cleaned)
        return round(gbp * GBP_TO_USD, 2)
    except ValueError:
        return None


def transform_fakestore(raw_items: list[dict]) -> list[dict]:
    """Нормализует данные из fakestoreapi.com"""
    print(f"[Transform] FakeStore: обрабатываем {len(raw_items)} записей...")
    result = []
    duplicates = set()

    for item in raw_items:
        title = clean_string(item.get('title', ''))

        # Пропускаем дубликаты по названию
        if title.lower() in duplicates:
            continue
        duplicates.add(title.lower())

        # Цена уже в fakestore указана в USD, просто округляем
        try:
            price = round(float(item.get('price', 0)), 2)
        except (TypeError, ValueError):
            price = None

        # Рейтинг: у fakestore это объект {"rate": 3.9, "count": 120}
        rating_data = item.get('rating', {})
        try:
            rating = round(float(rating_data.get('rate', 0)), 1)
        except (TypeError, ValueError):
            rating = None

        result.append({
            "title": title,
            "price": price,
            "category": clean_string(item.get('category', 'unknown')).lower(),
            "rating": rating,
            "in_stock": True,  # Предположим в рамках задания
            "source": "fakestore",
            "source_url": None
        })

    print(f"[Transform] FakeStore: после очистки {len(result)} записей")
    return result


def transform_books(raw_items: list[dict]) -> list[dict]:
    """Нормализует данные с books.toscrape.com"""
    print(f"[Transform] Books: обрабатываем {len(raw_items)} записей...")
    result = []
    duplicates = set()

    for item in raw_items:
        title = clean_string(item.get('title', ''))

        if title.lower() in duplicates:
            continue
        duplicates.add(title.lower())

        price = parse_gbp_price(item.get('price_raw', ''))

        # Рейтинг: текст "Three" -> число 3
        rating_raw = item.get('rating_raw', '')
        rating = RATING_MAP.get(rating_raw, None)

        # Наличие
        availability_text = item.get('availability', '').lower()
        in_stock = 'in stock' in availability_text

        result.append({
            "title": title,
            "price": price,
            "category": "books",        # на сайте нет категорий на главной
            "rating": float(rating) if rating else None,
            "in_stock": in_stock,
            "source": "books",
            "source_url": item.get('url', None)
        })

    print(f"[Transform] Books: после очистки {len(result)} записей")
    return result


def transform(fakestore_raw: list[dict], books_raw: list[dict]) -> list[dict]:
    """
    Объединяет данные из двух источников в единый список.
    Это финальный результат трансформации.
    """
    fakestore_items = transform_fakestore(fakestore_raw)
    books_items = transform_books(books_raw)

    combined = fakestore_items + books_items
    print(f"[Transform] Итого объединено: {len(combined)} записей")
    return combined


if __name__ == "__main__":
    import json
    import os
    import sys

    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from extract.source_api import extract as extract_fakestore
    from extract.source_scraper import extract as extract_books

    print("[Demo] Парсим FakeStore и 1 страницу books, затем трансформируем...")

    try:
        fakestore_raw = extract_fakestore()
    except Exception as e:
        print(f"[Demo] ❌ FakeStore недоступен: {e}")
        fakestore_raw = []

    try:
        books_raw = extract_books(max_pages=1)
    except Exception as e:
        print(f"[Demo] ❌ Books недоступен: {e}")
        books_raw = []

    if not fakestore_raw and not books_raw:
        print("[Demo] ❌ Оба источника недоступны.")
        raise SystemExit(1)

    transformed = transform(fakestore_raw, books_raw)

    print(f"[Demo] Готово. Получено нормализованных записей: {len(transformed)}")
    print("[Demo] Первые и последние 2 записи:")
    data_print = transformed[:2] + transformed[-2:]
    print(json.dumps(data_print, ensure_ascii=False, indent=2))

