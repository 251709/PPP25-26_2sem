"""
Extract: Источник 1 — fakestoreapi.com (REST API)
Получаем товары через HTTP GET запрос, сохраняем сырые данные в JSON.
"""

import requests
import json
import os
import time
from datetime import datetime

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
MAX_RETRIES = 3
RETRY_DELAY = 3  # секунды между попытками


def get_raw_dir() -> str:
    """Создаёт папку для raw-данных и возвращает путь к ней"""
    os.makedirs(RAW_DIR, exist_ok=True)
    return RAW_DIR


def http_get_with_retry(url: str, timeout: int = 10) -> requests.Response:
    """GET с повторными попытками"""
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


def extract() -> list[dict]:
    """Загружает товары с fakestoreapi.com и сохраняет сырые данные"""
    print("[Extract] Загрузка данных с fakestoreapi.com...")

    url = "https://fakestoreapi.com/products"
    response = http_get_with_retry(url, timeout=10)

    raw_data = response.json()

    # Сохраняем сырые данные (raw data)
    raw_dir = get_raw_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(raw_dir, f"fakestore_{timestamp}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    print(f"[Extract] Получено {len(raw_data)} товаров. Сохранено в {filepath}")
    return raw_data


if __name__ == "__main__":
    data = extract()
    print(data[0])  # Пример первого товара
