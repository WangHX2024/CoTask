"""Add task_node_managers for per-node subtree management."""
from alembic import op
import sqlalchemy as sa

revision = "20260530_0004"
down_revision = "20260530_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "task_node_managers",
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("groups.id"), primary_key=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("granted_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("granted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index(
        "idx_task_node_managers_user",
        "task_node_managers",
        ["group_id", "user_id"],
    )


def downgrade():
    op.drop_index("idx_task_node_managers_user", table_name="task_node_managers")
    op.drop_table("task_node_managers")
