"""
Extract: Источник 2 — books.toscrape.com (HTML-парсинг)
Парсим страницы сайта с помощью BeautifulSoup, сохраняем сырые данные в JSON.
"""

import requests
import json
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
BASE_URL = "http://books.toscrape.com/catalogue/"
MAX_RETRIES = 3
RETRY_DELAY = 3  # секунда между попытками


def get_raw_dir() -> str:
    """Создаёт папку для raw-данных и возвращает путь к ней"""
    os.makedirs(RAW_DIR, exist_ok=True)
    return RAW_DIR


def http_get_with_retry(url: str, timeout: int = 10) -> requests.Response:
    """GET с повторными попытками."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == MAX_RETRIES:
                raise
            print(f"[Extract] ❌ Попытка {attempt} не удалась: {type(e).__name__}. Повторяем...")
            time.sleep(RETRY_DELAY)


def extract(max_pages: int = 3) -> list[dict]:
    """
    Парсит страницы books.toscrape.com и возвращает список книг.
    max_pages — сколько страниц загрузить (на каждой 20 книг)
    """
    print(f"[Extract] Парсинг books.toscrape.com (страниц: {max_pages})...")
    all_books = []

    for page_num in range(1, max_pages + 1):
        url = f"{BASE_URL}page-{page_num}.html"

        response = http_get_with_retry(url, timeout=10)

        soup = BeautifulSoup(response.text, 'html.parser')
        books_on_page = soup.select('article.product_pod')

        # ПРИМЕР
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>...</head>
        <body>
        <article class="product_pod">
            <p class="star-rating Three"></p>
            <h3><a title="A Light in the Attic" href="a-light-in-the-attic_1000/index.html">...</a></h3>
            <p class="price_color">£51.77</p>
            <p class="instock availability">In stock</p>
        </article>
        </body>
        </html>
        """
        for book in books_on_page:
            # Извлекаем данные 
            title = book.h3.a['title']
            price_raw = book.select_one('.price_color').text.strip()
            rating_class = book.select_one('.star-rating')['class'][1]
            availability = book.select_one('.availability').text.strip()
            link = BASE_URL + book.h3.a['href'].replace('../', '')

            all_books.append({
                "title": title,
                "price_raw": price_raw,     # например "£51.77"
                "rating_raw": rating_class,  # например "Three"
                "availability": availability,
                "url": link,
                "page": page_num
            })

        print(f"[Extract] Страница {page_num}: {len(books_on_page)} книг")

    # Сохраняем сырые данные
    raw_dir = get_raw_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(raw_dir, f"books_{timestamp}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_books, f, ensure_ascii=False, indent=2)

    print(f"[Extract] Всего книг: {len(all_books)}. Сохранено в {filepath}")
    return all_books


if __name__ == "__main__":
    data = extract(max_pages=3)
    print(data[0])
