"""Backfill task_node_managers from task_assignments (assignee = subtree manager)."""
from alembic import op

revision = "20260530_0005"
down_revision = "20260530_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO task_node_managers (group_id, task_id, user_id, granted_by, granted_at)
        SELECT t.group_id, ta.task_id, ta.user_id, ta.user_id, NOW()
        FROM task_assignments ta
        JOIN tasks t ON t.id = ta.task_id
        WHERE t.deleted_at IS NULL
        ON DUPLICATE KEY UPDATE revoked_at = NULL
        """
    )


def downgrade():
    pass
