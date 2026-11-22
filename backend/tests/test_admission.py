"""SA-21 tests. Need DATABASE_URL pointing at a database with the SA-18 demo data."""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

pytestmark = pytest.mark.skipif(not get_settings().database_url,
                                reason="DATABASE_URL not set")
client = TestClient(app)


def test_engineering_admission() -> None:
    body = client.get("/api/v1/programs/IIT-ING-GI/admission").json()
    assert body["entry_level"] == "bac+2"
    assert body["accepted_backgrounds"]["prepa_track"] == ["MP", "PC", "PT"]
    assert "Informatique de gestion" in body["accepted_backgrounds"]["licence_specialty"]
    assert body["campaign"]["status"] == "open"


def test_licence_admission_lists_bac_sections() -> None:
    body = client.get("/api/v1/programs/iit-lic-glsi/admission").json()
    assert body["accepted_backgrounds"]["bac_section"] == [
        "Math", "Sciences", "Informatique", "Economie et Gestion", "Technique"]


def test_eligibility() -> None:
    url = "/api/v1/programs/IIT-LIC-SEER/eligibility"
    yes = client.get(url, params={"kind": "bac_section", "value": "technique"}).json()
    assert yes["eligible"] is True
    no = client.get(url, params={"kind": "bac_section", "value": "Economie et Gestion"}).json()
    assert no["eligible"] is False
    unknown = client.get("/api/v1/programs/ISB-LN-DROIT/eligibility",
                         params={"kind": "bac_section", "value": "Math"}).json()
    assert unknown["eligible"] is None


def test_accents_are_ignored() -> None:
    body = client.get("/api/v1/programs/IIT-LIC-GLSI/eligibility",
                      params={"kind": "bac_section", "value": "Économie et gestion"}).json()
    assert body["eligible"] is True


def test_monthly_tariffs_with_estimate() -> None:
    body = client.get("/api/v1/programs/IIT-LIC-GLSI/tariffs").json()
    assert body["published"] is True
    national = next(t for t in body["tariffs"] if t["student_category"] == "national")
    assert Decimal(national["amount"]) == 667
    assert national["installments"] == 9
    assert Decimal(national["year_total_estimate"]) == 6003
    assert national["is_confirmed"] is False
    assert len(body["fee_rules"]) == 4


def test_program_without_published_fees() -> None:
    body = client.get("/api/v1/programs/ISB-MBA/tariffs").json()
    assert body["published"] is False
    assert body["tariffs"] == []
    assert "admissions office" in body["message"]


def test_campaigns() -> None:
    body = client.get("/api/v1/campaigns", params={"status": "open"}).json()
    assert {c["institution"] for c in body} == {"IIT", "ISB"}


def test_bad_inputs() -> None:
    assert client.get("/api/v1/programs/NOPE/tariffs").status_code == 404
    bad_year = client.get("/api/v1/programs/IIT-PREPA/tariffs", params={"academic_year": "2026"})
    assert bad_year.status_code == 422
    bad_kind = client.get("/api/v1/programs/IIT-PREPA/eligibility",
                          params={"kind": "age", "value": "18"})
    assert bad_kind.json()["error"]["code"] == "VALIDATION_ERROR"
