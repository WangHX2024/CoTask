from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class DiscussionChannel(db.Model):
    __tablename__ = "discussion_channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    task_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tasks.id"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_channels_group", "group_id"),
        Index("uq_discussion_channels_group_task", "group_id", "task_id", unique=True),
    )


class DiscussionMessage(db.Model):
    __tablename__ = "discussion_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("discussion_channels.id"))
    task_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("tasks.id"))
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    anon: Mapped[bool] = mapped_column(Boolean, default=False)
    quote_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("discussion_messages.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_msg_channel_time", "channel_id", "created_at"),
        Index("idx_msg_task_time", "task_id", "created_at"),
    )
