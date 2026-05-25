from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, text

from ...common import audit
from ...common.errors import BadRequest, Forbidden, NotFound
from ...common.tx import tx
from ...extensions import db
from ...models import (
    GroupMember,
    InspirationPost,
    PostComment,
    PostFavorite,
    PostLike,
    Task,
    TaskAssignment,
    TaskClosure,
    User,
)


def _serialize(p: InspirationPost, viewer_id: int | None = None, with_body: bool = False) -> dict:
    author = db.session.get(User, p.author_id)
    liked = favored = False
    if viewer_id:
        liked = db.session.execute(
            select(PostLike).where(PostLike.post_id == p.id, PostLike.user_id == viewer_id)
        ).scalar_one_or_none() is not None
        favored = db.session.execute(
            select(PostFavorite).where(PostFavorite.post_id == p.id, PostFavorite.user_id == viewer_id)
        ).scalar_one_or_none() is not None
    excerpt = (p.body_md or "")[:140].replace("\n", " ")
    base = {
        "id": p.id,
        "title": p.title,
        "cover_url": p.cover_url,
        "category": p.category,
        "course_tag": p.course_tag,
        "author_id": p.author_id if not p.anon else 0,
        "author_name": "匿名同学" if p.anon else (author.name if author else "用户"),
        "author_avatar": "" if p.anon else (author.avatar_url if author else ""),
        "anon": p.anon,
        "likes": p.likes,
        "favs": p.favs,
        "comments": p.comments,
        "link_url": p.link_url,
        "has_template": p.template_root_id is not None,
        "excerpt": excerpt,
        "created_at": p.created_at,
        "liked_by_me": liked,
        "favored_by_me": favored,
    }
    if with_body:
        base["body_md"] = p.body_md
        base["template_root_id"] = p.template_root_id
    return base


def list_posts(viewer_id: int, query: dict):
    q = (
        select(InspirationPost)
        .where(InspirationPost.status == "published")
    )
    if query.get("category"):
        q = q.where(InspirationPost.category == query["category"])
    if query.get("course"):
        q = q.where(InspirationPost.course_tag == query["course"])
    if query.get("q"):
        kw = query["q"].strip()
        q = q.where(
            or_(
                InspirationPost.title.like(f"%{kw}%"),
                InspirationPost.body_md.like(f"%{kw}%"),
            )
        )
    if query.get("mine"):
        q = q.where(InspirationPost.author_id == viewer_id)
    if query.get("favorites"):
        q = q.join(PostFavorite, PostFavorite.post_id == InspirationPost.id).where(
            PostFavorite.user_id == viewer_id
        )

    sort = query.get("sort", "latest")
    if sort == "hot":
        q = q.order_by(InspirationPost.likes.desc(), InspirationPost.created_at.desc())
    elif sort == "favorites":
        q = q.order_by(InspirationPost.favs.desc(), InspirationPost.created_at.desc())
    else:
        q = q.order_by(InspirationPost.created_at.desc())

    page = max(1, int(query.get("page") or 1))
    size = max(1, min(50, int(query.get("size") or 20)))
    total = db.session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    items = db.session.execute(q.offset((page - 1) * size).limit(size)).scalars().all()
    return {
        "items": [_serialize(p, viewer_id) for p in items],
        "total": int(total),
        "page": page,
        "size": size,
    }


def get_post(viewer_id: int, post_id: int) -> dict:
    p = db.session.get(InspirationPost, post_id)
    if not p or p.status == "removed":
        raise NotFound("post")
    return _serialize(p, viewer_id, with_body=True)


