import os
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.models import Base
from app.database.session import get_db, async_session_factory, engine
from app.storage.object_store import LocalObjectStore
from app.core.config import get_settings
from app.ai.runtime import get_model_runtime
import app.storage.object_store as os_module

TEST_FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir():
    return TEST_FIXTURES_DIR


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def client(temp_storage_dir):
    # Set storage to temp directory
    store = LocalObjectStore(base_path=temp_storage_dir)
    os_module._global_store = store

    # Force mock mode for deterministic fast CI testing
    settings = get_settings()
    orig_mock = settings.AI_USE_MOCK
    settings.AI_USE_MOCK = True

    runtime = get_model_runtime()
    runtime.registry.clear()
    runtime.initialize_models()

    with TestClient(app) as test_client:
        yield test_client

    os_module._global_store = None
    settings.AI_USE_MOCK = orig_mock
