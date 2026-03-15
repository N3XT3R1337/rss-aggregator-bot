from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


feed_group_association = Table(
    "feed_group_association",
    Base.metadata,
    Column("feed_id", Integer, ForeignKey("feeds.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("feed_groups.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    digest_hour: Mapped[int] = mapped_column(Integer, default=9)
    digest_minute: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    feeds: Mapped[List["Feed"]] = relationship("Feed", back_populates="user", cascade="all, delete-orphan")
    keywords: Mapped[List["Keyword"]] = relationship("Keyword", back_populates="user", cascade="all, delete-orphan")
    groups: Mapped[List["FeedGroup"]] = relationship("FeedGroup", back_populates="user", cascade="all, delete-orphan")
    sent_entries: Mapped[List["SentEntry"]] = relationship("SentEntry", back_populates="user", cascade="all, delete-orphan")


class Feed(Base):
    __tablename__ = "feeds"
    __table_args__ = (UniqueConstraint("user_id", "url", name="uq_user_feed_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_entry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="feeds")
    groups: Mapped[List["FeedGroup"]] = relationship(
        "FeedGroup", secondary=feed_group_association, back_populates="feeds"
    )
    sent_entries: Mapped[List["SentEntry"]] = relationship("SentEntry", back_populates="feed", cascade="all, delete-orphan")


class FeedGroup(Base):
    __tablename__ = "feed_groups"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_group_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="groups")
    feeds: Mapped[List["Feed"]] = relationship(
        "Feed", secondary=feed_group_association, back_populates="groups"
    )


class Keyword(Base):
    __tablename__ = "keywords"
    __table_args__ = (UniqueConstraint("user_id", "word", name="uq_user_keyword"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    is_include: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="keywords")


class SentEntry(Base):
    __tablename__ = "sent_entries"
    __table_args__ = (UniqueConstraint("user_id", "entry_id", name="uq_user_entry"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feed_id: Mapped[int] = mapped_column(Integer, ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False)
    entry_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entry_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    entry_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="sent_entries")
    feed: Mapped["Feed"] = relationship("Feed", back_populates="sent_entries")
