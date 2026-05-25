from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class AiConversation(db.Model):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(
        Enum(
            "tree_gen",
            "tree_edit",
            "daily_advice",
            "assignment",
            "inspiration_rec",
            "summary",
            name="ai_scope",
        ),
        nullable=False,
    )
    group_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(
        Enum("pending", "streaming", "done", "failed", name="ai_status"),
        default="pending",
    )
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("idx_ai_user_scope", "user_id", "scope"),)


class AiMessage(db.Model):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ai_conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        Enum("user", "assistant", "system", name="ai_role"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_call: Mapped[dict] = mapped_column(JSON, default=dict)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("idx_ai_msg_conv", "conversation_id"),)
