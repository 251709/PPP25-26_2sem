"""
schemas.py — Pydantic-схемы для валидации входных и выходных данных.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Source

class SourceCreate(BaseModel):
    name:   str
    url:    Optional[str] = None
    active: bool = True


class SourceUpdate(BaseModel):
    name:   Optional[str] = None
    url:    Optional[str] = None
    active: Optional[bool] = None


class SourceOut(BaseModel):
    id:     int
    name:   str
    url:    Optional[str]
    active: bool

    model_config = {"from_attributes": True}


# Item

class ItemCreate(BaseModel):
    title:      str
    price:      Optional[float] = None
    category:   Optional[str] = None
    rating:     Optional[float] = None
    in_stock:   bool = True
    source:     str
    source_url: Optional[str] = None
    source_id:  Optional[int] = None


class ItemUpdate(BaseModel):
    """PUT — полная замена (все поля обязательны кроме source_url и source_id)."""
    title:      str
    price:      Optional[float]
    category:   Optional[str]
    rating:     Optional[float]
    in_stock:   bool
    source:     str
    source_url: Optional[str] = None
    source_id:  Optional[int] = None


class ItemPatch(BaseModel):
    """PATCH — частичное обновление (все поля опциональны)."""
    title:      Optional[str] = None
    price:      Optional[float] = None
    category:   Optional[str] = None
    rating:     Optional[float] = None
    in_stock:   Optional[bool] = None
    source_id:  Optional[int] = None


class ItemOut(BaseModel):
    id:         int
    title:      str
    price:      Optional[float]
    category:   Optional[str]
    rating:     Optional[float]
    in_stock:   int
    source:     str
    source_url: Optional[str]
    loaded_at:  Optional[str]
    source_id:  Optional[int]

    model_config = {"from_attributes": True}


# ItemEvent

class EventCreate(BaseModel):
    event_type: str
    note:       Optional[str] = None


class EventOut(BaseModel):
    id:         int
    item_id:    int
    event_type: str
    note:       Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
