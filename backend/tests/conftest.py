import os
import pytest

os.environ.setdefault("APP_ENV", "testing")


@pytest.fixture(scope="session")
def app():
    from app import create_app
    app = create_app()
    yield app