def _clone_subtree_as_template(group_id: int, author_id: int) -> int | None:
    """Deep-copy current group's tasks into a detached subtree (group_id=NULL).

    Returns the new root task id of the template.
    """
    roots = db.session.execute(
        select(Task).where(
            Task.group_id == group_id, Task.parent_id.is_(None), Task.deleted_at.is_(None)
        ).order_by(Task.position.asc())
    ).scalars().all()
    if not roots:
        return None

    # Create a synthetic root to anchor the template (template can have multiple original roots)
    synth = Task(
        group_id=None,
        parent_id=None,
        title="模板根",
        is_leaf=False,
        position=0,
        depth=0,
        path="/",
    )
    db.session.add(synth)
    db.session.flush()
    synth.path = f"/{synth.id}/"

    def _copy(src: Task, new_parent: Task, depth: int, position: int):
        copy = Task(
            group_id=None,
            parent_id=new_parent.id,
            title=src.title,
            description=src.description,
            is_leaf=src.is_leaf,
            position=position,
            depth=depth,
            path="/",
        )
        db.session.add(copy)
        db.session.flush()
        copy.path = f"{new_parent.path}{copy.id}/"
        # closure
        from ..tree.service import _insert_closure_for_new
        _insert_closure_for_new(copy.id, new_parent.id)
        children = db.session.execute(
            select(Task).where(Task.parent_id == src.id, Task.deleted_at.is_(None))
            .order_by(Task.position.asc())
        ).scalars().all()
        for i, c in enumerate(children):
            _copy(c, copy, depth + 1, i)

    # Closure for synth itself
    from ..tree.service import _insert_closure_for_new as _ins
    _ins(synth.id, None)

    for i, src in enumerate(roots):
        _copy(src, synth, 1, i)
    return synth.id


def create_post(author_id: int, data: dict) -> dict:
    template_root = None
    if data.get("template_from_group_id"):
        gid = data["template_from_group_id"]
        m = db.session.execute(
            select(GroupMember).where(
                GroupMember.group_id == gid, GroupMember.user_id == author_id,
                GroupMember.role == "leader",
            )
        ).scalar_one_or_none()
        if not m:
            raise Forbidden("只有该组组长可以发布该组的模板")

    with tx() as s:
        if data.get("template_from_group_id"):
            template_root = _clone_subtree_as_template(data["template_from_group_id"], author_id)
        p = InspirationPost(
            author_id=author_id,
            title=data["title"],
            category=data["category"] if not template_root else "template",
            body_md=data.get("body_md", ""),
            cover_url=data.get("cover_url"),
            course_tag=data.get("course_tag"),
            link_url=data.get("link_url"),
            anon=bool(data.get("anon")),
            template_root_id=template_root,
        )
        s.add(p)
        s.flush()
        audit.record(author_id, "post.create", target_type="post", target_id=p.id,
                     payload={"category": p.category})
    return _serialize(p, author_id, with_body=True)


def update_post(actor_id: int, post_id: int, data: dict) -> dict:
    p = db.session.get(InspirationPost, post_id)
    if not p or p.status == "removed":
        raise NotFound("post")
    if p.author_id != actor_id:
        raise Forbidden("仅作者可编辑")
    with tx():
        for k, v in data.items():
            if v is not None:
                setattr(p, k, v)
    return _serialize(p, actor_id, with_body=True)


def delete_post(actor_id: int, post_id: int):
    p = db.session.get(InspirationPost, post_id)
    if not p:
        raise NotFound("post")
    if p.author_id != actor_id:
        raise Forbidden("仅作者可删除")
    with tx():
        p.status = "removed"


def toggle_like(uid: int, post_id: int) -> bool:
    p = db.session.get(InspirationPost, post_id)
    if not p or p.status == "removed":
        raise NotFound("post")
    existing = db.session.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == uid)
    ).scalar_one_or_none()
    with tx() as s:
        if existing:
            s.delete(existing)
            p.likes = max(0, p.likes - 1)
            return False
        s.add(PostLike(post_id=post_id, user_id=uid))
        p.likes += 1
    return True


