"""Link discussion channels to project-tree tasks."""
from alembic import op
import sqlalchemy as sa

revision = "20260530_0006"
down_revision = "20260530_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "discussion_channels",
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("tasks.id"), nullable=True),
    )
    op.alter_column(
        "discussion_channels",
        "name",
        existing_type=sa.String(64),
        type_=sa.String(256),
        existing_nullable=False,
    )
    op.create_index(
        "uq_discussion_channels_group_task",
        "discussion_channels",
        ["group_id", "task_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_discussion_channels_group_task", table_name="discussion_channels")
    op.alter_column(
        "discussion_channels",
        "name",
        existing_type=sa.String(256),
        type_=sa.String(64),
        existing_nullable=False,
    )
    op.drop_column("discussion_channels", "task_id")
