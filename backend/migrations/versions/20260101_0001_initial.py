"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("student_id", sa.String(32), unique=True, nullable=True),
        sa.Column("phone", sa.String(20), unique=True, nullable=True),
        sa.Column("email", sa.String(128), unique=True, nullable=True),
        sa.Column("wechat_openid", sa.String(64), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(128), nullable=True),
        sa.Column("name", sa.String(64)),
        sa.Column("major", sa.String(64)),
        sa.Column("grade", sa.String(16)),
        sa.Column("avatar_url", sa.String(256)),
        sa.Column("bio", sa.String(256)),
        sa.Column("contribution", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prefs", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_users_deleted", "users", ["deleted_at"])

    op.create_table(
        "user_skills",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("skill", sa.String(32), primary_key=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_user_skills_skill", "user_skills", ["skill"])

    op.create_table(
        "contribution_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(64)),
        sa.Column("ref_type", sa.String(32)),
        sa.Column("ref_id", sa.BigInteger()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_contribution_user_time", "contribution_log", ["user_id", "created_at"])

    op.create_table(
        "groups",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("course_name", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("invite_code", sa.String(8), unique=True, nullable=False),
        sa.Column("status", sa.Enum("active", "archived", "dissolved", name="group_status"), nullable=False, server_default="active"),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("description", sa.String(512)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "group_members",
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role", sa.Enum("leader", "member", name="member_role"), nullable=False, server_default="member"),
        sa.Column("anon_id", sa.String(4)),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_member_user", "group_members", ["user_id", "role"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("path", sa.String(512), nullable=False, server_default="/"),
        sa.Column("depth", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_leaf", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("refined", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("status", sa.Enum("todo", "in_progress", "done", "blocked", name="task_status"), nullable=False, server_default="todo"),
        sa.Column("progress", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_tasks_group_parent", "tasks", ["group_id", "parent_id"])
    op.create_index("idx_tasks_path", "tasks", ["group_id", "path"])
    op.create_index("idx_tasks_ddl", "tasks", ["group_id", "end_date"])
    op.create_index("idx_tasks_deleted", "tasks", ["deleted_at"])

    op.create_table(
        "task_closure",
        sa.Column("ancestor_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("descendant_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("distance", sa.SmallInteger(), nullable=False),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_closure_desc", "task_closure", ["descendant_id"])

    op.create_table(
        "task_assignments",
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), primary_key=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_assign_user", "task_assignments", ["user_id"])

    op.create_table(
        "task_dependencies",
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("depends_on", sa.BigInteger(), sa.ForeignKey("tasks.id"), primary_key=True),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "inspiration_posts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("author_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category", sa.String(16), nullable=False, server_default="case"),
        sa.Column("course_tag", sa.String(64)),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("cover_url", sa.String(256)),
        sa.Column("body_md", sa.Text(), nullable=False),
        sa.Column("template_root_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("link_url", sa.String(512)),
        sa.Column("likes", sa.Integer(), server_default="0"),
        sa.Column("favs", sa.Integer(), server_default="0"),
        sa.Column("comments", sa.Integer(), server_default="0"),
        sa.Column("status", sa.Enum("draft", "published", "removed", name="post_status"), server_default="published"),
        sa.Column("anon", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_posts_status_time", "inspiration_posts", ["status", "created_at"])
    op.create_index("idx_posts_category", "inspiration_posts", ["category"])
    op.create_index("idx_posts_course", "inspiration_posts", ["course_tag"])

    op.create_table(
        "task_inspiration_refs",
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("inspiration_posts.id"), primary_key=True),
        sa.Column("source", sa.Enum("ai", "manual", name="ref_source"), nullable=False, server_default="manual"),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "post_likes",
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("inspiration_posts.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "post_favorites",
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("inspiration_posts.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_favs_user", "post_favorites", ["user_id"])

    op.create_table(
        "post_comments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("inspiration_posts.id"), nullable=False),
        sa.Column("author_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("post_comments.id"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("anon", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_comments_post_time", "post_comments", ["post_id", "created_at"])

    op.create_table(
        "folders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("folders.id"), nullable=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("path", sa.String(512), nullable=False, server_default="/"),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_folders_group", "folders", ["group_id", "parent_id"])

    op.create_table(
        "files",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("folder_id", sa.BigInteger(), sa.ForeignKey("folders.id"), nullable=True),
        sa.Column("uploader_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(256), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("mime", sa.String(64)),
        sa.Column("md5", sa.String(32)),
        sa.Column("storage_key", sa.String(256), nullable=False),
        sa.Column("visibility", sa.Enum("group", "public", "self", name="file_vis"), server_default="group"),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("parent_file_id", sa.BigInteger(), sa.ForeignKey("files.id"), nullable=True),
        sa.Column("finalized", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_files_md5", "files", ["md5"])
    op.create_index("idx_files_task", "files", ["task_id"])
    op.create_index("idx_files_group_folder", "files", ["group_id", "folder_id"])

    op.create_table(
        "discussion_channels",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_channels_group", "discussion_channels", ["group_id"])

    op.create_table(
        "discussion_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("channel_id", sa.BigInteger(), sa.ForeignKey("discussion_channels.id"), nullable=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("author_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("anon", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("quote_id", sa.BigInteger(), sa.ForeignKey("discussion_messages.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_msg_channel_time", "discussion_messages", ["channel_id", "created_at"])
    op.create_index("idx_msg_task_time", "discussion_messages", ["task_id", "created_at"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON()),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_notif_user_unread", "notifications", ["user_id", "read_at"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("actor_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32)),
        sa.Column("target_id", sa.BigInteger()),
        sa.Column("payload", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_audit_target", "audit_log", ["target_type", "target_id"])
    op.create_index("idx_audit_group_time", "audit_log", ["group_id", "created_at"])

    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column(
            "scope",
            sa.Enum(
                "tree_gen", "tree_edit", "daily_advice", "assignment",
                "inspiration_rec", "summary", name="ai_scope",
            ),
            nullable=False,
        ),
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("context", sa.JSON()),
        sa.Column("status", sa.Enum("pending", "streaming", "done", "failed", name="ai_status"), server_default="pending"),
        sa.Column("result", sa.JSON()),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_ai_user_scope", "ai_conversations", ["user_id", "scope"])

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("ai_conversations.id"), nullable=False),
        sa.Column("role", sa.Enum("user", "assistant", "system", name="ai_role"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_call", sa.JSON()),
        sa.Column("tokens_in", sa.Integer()),
        sa.Column("tokens_out", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_ai_msg_conv", "ai_messages", ["conversation_id"])

    # FULLTEXT index with ngram parser for Chinese search
    op.execute(
        "ALTER TABLE inspiration_posts ADD FULLTEXT INDEX idx_posts_search (title, body_md) WITH PARSER ngram"
    )


def downgrade():
    for t in (
        "ai_messages",
        "ai_conversations",
        "audit_log",
        "notifications",
        "discussion_messages",
        "discussion_channels",
        "files",
        "folders",
        "post_comments",
        "post_favorites",
        "post_likes",
        "task_inspiration_refs",
        "inspiration_posts",
        "task_dependencies",
        "task_assignments",
        "task_closure",
        "tasks",
        "group_members",
        "groups",
        "contribution_log",
        "user_skills",
        "users",
    ):
        op.drop_table(t)
