import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Integer, Text, Boolean, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="editor", nullable=False)  # "admin" | "editor"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'editor')", name="chk_user_role"),
    )

class Show(Base):
    __tablename__ = "shows"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # "featured", "series", "minisodes", "songs"
    categories: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)  # "draft" | "published"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    seasons: Mapped[List["Season"]] = relationship(
        "Season",
        back_populates="show",
        cascade="all, delete-orphan",
        order_by="Season.season_number"
    )
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode",
        back_populates="show",
        cascade="all, delete-orphan"
    )
    artwork: Mapped[List["Artwork"]] = relationship(
        "Artwork",
        back_populates="show",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published')", name="chk_show_status"),
        CheckConstraint("section IS NULL OR section IN ('featured', 'series', 'minisodes', 'songs')", name="chk_show_section"),
        Index("ix_show_section_status", "section", "status"),
    )

class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    show_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("shows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    season_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 0 for trailers, 1..N for regular seasons
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    show: Mapped["Show"] = relationship("Show", back_populates="seasons")
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode",
        back_populates="season",
        cascade="all, delete-orphan",
        order_by="Episode.episode_number"
    )

    __table_args__ = (
        UniqueConstraint("show_id", "season_number", name="uq_show_season_number"),
        CheckConstraint("season_number >= 0", name="chk_season_number_non_negative"),
        Index("ix_season_show_number", "show_id", "season_number"),
    )

class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    custom_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)  # e.g., "ep_0001"
    show_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("shows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    episode_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", index=True)  # "en" | "hi"
    content_group: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)  # "draft" | "published"
    artwork_available: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    show: Mapped["Show"] = relationship("Show", back_populates="episodes")
    season: Mapped["Season"] = relationship("Season", back_populates="episodes")
    artwork: Mapped[List["Artwork"]] = relationship(
        "Artwork",
        back_populates="episode",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("content_group", "language", name="uq_episode_content_group_language"),
        CheckConstraint("status IN ('draft', 'published')", name="chk_episode_status"),
        CheckConstraint("language IN ('en', 'hi')", name="chk_episode_language"),
        CheckConstraint("episode_number >= 1", name="chk_episode_number_positive"),
        CheckConstraint("duration_seconds IS NULL OR duration_seconds > 0", name="chk_episode_duration_positive"),
        Index("ix_episode_content_group_lang", "content_group", "language"),
        Index("ix_episode_show_season_epnum", "show_id", "season_id", "episode_number"),
    )

class Artwork(Base):
    __tablename__ = "artwork"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # "show" | "episode"
    show_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("shows.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    episode_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    artwork_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # "poster" | "banner" | "thumbnail"
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    show: Mapped[Optional["Show"]] = relationship("Show", back_populates="artwork")
    episode: Mapped[Optional["Episode"]] = relationship("Episode", back_populates="artwork")

    __table_args__ = (
        UniqueConstraint("show_id", "artwork_type", name="uq_show_artwork_type"),
        UniqueConstraint("episode_id", "artwork_type", name="uq_episode_artwork_type"),
        CheckConstraint("entity_type IN ('show', 'episode')", name="chk_artwork_entity_type"),
        CheckConstraint("artwork_type IN ('poster', 'banner', 'thumbnail')", name="chk_artwork_type"),
        CheckConstraint(
            "(entity_type = 'show' AND show_id IS NOT NULL AND episode_id IS NULL) OR "
            "(entity_type = 'episode' AND episode_id IS NOT NULL AND show_id IS NULL)",
            name="chk_artwork_entity_integrity"
        ),
        Index("ix_artwork_entity_type_type", "entity_type", "artwork_type"),
    )

class PublishRun(Base):
    __tablename__ = "publish_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # "success" | "failed"
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    show_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    episode_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @property
    def catalogue_version(self) -> int:
        return self.version

    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed')", name="chk_publish_status"),
        CheckConstraint("version >= 1", name="chk_publish_version_positive"),
        Index("ix_publish_status_version", "status", "version"),
    )
