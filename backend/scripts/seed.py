"""Seed demo data. Run: docker compose exec api python -m scripts.seed"""
from __future__ import annotations

from datetime import date, timedelta

import bcrypt

from app import create_app
from app.common.utils import gen_anon_id, gen_invite_code
from app.extensions import db
from app.models import (
    Group,
    GroupMember,
    InspirationPost,
    Task,
    TaskAssignment,
    TaskClosure,
    User,
    UserSkill,
)


def _pw(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def run():
    app = create_app()
    with app.app_context():
        if db.session.execute(db.select(User).where(User.phone == "13800000001")).scalar_one_or_none():
            print("Seed already applied, skipping.")
            return

        leader = User(phone="13800000001", name="王浩雄", student_id="3210101001",
                      password_hash=_pw("password123"), major="计算机科学", grade="2023",
                      bio="组长 / 习概小组",
                      avatar_url="https://api.dicebear.com/7.x/personas/svg?seed=wang")
        m1 = User(phone="13800000002", name="李涵", student_id="3210101002",
                  password_hash=_pw("password123"), major="软件工程", grade="2023",
                  avatar_url="https://api.dicebear.com/7.x/personas/svg?seed=li")
        m2 = User(phone="13800000003", name="高烨辉", student_id="3210101003",
                  password_hash=_pw("password123"), major="信息安全", grade="2023",
                  avatar_url="https://api.dicebear.com/7.x/personas/svg?seed=gao")
        m3 = User(phone="13800000004", name="洪宇童", student_id="3210101004",
                  password_hash=_pw("password123"), major="计算机科学", grade="2023",
                  avatar_url="https://api.dicebear.com/7.x/personas/svg?seed=hong")
        db.session.add_all([leader, m1, m2, m3])
        db.session.flush()

        for u, skills in [
            (leader, ["统筹", "演讲", "PPT制作"]),
            (m1, ["文献综述", "写作", "PPT制作"]),
            (m2, ["数据分析", "可视化", "调研"]),
            (m3, ["摄影", "设计", "视频剪辑"]),
        ]:
            for s in skills:
                db.session.add(UserSkill(user_id=u.id, skill=s))

        g = Group(course_name="习概", name="习概小组",
                  invite_code=gen_invite_code(),
                  created_by=leader.id, description="2026 春季 习概课程作业小组")
        db.session.add(g)
        db.session.flush()
        db.session.add(GroupMember(group_id=g.id, user_id=leader.id, role="leader",
                                   anon_id=gen_anon_id()))
        for m in (m1, m2, m3):
            db.session.add(GroupMember(group_id=g.id, user_id=m.id, role="member",
                                       anon_id=gen_anon_id()))

        # Build a sample tree
        def _add(parent, title, **kw):
            t = Task(group_id=g.id, parent_id=parent.id if parent else None,
                     title=title, depth=(parent.depth + 1 if parent else 0),
                     position=kw.pop("pos", 0), path="/", **kw)
            db.session.add(t)
            db.session.flush()
            t.path = f"{parent.path}{t.id}/" if parent else f"/{t.id}/"
            # closure
            db.session.add(TaskClosure(ancestor_id=t.id, descendant_id=t.id, distance=0))
            cur = parent
            d = 1
            while cur:
                db.session.add(TaskClosure(ancestor_id=cur.id, descendant_id=t.id, distance=d))
                cur = db.session.get(Task, cur.parent_id) if cur.parent_id else None
                d += 1
            return t

        root = _add(None, "《习概》课程小组作业", description="完成习概课程的小组合作任务")
        b1 = _add(root, "读书报告", pos=0)
        b2 = _add(root, "社会实践", pos=1)
        b3 = _add(root, "思想汇报", pos=2)

        today = date.today()
        n1 = _add(b1, "文献阅读", is_leaf=True, pos=0,
                  start_date=today + timedelta(days=1),
                  end_date=today + timedelta(days=7),
                  description="阅读指定书目并做笔记")
        n2 = _add(b1, "PPT 制作", is_leaf=True, pos=1,
                  start_date=today + timedelta(days=5),
                  end_date=today + timedelta(days=10),
                  description="完成读书报告 PPT")
        n3 = _add(b1, "讲稿撰写", is_leaf=True, pos=2,
                  start_date=today + timedelta(days=8),
                  end_date=today + timedelta(days=12),
                  description="撰写演讲讲稿")
        n4 = _add(b2, "现场调研", is_leaf=True, pos=0,
                  start_date=today + timedelta(days=2),
                  end_date=today + timedelta(days=14),
                  description="完成田野调研")
        n5 = _add(b3, "个人汇报", is_leaf=True, pos=0,
                  start_date=today,
                  end_date=today + timedelta(days=21),
                  description="贯穿全程的思想汇报")

        for nid, uid in [
            (n1.id, m1.id),
            (n2.id, m1.id),
            (n2.id, m3.id),
            (n3.id, leader.id),
            (n4.id, m2.id),
            (n5.id, leader.id),
        ]:
            db.session.add(TaskAssignment(task_id=nid, user_id=uid))

        # Inspiration plaza demo posts
        db.session.add(InspirationPost(
            author_id=leader.id, title="习概课程读书报告高分模板",
            category="case", course_tag="习概",
            body_md="## 摘要\n\n本模板提供 ...\n\n## 推荐结构\n\n1. 引言\n2. 文献综述\n3. 核心论点\n4. 反思",
            cover_url="https://images.unsplash.com/photo-1455390582262-044cdead277a?w=400",
            likes=42, favs=18, comments=3,
        ))
        db.session.add(InspirationPost(
            author_id=m1.id, title="演讲脚本结构（10 分钟版）", category="script",
            course_tag="演讲", body_md="开场 30s\n主体 8min（3 个核心观点）\n收尾 1min", likes=15,
        ))
        db.session.add(InspirationPost(
            author_id=m2.id, title="社会实践访谈技巧",
            category="tip", course_tag="习概", body_md="1. 提前预约\n2. 准备 5 个开放问题\n3. 全程录音", likes=8,
        ))
        db.session.add(InspirationPost(
            author_id=m3.id, title="知网批量下载小工具", category="tool",
            link_url="https://github.com/example/tool", body_md="支持文献批量下载与去重", likes=22,
        ))
        db.session.add(InspirationPost(
            author_id=m1.id, title="iThenticate 查重门户",
            category="link", link_url="https://www.ithenticate.com",
            body_md="国际通用的论文查重平台",
        ))

        db.session.commit()
        print("Seed done.")
        print(f"  Leader: 13800000001 / password123")
        print(f"  Member: 13800000002 / password123")
        print(f"  Invite code: {g.invite_code}")


if __name__ == "__main__":
    run()
