from __future__ import annotations

import uuid
from datetime import datetime

from flask import current_app
from sqlalchemy import func, or_, select

from ...common import audit
from ...common.datetime_util import to_api_datetime, utc_now
from ...common.errors import BadRequest, Forbidden, NotFound
from ...common.tx import tx
from ...extensions import db
from ...models import File, Folder, GroupMember, Task, TaskClosure, User
from .minio_client import presign_get, presign_put

UNCATEGORIZED_LABEL = "未分类"


def _normalize_mime(mime: str | None) -> str | None:
    if not mime:
        return None
    return mime.strip()[:128] or None


def _check_group_member(uid: int, gid: int):
    m = db.session.execute(
        select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == uid)
    ).scalar_one_or_none()
    if not m:
        raise Forbidden("非小组成员")


def _resolve_folder_id(gid: int, folder_id: int | None) -> int | None:
    """None or 0 → group root (files.folder_id IS NULL)."""
    if folder_id is None or folder_id == 0:
        return None
    folder = db.session.get(Folder, folder_id)
    if not folder or folder.group_id != gid:
        raise BadRequest("BAD_FOLDER", "目标文件夹无效")
    return folder_id


def _validate_tag_task(gid: int, tag_task_id: int | None) -> None:
    if tag_task_id is None:
        return
    t = db.session.get(Task, tag_task_id)
    if not t or t.group_id != gid or t.deleted_at:
        raise BadRequest("BAD_TAG", "任务归属无效或已删除")


def _task_tag_label(gid: int, tag_task_id: int | None) -> str:
    if not tag_task_id:
        return UNCATEGORIZED_LABEL
    t = db.session.get(Task, tag_task_id)
    if not t or t.group_id != gid or t.deleted_at:
        return UNCATEGORIZED_LABEL
    parts: list[str] = []
    cur: Task | None = t
    seen: set[int] = set()
    while cur and cur.id not in seen:
        seen.add(cur.id)
        parts.append(cur.title)
        cur = db.session.get(Task, cur.parent_id) if cur.parent_id else None
    return " / ".join(reversed(parts))


def _folder_subtree_ids(gid: int, root_id: int) -> list[int]:
    rows = db.session.execute(select(Folder).where(Folder.group_id == gid)).scalars().all()
    children_map: dict[int | None, list[int]] = {}
    for f in rows:
        children_map.setdefault(f.parent_id, []).append(f.id)

    out: list[int] = []

    def walk(fid: int) -> None:
        out.append(fid)
        for cid in children_map.get(fid, []):
            walk(cid)

    walk(root_id)
    return out


def sign_upload(uid: int, data: dict) -> dict:
    max_bytes = int(current_app.config.get("UPLOAD_MAX_BYTES", 100 * 1024 * 1024))
    size = int(data.get("size") or 0)
    if size <= 0:
        raise BadRequest("INVALID_SIZE", "文件大小无效")
    if size > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise BadRequest("FILE_TOO_LARGE", f"单文件不能超过 {limit_mb}MB")

    md5 = data.get("md5")
    gid = data.get("group_id")
    if not gid:
        raise BadRequest("GROUP_REQUIRED", "缺少小组信息")
    _check_group_member(uid, gid)

    folder_id = _resolve_folder_id(gid, data.get("folder_id"))
    tag_task_id = data.get("tag_task_id")
    if tag_task_id is None and data.get("task_id") is not None:
        tag_task_id = data.get("task_id")
    _validate_tag_task(gid, tag_task_id)

    if md5:
        existing = db.session.execute(
            select(File).where(File.md5 == md5, File.finalized.is_(True), File.deleted_at.is_(None))
        ).scalar_one_or_none()
        if existing:
            with tx() as s:
                new = File(
                    group_id=gid,
                    task_id=tag_task_id,
                    folder_id=folder_id,
                    uploader_id=uid,
                    filename=data["filename"],
                    size=existing.size,
                    mime=_normalize_mime(existing.mime),
                    md5=md5,
                    storage_key=existing.storage_key,
                    visibility=data.get("visibility", "group"),
                    finalized=True,
                )
                s.add(new)
                s.flush()
                return {"file_id": new.id, "upload_url": None, "deduped": True}

    today = utc_now().strftime("%Y/%m/%d")
    key = f"{today}/{uuid.uuid4().hex}-{data['filename']}"
    mime = _normalize_mime(data.get("mime"))
    upload_url = presign_put(key, content_type=mime)
    with tx() as s:
        f = File(
            group_id=gid,
            task_id=tag_task_id,
            folder_id=folder_id,
            uploader_id=uid,
            filename=data["filename"],
            size=data["size"],
            mime=mime,
            md5=md5,
            storage_key=key,
            visibility=data.get("visibility", "group"),
            finalized=False,
        )
        s.add(f)
        s.flush()
    return {"file_id": f.id, "upload_url": upload_url, "deduped": False}


