"""
routes/events.py — эндпоинты для работы с логом событий.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db, Item, ItemEvent
from app.schemas import EventCreate, EventOut

router = APIRouter(prefix="/items/{item_id}/events", tags=["events"])


# GET /items/{id}/events
# Запрос:  GET http://127.0.0.1:8000/items/1/events
# Ответ:
# [
#     {"id": 1, "item_id": 1, "event_type": "created", "note": null, "created_at": "2026-05-10T12:00:00"},
#     {"id": 2, "item_id": 1, "event_type": "updated", "note": "partial update", "created_at": "2026-05-10T13:00:00"}
# ]
#
# Если item_id не существует:
# {"detail": "Item not found"}  — статус 404

@router.get("/", response_model=list[EventOut])
def get_events(item_id: int, db: Session = Depends(get_db)):
    if not db.get(Item, item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return db.query(ItemEvent).filter(ItemEvent.item_id == item_id).all()
 
 
# POST /items/{id}/events
# Запрос:  POST http://127.0.0.1:8000/items/1/events
# Тело:    {"event_type": "reviewed", "note": "проверено вручную"}
# Ответ:
# {"id": 3, "item_id": 1, "event_type": "reviewed", "note": "проверено вручную", "created_at": "2026-05-10T14:00:00"}
#
# Если item_id не существует:
# {"detail": "Item not found"}  — статус 404

@router.post("/", response_model=EventOut, status_code=201)
def create_event(item_id: int, data: EventCreate, db: Session = Depends(get_db)):
    if not db.get(Item, item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    event = ItemEvent(item_id=item_id, **data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
 