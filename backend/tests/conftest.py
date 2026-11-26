import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["AUTO_SEED"] = "false"
os.environ["PRICE_PROVIDER"] = "simulator"
os.environ["ADMIN_KEY"] = "test-admin"
os.environ["CRON_SECRET"] = "test-cron"
os.environ["REFRESH_COOLDOWN_SECONDS"] = "600"
os.environ.pop("TRAVELPAYOUTS_TOKEN", None)
os.environ.pop("SERPAPI_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        yield c
