"""SA-20 tests. They need a database loaded with the SA-18 demo data:
set DATABASE_URL to the test database (smartcampus_test) before running pytest.
Without it they are skipped."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

pytestmark = pytest.mark.skipif(not get_settings().database_url,
                                reason="DATABASE_URL not set")
client = TestClient(app)


def test_institutions() -> None:
    body = client.get("/api/v1/institutions").json()
    assert {i["code"]: i["program_count"] for i in body} == {"IIT": 15, "ISB": 16}


def test_all_programs() -> None:
    body = client.get("/api/v1/programs", params={"limit": 100}).json()
    assert body["total"] == 31
    assert len(body["items"]) == 31


def test_filters() -> None:
    body = client.get("/api/v1/programs", params={"institution": "iit", "level": "ingenieur"}).json()
    assert body["total"] == 5
    assert all(p["institution"] == "IIT" for p in body["items"])
    english = client.get("/api/v1/programs", params={"language": "en"}).json()
    assert any(p["code"] == "ISB-MBA" for p in english["items"])


def test_bad_level_is_rejected() -> None:
    response = client.get("/api/v1/programs", params={"level": "doctorat"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_program_detail_with_pathways() -> None:
    body = client.get("/api/v1/programs/iit-ing-gi").json()
    assert body["code"] == "IIT-ING-GI"
    assert body["labels"] == ["EURO-INF"]
    assert "IIT-PREPA" in [p["code"] for p in body["reachable_from"]]
    prepa = client.get("/api/v1/programs/IIT-PREPA").json()
    assert len(prepa["leads_to"]) == 5


def test_unknown_program() -> None:
    response = client.get("/api/v1/programs/NOPE")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROGRAM_NOT_FOUND"
