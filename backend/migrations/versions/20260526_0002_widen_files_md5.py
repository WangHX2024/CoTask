"""Widen files.md5 for SHA-256 hex digests (64 chars)."""
from alembic import op
import sqlalchemy as sa

revision = "20260526_0002"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "files",
        "md5",
        existing_type=sa.String(32),
        type_=sa.String(64),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "files",
        "md5",
        existing_type=sa.String(64),
        type_=sa.String(32),
        existing_nullable=True,
    )