def toggle_favorite(uid: int, post_id: int) -> bool:
    p = db.session.get(InspirationPost, post_id)
    if not p:
        raise NotFound("post")
    existing = db.session.execute(
        select(PostFavorite).where(PostFavorite.post_id == post_id, PostFavorite.user_id == uid)
    ).scalar_one_or_none()
    with tx() as s:
        if existing:
            s.delete(existing)
            p.favs = max(0, p.favs - 1)
            return False
        s.add(PostFavorite(post_id=post_id, user_id=uid))
        p.favs += 1
    return True


def add_comment(uid: int, post_id: int, data: dict) -> dict:
    p = db.session.get(InspirationPost, post_id)
    if not p or p.status == "removed":
        raise NotFound("post")
    with tx() as s:
        c = PostComment(
            post_id=post_id, author_id=uid,
            parent_id=data.get("parent_id"),
            body=data["body"], anon=bool(data.get("anon")),
        )
        s.add(c)
        p.comments += 1
        s.flush()
    return _serialize_comment(c)


def list_comments(post_id: int) -> list[dict]:
    rows = db.session.execute(
        select(PostComment).where(
            PostComment.post_id == post_id, PostComment.deleted_at.is_(None)
        ).order_by(PostComment.created_at.asc())
    ).scalars().all()
    return [_serialize_comment(c) for c in rows]


def _serialize_comment(c: PostComment) -> dict:
    u = db.session.get(User, c.author_id)
    return {
        "id": c.id,
        "post_id": c.post_id,
        "body": c.body,
        "author_id": 0 if c.anon else c.author_id,
        "author_name": "匿名同学" if c.anon else (u.name if u else "用户"),
        "author_avatar": "" if c.anon else (u.avatar_url if u else ""),
        "anon": c.anon,
        "parent_id": c.parent_id,
        "created_at": c.created_at,
    }


def import_template(actor_id: int, post_id: int, to_group_id: int, mode: str = "replace") -> dict:
    p = db.session.get(InspirationPost, post_id)
    if not p or not p.template_root_id:
        raise BadRequest("NOT_TEMPLATE", "该帖不是模板")
    m = db.session.execute(
        select(GroupMember).where(
            GroupMember.group_id == to_group_id, GroupMember.user_id == actor_id,
            GroupMember.role == "leader",
        )
    ).scalar_one_or_none()
    if not m:
        raise Forbidden("仅目标组组长可导入")

    with tx() as s:
        if mode == "replace":
            # Soft-delete existing
            s.execute(
                db.update(Task).where(
                    Task.group_id == to_group_id, Task.deleted_at.is_(None)
                ).values(deleted_at=datetime.utcnow())
            )

        synth_root = db.session.get(Task, p.template_root_id)
        # Copy children of synth as new roots into target group
        from ..tree.service import _insert_closure_for_new
        roots = db.session.execute(
            select(Task).where(Task.parent_id == synth_root.id, Task.deleted_at.is_(None))
            .order_by(Task.position.asc())
        ).scalars().all()

        def _copy(src: Task, new_parent_id: int | None, depth: int, position: int):
            copy = Task(
                group_id=to_group_id,
                parent_id=new_parent_id,
                title=src.title,
                description=src.description,
                is_leaf=src.is_leaf,
                position=position,
                depth=depth,
                path="/",
            )
            s.add(copy)
            s.flush()
            new_parent = db.session.get(Task, new_parent_id) if new_parent_id else None
            copy.path = (f"{new_parent.path}{copy.id}/" if new_parent else f"/{copy.id}/")
            _insert_closure_for_new(copy.id, new_parent_id)
            children = db.session.execute(
                select(Task).where(Task.parent_id == src.id, Task.deleted_at.is_(None))
                .order_by(Task.position.asc())
            ).scalars().all()
            for i, c in enumerate(children):
                _copy(c, copy.id, depth + 1, i)

        for i, r in enumerate(roots):
            _copy(r, None, 0, i)
        audit.record(actor_id, "template.import", group_id=to_group_id,
                     target_type="post", target_id=post_id)
    from ..tree.service import get_tree
    return get_tree(to_group_id)
