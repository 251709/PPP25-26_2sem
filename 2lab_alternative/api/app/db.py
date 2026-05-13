"""
db.py — конфигурация БД и ORM-модели.

Таблицы:
    sources  — источники данных (fakestore, books)
    items    — товары, загруженные ETL-процессом
    events   — лог событий по каждому товару (создан, обновлён, удалён)
"""
import os


from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, Text,
    ForeignKey, DateTime, func
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Путь к ETL-базе (shop.db в папке data/)
DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "data",
    "shop.db"
)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Модели

class Source(Base):
    """Источник данных (fakestore, books)"""
    __tablename__ = "sources"

    id      = Column(Integer, primary_key=True, index=True)
    name    = Column(String, unique=True, nullable=False)   # 'fakestore', 'books'
    url     = Column(String, nullable=True)
    active  = Column(Boolean, default=True)

    items = relationship("Item", back_populates="source_rel")


class Item(Base):
    """Товар — основная сущность, загружается из ETL."""
    __tablename__ = "items"

    id         = Column(Integer, primary_key=True, index=True)
    title      = Column(Text, nullable=False)
    price      = Column(Float, nullable=True)
    category   = Column(String, nullable=True)
    rating     = Column(Float, nullable=True)
    in_stock   = Column(Integer, default=1)     # 0/1
    source     = Column(String, nullable=False)  # текстовое поле из ETL
    source_url = Column(Text, nullable=True)
    loaded_at  = Column(String, nullable=True)

    source_id  = Column(Integer, ForeignKey("sources.id"), nullable=True)
    source_rel = relationship("Source", back_populates="items")
    events     = relationship("ItemEvent", back_populates="item")


class ItemEvent(Base):
    """Лог событий по товару (создан, обновлён, удалён и т.д.)"""
    __tablename__ = "item_events"

    id         = Column(Integer, primary_key=True, index=True)
    item_id    = Column(Integer, ForeignKey("items.id"), nullable=False)
    event_type = Column(String, nullable=False)   # 'created', 'updated', 'deleted'
    note       = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    item = relationship("Item", back_populates="events")


# Утилиты

def get_db():
    """Dependency для FastAPI — открывает сессию и закрывает после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Создаёт служебные таблицы (sources, item_events). Таблицу items не трогаем."""
    # Создаём только те таблицы которых ещё нет
    Source.__table__.create(bind=engine, checkfirst=True)
    ItemEvent.__table__.create(bind=engine, checkfirst=True)
    # items уже есть из ETL — добавляем только source_id колонку если её нет
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("items")]
    if "source_id" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE items ADD COLUMN source_id INTEGER REFERENCES sources(id)"))
            conn.commit()
