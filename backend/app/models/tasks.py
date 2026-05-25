from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db

TASK_STATUS = ("todo", "in_progress", "done", "blocked")


class Task(db.Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("groups.id"), nullable=True
    )  # nullable so a detached subtree can act as a plaza template
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("tasks.id"), nullable=True)
    path: Mapped[str] = mapped_column(String(512), nullable=False, default="/")
    depth: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_leaf: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(*TASK_STATUS, name="task_status"),
        default="todo",
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_tasks_group_parent", "group_id", "parent_id"),
        Index("idx_tasks_path", "group_id", "path"),
        Index("idx_tasks_ddl", "group_id", "end_date"),
        Index("idx_tasks_deleted", "deleted_at"),
    )


class TaskClosure(db.Model):
    __tablename__ = "task_closure"

    ancestor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), primary_key=True)
    descendant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), primary_key=True)
    distance: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    __table_args__ = (
        Index("idx_closure_desc", "descendant_id"),
    )


class TaskAssignment(db.Model):
    __tablename__ = "task_assignments"

    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)

    __table_args__ = (
        Index("idx_assign_user", "user_id"),
    )


class TaskDependency(db.Model):
    __tablename__ = "task_dependencies"

    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), primary_key=True)
    depends_on: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), primary_key=True)


class TaskInspirationRef(db.Model):
    __tablename__ = "task_inspiration_refs"

    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), primary_key=True)
    post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(
        Enum("ai", "manual", name="ref_source"), default="manual", nullable=False
    )
