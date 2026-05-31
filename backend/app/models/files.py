from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class Folder(db.Model):
    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("folders.id"))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False, default="/")

    __table_args__ = (Index("idx_folders_group", "group_id", "parent_id"),)


class File(db.Model):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=True)
    task_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("tasks.id"), nullable=True)
    folder_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("folders.id"), nullable=True)
    uploader_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime: Mapped[str | None] = mapped_column(String(128), nullable=True)
    md5: Mapped[str | None] = mapped_column(String(64), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(256), nullable=False)
    visibility: Mapped[str] = mapped_column(
        Enum("group", "public", "self", name="file_vis"), default="group"
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_file_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("files.id"), nullable=True)
    finalized: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_files_md5", "md5"),
        Index("idx_files_task", "task_id"),
        Index("idx_files_group_folder", "group_id", "folder_id"),
    )
