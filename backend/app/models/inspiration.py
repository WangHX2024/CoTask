from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class InspirationPost(db.Model):
    __tablename__ = "inspiration_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="case")
    course_tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    body_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    template_root_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tasks.id"), nullable=True
    )
    link_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    favs: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        Enum("draft", "published", "removed", name="post_status"),
        default="published",
    )
    anon: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_posts_status_time", "status", "created_at"),
        Index("idx_posts_category", "category"),
        Index("idx_posts_course", "course_tag"),
    )


class PostLike(db.Model):
    __tablename__ = "post_likes"

    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("inspiration_posts.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PostFavorite(db.Model):
    __tablename__ = "post_favorites"

    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("inspiration_posts.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("idx_favs_user", "user_id"),)


class PostComment(db.Model):
    __tablename__ = "post_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("inspiration_posts.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("post_comments.id"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    anon: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (Index("idx_comments_post_time", "post_id", "created_at"),)
