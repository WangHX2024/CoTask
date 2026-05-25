"""Transaction context helper."""
from contextlib import contextmanager

from ..extensions import db


@contextmanager
def tx():
    """Use within service layer. Auto commits / rolls back."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
