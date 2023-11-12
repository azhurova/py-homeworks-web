import os
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, ForeignKey, func

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

DB_DSN = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine = create_async_engine(DB_DSN)
Session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


class User(Base):
    __tablename__ = 'fl_user'

    name: Mapped[str] = mapped_column(String[50], unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String[255], nullable=False)
    create_datetime: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    stickers: Mapped[List["Sticker"]] = relationship(back_populates="owner")


class Sticker(Base):
    __tablename__ = 'fl_sticker'

    title: Mapped[str] = mapped_column(String[255], index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    create_datetime: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    owner_id: Mapped[int] = mapped_column(ForeignKey("fl_user.id"))
    owner: Mapped["User"] = relationship(back_populates="stickers")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