def finalize(uid: int, file_id: int) -> dict:
    f = db.session.get(File, file_id)
    if not f or f.uploader_id != uid:
        raise NotFound("file")
    with tx():
        f.finalized = True
        audit.record(
            uid,
            "file.upload",
            group_id=f.group_id,
            target_type="file",
            target_id=f.id,
            payload={"filename": f.filename},
        )
    return _serialize(f)


def _serialize(f: File) -> dict:
    u = db.session.get(User, f.uploader_id)
    gid = f.group_id or 0
    tag_task_id = f.task_id
    tag_label = _task_tag_label(gid, tag_task_id)
    return {
        "id": f.id,
        "filename": f.filename,
        "size": f.size,
        "mime": f.mime,
        "md5": f.md5,
        "uploader_id": f.uploader_id,
        "uploader_name": u.name if u else None,
        "group_id": f.group_id,
        "folder_id": f.folder_id,
        "tag_task_id": tag_task_id,
        "tag_label": tag_label,
        "task_id": tag_task_id,
        "visibility": f.visibility,
        "version": f.version,
        "parent_file_id": f.parent_file_id,
        "download_url": presign_get(f.storage_key, expires_minutes=60),
        "created_at": to_api_datetime(f.created_at),
    }


def _task_subtree_ids(gid: int, root_task_id: int) -> list[int]:
    """All task ids in subtree (including root), excluding soft-deleted tasks."""
    rows = db.session.execute(
        select(TaskClosure.descendant_id)
        .join(Task, Task.id == TaskClosure.descendant_id)
        .where(
            TaskClosure.ancestor_id == root_task_id,
            Task.group_id == gid,
            Task.deleted_at.is_(None),
        )
    ).scalars().all()
    return list(rows) if rows else [root_task_id]


def _uncategorized_filter(gid: int):
    deleted_task_ids = select(Task.id).where(
        Task.group_id == gid,
        Task.deleted_at.is_not(None),
    )
    return or_(File.task_id.is_(None), File.task_id.in_(deleted_task_ids))


def list_files(
    uid: int,
    gid: int,
    *,
    folder_id: int | None = None,
    folder_root: bool = False,
    tag_task_id: int | None = None,
    tag_uncategorized: bool = False,
):
    _check_group_member(uid, gid)
    q = select(File).where(
        File.group_id == gid,
        File.finalized.is_(True),
        File.deleted_at.is_(None),
    )

    if tag_uncategorized:
        q = q.where(_uncategorized_filter(gid))
    elif tag_task_id is not None:
        t = db.session.get(Task, tag_task_id)
        if not t or t.group_id != gid or t.deleted_at:
            return []
        subtree_ids = _task_subtree_ids(gid, tag_task_id)
        q = q.where(File.task_id.in_(subtree_ids))
    elif folder_root or folder_id == 0:
        q = q.where(File.folder_id.is_(None))
    elif folder_id is not None:
        folder = db.session.get(Folder, folder_id)
        if not folder or folder.group_id != gid:
            raise NotFound("folder")
        q = q.where(File.folder_id == folder_id)
    else:
        raise BadRequest("LIST_SCOPE_REQUIRED", "请指定文件夹或任务归属筛选条件")

    q = q.order_by(File.created_at.desc())
    rows = db.session.execute(q).scalars().all()
    return [_serialize(f) for f in rows]


def _load_group_files(gid: int, file_ids: list[int]) -> list[File]:
    if not file_ids:
        raise BadRequest("FILE_IDS_REQUIRED", "请选择至少一个文件")
    ordered = list(dict.fromkeys(file_ids))
    rows = db.session.execute(
        select(File).where(
            File.id.in_(ordered),
            File.group_id == gid,
            File.deleted_at.is_(None),
            File.finalized.is_(True),
        )
    ).scalars().all()
    by_id = {f.id: f for f in rows}
    missing = [fid for fid in ordered if fid not in by_id]
    if missing:
        raise BadRequest("BAD_FILES", "部分文件不存在或不可操作")
    return [by_id[fid] for fid in ordered]


def move_files(uid: int, gid: int, file_ids: list[int], folder_id: int | None) -> dict:
    _check_group_member(uid, gid)
    target_folder_id = _resolve_folder_id(gid, folder_id)
    files = _load_group_files(gid, file_ids)
    with tx():
        for f in files:
            f.folder_id = target_folder_id
        audit.record(
            uid,
            "file.move",
            group_id=gid,
            target_type="file",
            target_id=None,
            payload={
                "file_ids": [f.id for f in files],
                "folder_id": target_folder_id,
            },
        )
    return {"updated": len(files), "items": [_serialize(f) for f in files]}


