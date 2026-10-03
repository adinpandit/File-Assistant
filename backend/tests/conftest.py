import os
import secrets
from functools import partial

import pytest

# Must run before anything imports app.config. Tests get a random,
# per-session HS256 secret (>= 32 bytes) instead of the short default
# or a developer's real secret.
os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(48)

from qdrant_client import QdrantClient  # noqa: E402

import app.core.vectorstore.qdrant_store as qdrant_store  # noqa: E402

# Tests never talk to a live Qdrant server (they swap in fake clients),
# so skip the background server-version probe that would otherwise warn.
qdrant_store.QdrantClient = partial(QdrantClient, check_compatibility=False)

_test_postgres = None


def pytest_configure(config):
    # Runs before collection, so test_document_store sees TEST_DATABASE_URL.
    # An explicitly configured TEST_DATABASE_URL takes precedence.
    global _test_postgres

    if os.getenv("TEST_DATABASE_URL"):
        return

    import tempfile

    import pgserver

    _test_postgres = pgserver.get_server(tempfile.mkdtemp(), cleanup_mode="delete")
    os.environ["TEST_DATABASE_URL"] = _test_postgres.get_uri()


def pytest_unconfigure(config):
    if _test_postgres is not None:
        _test_postgres.cleanup()
        os.environ.pop("TEST_DATABASE_URL", None)


TEST_USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "email": "test@example.com",
    "role": "USER",
}


@pytest.fixture
def authenticated_user():
    from app.main import app
    from app.core.auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: TEST_USER

    yield TEST_USER

    app.dependency_overrides.pop(get_current_user, None)
