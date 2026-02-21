from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from snipsel_api.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


SnipselType = Enum(
    "text",
    "task",
    "link_external",
    "link_internal",
    "attachment",
    "image",
    name="snipsel_type",
)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Collection(db.Model):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(8), nullable=False, default="🗒")
    header_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    list_for_day: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    modified_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    owner = relationship("User", foreign_keys=[owner_user_id])

    __table_args__ = (
        UniqueConstraint("owner_user_id", "list_for_day", name="uq_collection_owner_day"),
        Index("ix_collections_owner_archived", "owner_user_id", "archived_at"),
    )


class Snipsel(db.Model):
    __tablename__ = "snipsels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    type: Mapped[str] = mapped_column(SnipselType, nullable=False, index=True)

    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    task_done: Mapped[bool] = mapped_column(default=False, nullable=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    done_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_label: Mapped[str | None] = mapped_column(Text, nullable=True)

    internal_target_snipsel_id: Mapped[str | None] = mapped_column(ForeignKey("snipsels.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    modified_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    owner = relationship("User", foreign_keys=[owner_user_id])
    done_by = relationship("User", foreign_keys=[done_by_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])

    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="snipsel", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "(task_done = 0) OR (task_done = 1)",
            name="ck_snipsels_task_done_bool",
        ),
    )


class CollectionSnipsel(db.Model):
    __tablename__ = "collection_snipsels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id: Mapped[str] = mapped_column(ForeignKey("collections.id"), nullable=False, index=True)
    snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), nullable=False, index=True)

    position: Mapped[int] = mapped_column(nullable=False, default=0)
    indent: Mapped[int] = mapped_column(nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    collection = relationship("Collection")
    snipsel = relationship("Snipsel")

    __table_args__ = (
        UniqueConstraint("collection_id", "snipsel_id", name="uq_collection_snipsel"),
        Index("ix_collection_snipsels_collection_position", "collection_id", "position"),
        CheckConstraint("indent >= 0", name="ck_collection_snipsels_indent_nonneg"),
    )


class Tag(db.Model):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("owner_user_id", "name", name="uq_tags_owner_name"),)


class SnipselTag(db.Model):
    __tablename__ = "snipsel_tags"

    snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id"), primary_key=True)

    snipsel = relationship("Snipsel")
    tag = relationship("Tag")


class Mention(db.Model):
    __tablename__ = "mentions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("owner_user_id", "name", name="uq_mentions_owner_name"),)


class SnipselMention(db.Model):
    __tablename__ = "snipsel_mentions"

    snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), primary_key=True)
    mention_id: Mapped[str] = mapped_column(ForeignKey("mentions.id"), primary_key=True)

    snipsel = relationship("Snipsel")
    mention = relationship("Mention")


class SnipselLink(db.Model):
    __tablename__ = "snipsel_links"

    from_snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), primary_key=True)
    to_snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    from_snipsel = relationship("Snipsel", foreign_keys=[from_snipsel_id])
    to_snipsel = relationship("Snipsel", foreign_keys=[to_snipsel_id])

    __table_args__ = (Index("ix_snipsel_links_to", "to_snipsel_id"),)


class Attachment(db.Model):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snipsel_id: Mapped[str] = mapped_column(ForeignKey("snipsels.id"), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False)

    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    snipsel: Mapped[Snipsel] = relationship("Snipsel", back_populates="attachments")


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user = relationship("User")