def bulk_update_file_tags(
    uid: int, gid: int, file_ids: list[int], tag_task_id: int | None
) -> dict:
    _check_group_member(uid, gid)
    _validate_tag_task(gid, tag_task_id)
    files = _load_group_files(gid, file_ids)
    with tx():
        for f in files:
            f.task_id = tag_task_id
        audit.record(
            uid,
            "file.update_tag",
            group_id=gid,
            target_type="file",
            target_id=None,
            payload={
                "file_ids": [f.id for f in files],
                "tag_task_id": tag_task_id,
            },
        )
    return {"updated": len(files), "items": [_serialize(f) for f in files]}


def update_file_tag(uid: int, file_id: int, tag_task_id: int | None) -> dict:
    f = db.session.get(File, file_id)
    if not f or not f.group_id or f.deleted_at:
        raise NotFound("file")
    _check_group_member(uid, f.group_id)
    if tag_task_id is not None:
        _validate_tag_task(f.group_id, tag_task_id)
    with tx():
        f.task_id = tag_task_id
        audit.record(
            uid,
            "file.update_tag",
            group_id=f.group_id,
            target_type="file",
            target_id=f.id,
            payload={"tag_task_id": tag_task_id},
        )
    return _serialize(f)


def delete_file(uid: int, file_id: int):
    f = db.session.get(File, file_id)
    if not f:
        raise NotFound("file")
    if f.group_id:
        _check_group_member(uid, f.group_id)
    elif f.uploader_id != uid:
        raise Forbidden("无权删除")
    with tx():
        f.deleted_at = utc_now()
        audit.record(
            uid,
            "file.delete",
            group_id=f.group_id,
            target_type="file",
            target_id=f.id,
        )


def create_folder(uid: int, gid: int, name: str, parent_id: int | None = None) -> dict:
    _check_group_member(uid, gid)
    parent = db.session.get(Folder, parent_id) if parent_id else None
    if parent and parent.group_id != gid:
        raise BadRequest("BAD_PARENT", "目标文件夹无效")
    name = name.strip()
    if not name:
        raise BadRequest("INVALID_NAME", "文件夹名不能为空")
    with tx() as s:
        f = Folder(group_id=gid, parent_id=parent_id, name=name, path="/")
        s.add(f)
        s.flush()
        f.path = f"{parent.path}{f.id}/" if parent else f"/{f.id}/"
    return {"id": f.id, "name": f.name, "parent_id": f.parent_id, "path": f.path}


def list_folders(uid: int, gid: int):
    _check_group_member(uid, gid)
    rows = db.session.execute(
        select(Folder).where(Folder.group_id == gid).order_by(Folder.path.asc())
    ).scalars().all()
    return [{"id": f.id, "name": f.name, "parent_id": f.parent_id, "path": f.path} for f in rows]


def rename_folder(uid: int, gid: int, folder_id: int, name: str) -> dict:
    _check_group_member(uid, gid)
    folder = db.session.get(Folder, folder_id)
    if not folder or folder.group_id != gid:
        raise NotFound("folder")
    name = name.strip()
    if not name:
        raise BadRequest("INVALID_NAME", "文件夹名不能为空")
    with tx():
        folder.name = name
        audit.record(
            uid,
            "folder.rename",
            group_id=gid,
            target_type="folder",
            target_id=folder_id,
            payload={"name": name},
        )
    return {"id": folder.id, "name": folder.name, "parent_id": folder.parent_id, "path": folder.path}


def delete_folder(uid: int, gid: int, folder_id: int) -> dict:
    """Cascade: soft-delete all files in subtree, then remove folder rows."""
    _check_group_member(uid, gid)
    folder = db.session.get(Folder, folder_id)
    if not folder or folder.group_id != gid:
        raise NotFound("folder")

    subtree_ids = _folder_subtree_ids(gid, folder_id)
    if not subtree_ids:
        return {"deleted_folders": 0, "deleted_files": 0}
    now = utc_now()

    with tx() as s:
        file_result = s.execute(
            db.update(File)
            .where(
                File.folder_id.in_(subtree_ids),
                File.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        deleted_files = file_result.rowcount or 0

        # Break FK refs before removing folder rows (files + folder parent links).
        s.execute(
            db.update(File)
            .where(File.folder_id.in_(subtree_ids))
            .values(folder_id=None)
        )
        s.execute(
            db.update(Folder)
            .where(Folder.id.in_(subtree_ids))
            .values(parent_id=None)
        )
        s.flush()
        s.execute(db.delete(Folder).where(Folder.id.in_(subtree_ids)))

        audit.record(
            uid,
            "folder.delete",
            group_id=gid,
            target_type="folder",
            target_id=folder_id,
            payload={
                "subtree_ids": subtree_ids,
                "deleted_files": deleted_files,
            },
        )

    return {"deleted_folders": len(subtree_ids), "deleted_files": deleted_files}
