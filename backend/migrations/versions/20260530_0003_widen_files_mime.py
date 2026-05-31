"""Widen files.mime for long Office / OpenXML MIME types."""
from alembic import op
import sqlalchemy as sa

revision = "20260530_0003"
down_revision = "20260526_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "files",
        "mime",
        existing_type=sa.String(64),
        type_=sa.String(128),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "files",
        "mime",
        existing_type=sa.String(128),
        type_=sa.String(64),
        existing_nullable=True,
    )
