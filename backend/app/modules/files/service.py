from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select

from ...common import audit
from ...common.errors import BadRequest, Forbidden, NotFound
from ...common.tx import tx
from ...extensions import db
from ...models import File, Folder, GroupMember, Task, User
from .minio_client import presign_get, presign_put


def _check_group_member(uid: int, gid: int):
    m = db.session.execute(
        select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == uid)
    ).scalar_one_or_none()
    if not m:
        raise Forbidden("非小组成员")


def sign_upload(uid: int, data: dict) -> dict:
    md5 = data.get("md5")
    gid = data.get("group_id")
    if gid:
        _check_group_member(uid, gid)
    # Dedup by md5 if provided
    if md5:
        existing = db.session.execute(
            select(File).where(File.md5 == md5, File.finalized.is_(True), File.deleted_at.is_(None))
        ).scalar_one_or_none()
        if existing:
            with tx() as s:
                new = File(
                    group_id=gid,
                    task_id=data.get("task_id"),
                    folder_id=data.get("folder_id"),
                    uploader_id=uid,
                    filename=data["filename"],
                    size=existing.size,
                    mime=existing.mime,
                    md5=md5,
                    storage_key=existing.storage_key,
                    visibility=data.get("visibility", "group"),
                    finalized=True,
                )
                s.add(new)
                s.flush()
                return {"file_id": new.id, "upload_url": None, "deduped": True}

    # Build new key
    today = datetime.utcnow().strftime("%Y/%m/%d")
    key = f"{today}/{uuid.uuid4().hex}-{data['filename']}"
    upload_url = presign_put(key, content_type=data.get("mime"))
    with tx() as s:
        f = File(
            group_id=gid,
            task_id=data.get("task_id"),
            folder_id=data.get("folder_id"),
            uploader_id=uid,
            filename=data["filename"],
            size=data["size"],
            mime=data.get("mime"),
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
        audit.record(uid, "file.upload", group_id=f.group_id, target_type="file", target_id=f.id,
                     payload={"filename": f.filename})
    return _serialize(f)


def _serialize(f: File) -> dict:
    u = db.session.get(User, f.uploader_id)
    return {
        "id": f.id,
        "filename": f.filename,
        "size": f.size,
        "mime": f.mime,
        "md5": f.md5,
        "uploader_id": f.uploader_id,
        "uploader_name": u.name if u else None,
        "group_id": f.group_id,
        "task_id": f.task_id,
        "folder_id": f.folder_id,
        "visibility": f.visibility,
        "version": f.version,
        "parent_file_id": f.parent_file_id,
        "download_url": presign_get(f.storage_key, expires_minutes=60),
        "created_at": f.created_at,
    }


def list_files(uid: int, gid: int, task_id: int | None = None, folder_id: int | None = None):
    _check_group_member(uid, gid)
    q = select(File).where(File.group_id == gid, File.finalized.is_(True), File.deleted_at.is_(None))
    if task_id:
        q = q.where(File.task_id == task_id)
    if folder_id is not None:
        q = q.where(File.folder_id == folder_id)
    q = q.order_by(File.created_at.desc())
    rows = db.session.execute(q).scalars().all()
    return [_serialize(f) for f in rows]


def delete_file(uid: int, file_id: int):
    f = db.session.get(File, file_id)
    if not f:
        raise NotFound("file")
    if f.uploader_id != uid:
        # leader can also delete
        if f.group_id:
            m = db.session.execute(
                select(GroupMember).where(
                    GroupMember.group_id == f.group_id,
                    GroupMember.user_id == uid,
                    GroupMember.role == "leader",
                )
            ).scalar_one_or_none()
            if not m:
                raise Forbidden("无权删除")
        else:
            raise Forbidden("无权删除")
    with tx():
        f.deleted_at = datetime.utcnow()
        audit.record(uid, "file.delete", group_id=f.group_id, target_type="file", target_id=f.id)


def create_folder(uid: int, gid: int, name: str, parent_id: int | None = None) -> dict:
    _check_group_member(uid, gid)
    parent = db.session.get(Folder, parent_id) if parent_id else None
    if parent and parent.group_id != gid:
        raise BadRequest("BAD_PARENT", "目标文件夹无效")
    with tx() as s:
        f = Folder(group_id=gid, parent_id=parent_id, name=name, path="/")
        s.add(f)
        s.flush()
        f.path = (f"{parent.path}{f.id}/" if parent else f"/{f.id}/")
    return {"id": f.id, "name": f.name, "parent_id": f.parent_id, "path": f.path}


def list_folders(uid: int, gid: int):
    _check_group_member(uid, gid)
    rows = db.session.execute(
        select(Folder).where(Folder.group_id == gid).order_by(Folder.path.asc())
    ).scalars().all()
    return [{"id": f.id, "name": f.name, "parent_id": f.parent_id, "path": f.path} for f in rows]
