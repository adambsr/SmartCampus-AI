"""SA-22: check every catalog / admission endpoint on a RUNNING server.

Start the API first (from backend/):  python -m uvicorn app.main:app
Then in a second terminal:            python scripts/smoke_test.py
Another server:                       python scripts/smoke_test.py --base-url https://...

Works on any database loaded with the SA-18 demo data. Exit code 0 = all checks passed.
"""
import argparse
import sys
import time

import httpx

CHECKS = []


def check(name):
    def wrap(fn):
        CHECKS.append((name, fn))
        return fn
    return wrap


def get(c, path, **params):
    return c.get("/api/v1" + path, params=params)


@check("health answers ok")
def _(c):
    assert get(c, "/health").json()["status"] == "ok"


@check("2 institutions: IIT 15 programs, ISB 16")
def _(c):
    body = get(c, "/institutions").json()
    assert {i["code"]: i["program_count"] for i in body} == {"IIT": 15, "ISB": 16}, body


@check("catalog lists 31 programs")
def _(c):
    assert get(c, "/programs", limit=100).json()["total"] == 31


@check("filter: 5 IIT engineering programs")
def _(c):
    assert get(c, "/programs", institution="IIT", level="ingenieur").json()["total"] == 5


@check("paging: limit=10 offset=30 returns 1 program")
def _(c):
    body = get(c, "/programs", limit=10, offset=30).json()
    assert body["total"] == 31 and len(body["items"]) == 1, body


@check("search q=informatique finds Génie Informatique")
def _(c):
    codes = [p["code"] for p in get(c, "/programs", q="informatique").json()["items"]]
    assert "IIT-ING-GI" in codes, codes


@check("program detail with pathways (Prépa -> 5 engineering)")
def _(c):
    body = get(c, "/programs/IIT-PREPA").json()
    assert len(body["leads_to"]) == 5, body["leads_to"]


@check("unknown program -> 404 PROGRAM_NOT_FOUND")
def _(c):
    r = get(c, "/programs/NOPE")
    assert r.status_code == 404 and r.json()["error"]["code"] == "PROGRAM_NOT_FOUND"


@check("admission: GI accepts Prépa MP/PC/PT + 24 licences")
def _(c):
    bg = get(c, "/programs/IIT-ING-GI/admission").json()["accepted_backgrounds"]
    assert bg["prepa_track"] == ["MP", "PC", "PT"] and len(bg["licence_specialty"]) == 24, bg


@check("eligibility: Bac Technique accepted in SEER")
def _(c):
    assert get(c, "/programs/IIT-LIC-SEER/eligibility",
               kind="bac_section", value="Technique").json()["eligible"] is True


@check("eligibility: Bac Eco-Gestion refused in SEER")
def _(c):
    assert get(c, "/programs/IIT-LIC-SEER/eligibility",
               kind="bac_section", value="Economie et Gestion").json()["eligible"] is False


@check("tariffs GLSI 2026-2027: 667 TND x 9, unconfirmed")
def _(c):
    body = get(c, "/programs/IIT-LIC-GLSI/tariffs", academic_year="2026-2027").json()
    nat = next(t for t in body["tariffs"] if t["student_category"] == "national")
    assert float(nat["amount"]) == 667 and nat["installments"] == 9 and not nat["is_confirmed"], nat


@check("no published fee -> published=false (ISB MBA)")
def _(c):
    assert get(c, "/programs/ISB-MBA/tariffs").json()["published"] is False


@check("bad year -> 422 VALIDATION_ERROR")
def _(c):
    r = get(c, "/programs/IIT-LIC-GLSI/tariffs", academic_year="1")
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


@check("2 open campaigns")
def _(c):
    assert len(get(c, "/campaigns", status="open").json()) == 2


@check("every response carries X-Request-ID")
def _(c):
    assert get(c, "/programs", limit=1).headers.get("x-request-id")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    base = ap.parse_args().base_url
    failed = 0
    with httpx.Client(base_url=base, timeout=15) as c:
        try:
            c.get("/api/v1/health")
        except httpx.HTTPError:
            print(f"Cannot reach {base}. Start the server first: python -m uvicorn app.main:app")
            return 2
        for name, fn in CHECKS:
            start = time.perf_counter()
            try:
                fn(c)
                status = "PASS"
            except Exception as exc:  # noqa: BLE001 - report any failure
                status, failed = f"FAIL  {exc!r}"[:200], failed + 1
            print(f"{(time.perf_counter() - start) * 1000:6.0f} ms  {name:55} {status}")
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
