"""
routes/items.py — эндпоинты для работы с товарами.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db, Item, ItemEvent
from app.schemas import ItemCreate, ItemUpdate, ItemPatch, ItemOut

router = APIRouter(prefix="/items", tags=["items"])


# GET /items/
# Запрос:  GET http://127.0.0.1:8000/items/
# Запрос с фильтрами: GET http://127.0.0.1:8000/items/?category=books&in_stock=true
# Ответ:
# [
#     {"id": 1, "title": "Fjallraven Backpack", "price": 109.95, "category": "men's clothing", ...},
#     {"id": 2, "title": "Harry Potter",        "price": 65.75,  "category": "books", ...}
# ]

@router.get("/", response_model=list[ItemOut])
def get_items(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    source:   Optional[str] = Query(None, description="Фильтр по источнику"),
    in_stock: Optional[bool] = Query(None, description="Только в наличии"),
    limit:    int = Query(50, le=500),
    offset:   int = Query(0),
    db: Session = Depends(get_db)
):
    q = db.query(Item)
    if category:
        q = q.filter(Item.category == category)
    if source:
        q = q.filter(Item.source == source)
    if in_stock is not None:
        q = q.filter(Item.in_stock == (1 if in_stock else 0))
    return q.offset(offset).limit(limit).all()
 
 
# GET /items/search?q=...
# Запрос:  GET http://127.0.0.1:8000/items/search?q=harry
# Ответ:
# [
#     {"id": 3, "title": "Harry Potter", "price": 65.75, ...}
# ]

@router.get("/search", response_model=list[ItemOut])
def search_items(
    q: str = Query(..., min_length=1, description="Поиск по названию"),
    db: Session = Depends(get_db)
):
    return db.query(Item).filter(Item.title.ilike(f"%{q}%")).limit(50).all()
 
 
# GET /items/stats
# Запрос:  GET http://127.0.0.1:8000/items/stats
# Ответ:
# {
#     "total": 80,
#     "by_source":   {"fakestore": 20, "books": 60},
#     "by_category": {"books": 60, "men's clothing": 10, ...}
# }

@router.get("/stats", response_model=dict)
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(func.count(Item.id)).scalar()
    by_source = db.query(Item.source, func.count(Item.id)).group_by(Item.source).all()
    by_category = db.query(Item.category, func.count(Item.id)).group_by(Item.category).all()
    return {
        "total": total,
        "by_source": {s: c for s, c in by_source},
        "by_category": {cat: c for cat, c in by_category},
    }
 
 
# GET /items/{id}
# Запрос:  GET http://127.0.0.1:8000/items/1
# Ответ:
# {"id": 1, "title": "Fjallraven Backpack", "price": 109.95, ...}
#
# Если id не существует:
# {"detail": "Item not found"}  — статус 404

@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
 
 
# POST /items/
# Запрос:  POST http://127.0.0.1:8000/items/
# Тело:    {"title": "New Item", "price": 9.99, "source": "manual"}
# Ответ:
# {"id": 81, "title": "New Item", "price": 9.99, "source": "manual", ...}

@router.post("/", response_model=ItemOut, status_code=201)
def create_item(data: ItemCreate, db: Session = Depends(get_db)):
    from datetime import datetime
    item = Item(**data.model_dump(), loaded_at=datetime.now().isoformat())
    db.add(item)
    db.flush()
    db.add(ItemEvent(item_id=item.id, event_type="created"))
    db.commit()
    db.refresh(item)
    return item
 
 
# PUT /items/{id}
# Запрос:  PUT http://127.0.0.1:8000/items/1
# Тело:    {"title": "Updated Item", "price": 19.99, "source": "manual", "in_stock": true}
# Ответ:
# {"id": 1, "title": "Updated Item", "price": 19.99, ...}
#
# Если id не существует:
# {"detail": "Item not found"}  — статус 404

@router.put("/{item_id}", response_model=ItemOut)
def replace_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in data.model_dump().items():
        setattr(item, field, value)
    db.add(ItemEvent(item_id=item.id, event_type="updated", note="full replace"))
    db.commit()
    db.refresh(item)
    return item
 
 
# PATCH /items/{id}
# Запрос:  PATCH http://127.0.0.1:8000/items/1
# Тело:    {"price": 49.99}         — только те поля которые нужно изменить
# Ответ:
# {"id": 1, "title": "Fjallraven Backpack", "price": 49.99, ...}
#
# Если id не существует:
# {"detail": "Item not found"}  — статус 404

@router.patch("/{item_id}", response_model=ItemOut)
def patch_item(item_id: int, data: ItemPatch, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.add(ItemEvent(item_id=item.id, event_type="updated", note="partial update"))
    db.commit()
    db.refresh(item)
    return item
 
 
# DELETE /items/{id}
# Запрос:  DELETE http://127.0.0.1:8000/items/1
# Ответ:   пустой ответ — статус 204 (No Content)
#
# Если id не существует:
# {"detail": "Item not found"}  — статус 404
@router.delete("/{item_id}", status_code=204)

def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.add(ItemEvent(item_id=item.id, event_type="deleted"))
    db.commit()
    db.delete(item)
    db.commit()
 