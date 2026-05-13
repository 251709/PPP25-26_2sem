"""
routes/sources.py — эндпоинты для работы с источниками данных.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db, Source
from app.schemas import SourceCreate, SourceUpdate, SourceOut

router = APIRouter(prefix="/sources", tags=["sources"])


# GET /sources/
# Запрос:  GET http://127.0.0.1:8000/sources/
# Ответ:
# [
#     {"id": 1, "name": "fakestore", "url": null, "active": true},
#     {"id": 2, "name": "books",     "url": null, "active": true}
# ]

@router.get("/", response_model=list[SourceOut])
def get_sources(db: Session = Depends(get_db)):
    return db.query(Source).all()
 
 
# GET /sources/{id}
# Запрос:  GET http://127.0.0.1:8000/sources/1
# Ответ:
# {"id": 1, "name": "fakestore", "url": null, "active": true}
#
# Если id не существует:
# {"detail": "Source not found"}  — статус 404

@router.get("/{source_id}", response_model=SourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source
 
 
# POST /sources/
# Запрос:  POST http://127.0.0.1:8000/sources/
# Тело:    {"name": "newsite", "url": "http://newsite.com"}
# Ответ:
# {"id": 3, "name": "newsite", "url": "http://newsite.com", "active": true}
#
# Если источник с таким именем уже есть:
# {"detail": "Source with this name already exists"}  — статус 400

@router.post("/", response_model=SourceOut, status_code=201)
def create_source(data: SourceCreate, db: Session = Depends(get_db)):
    if db.query(Source).filter(Source.name == data.name).first():
        raise HTTPException(status_code=400, detail="Source with this name already exists")
    source = Source(**data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
 
 
# PATCH /sources/{id}
# Запрос:  PATCH http://127.0.0.1:8000/sources/1
# Тело:    {"active": false} — можно передать любое поле или несколько
# Ответ:
# {"id": 1, "name": "fakestore", "url": null, "active": false}
#
# Если id не существует:
# {"detail": "Source not found"}  — статус 404

@router.patch("/{source_id}", response_model=SourceOut)
def update_source(source_id: int, data: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source
 
 
# DELETE /sources/{id}
# Запрос:  DELETE http://127.0.0.1:8000/sources/1
# Ответ:   пустой ответ — статус 204 (No Content)
#
# Если id не существует:
# {"detail": "Source not found"}  — статус 404

@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
