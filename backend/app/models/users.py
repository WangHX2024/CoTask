from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    major: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(256), nullable=True)
    contribution: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prefs: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_deleted", "deleted_at"),
    )

    @property
    def display_name(self) -> str:
        return self.name or (self.phone or self.student_id or f"用户{self.id}")


class UserSkill(db.Model):
    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    skill: Mapped[str] = mapped_column(String(32), primary_key=True)

    user = relationship("User", back_populates="skills")

    __table_args__ = (
        Index("idx_user_skills_skill", "skill"),
    )


class ContributionLog(db.Model):
    __tablename__ = "contribution_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(64))
    ref_type: Mapped[str | None] = mapped_column(String(32))
    ref_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_contribution_user_time", "user_id", "created_at"),
    )
