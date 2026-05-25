from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class Group(db.Model):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_name: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "archived", "dissolved", name="group_status"),
        default="active",
        nullable=False,
    )
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(db.Model):
    __tablename__ = "group_members"

    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(
        Enum("leader", "member", name="member_role"),
        default="member",
        nullable=False,
    )
    anon_id: Mapped[str | None] = mapped_column(String(4), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    group = relationship("Group", back_populates="members")

    __table_args__ = (
        Index("idx_member_user", "user_id", "role"),
    )
