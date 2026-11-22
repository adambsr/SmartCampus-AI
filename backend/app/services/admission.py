"""Admission and fees queries (SA-21)."""
import unicodedata
from typing import Any

from psycopg import Connection

from app.core.errors import AppError

KINDS = ("bac_section", "prepa_track", "licence_specialty", "diploma")


def _program(conn: Connection, code: str) -> dict[str, Any]:
    row = conn.execute(
        """SELECT p.id, p.code, p.name, p.institution_id, i.code AS institution
           FROM program p JOIN institution i ON i.id = p.institution_id
           WHERE p.code = upper(%s) AND p.is_active""",
        (code,),
    ).fetchone()
    if row is None:
        raise AppError(code="PROGRAM_NOT_FOUND", message=f"No program with code {code}.",
                       status_code=404)
    return row


def _norm(text: str) -> str:
    """Lowercase without accents, so 'Économie' matches 'Economie'."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def list_campaigns(conn: Connection, institution: str | None = None,
                   status: str | None = None) -> list[dict[str, Any]]:
    where, params = [], {}
    if institution:
        where.append("i.code = upper(%(institution)s)")
        params["institution"] = institution
    if status:
        where.append("c.status = %(status)s::campaign_status")
        params["status"] = status
    sql = """SELECT i.code AS institution, c.academic_year, c.opens_at, c.closes_at,
                    c.status::text AS status
             FROM admission_campaign c JOIN institution i ON i.id = c.institution_id"""
    if where:
        sql += " WHERE " + " AND ".join(where)
    return conn.execute(sql + " ORDER BY c.academic_year DESC, i.code", params).fetchall()


def get_admission(conn: Connection, code: str) -> dict[str, Any]:
    prog = _program(conn, code)
    req = conn.execute(
        """SELECT id, entry_level::text AS entry_level, COALESCE(selection_steps, '{}') AS selection_steps,
                  min_average, language_requirement,
                  COALESCE(required_documents, '{}') AS required_documents, notes, source_url
           FROM admission_requirement WHERE program_id = %s""",
        (prog["id"],),
    ).fetchone()
    if req is None:
        raise AppError(code="ADMISSION_NOT_FOUND",
                       message=f"No admission rules recorded for {prog['code']}.", status_code=404)
    backgrounds: dict[str, list[str]] = {k: [] for k in KINDS}
    for row in conn.execute(
        "SELECT kind::text AS kind, value FROM accepted_background WHERE requirement_id = %s ORDER BY id",
        (req.pop("id"),),
    ):
        backgrounds[row["kind"]].append(row["value"])
    campaign = conn.execute(
        """SELECT %s AS institution, academic_year, opens_at, closes_at, status::text AS status
           FROM admission_campaign WHERE institution_id = %s
           ORDER BY (status = 'open') DESC, academic_year DESC LIMIT 1""",
        (prog["institution"], prog["institution_id"]),
    ).fetchone()
    return {"program_code": prog["code"], "program_name": prog["name"], **req,
            "accepted_backgrounds": backgrounds, "campaign": campaign}


def check_eligibility(conn: Connection, code: str, kind: str, value: str) -> dict[str, Any]:
    admission = get_admission(conn, code)
    accepted = admission["accepted_backgrounds"][kind]
    result = {"program_code": admission["program_code"], "kind": kind, "value": value}
    if not accepted:
        has_any = any(admission["accepted_backgrounds"].values())
        return {**result, "eligible": False if has_any else None,
                "reason": ("This program does not list this kind of background."
                           if has_any else
                           "No list of accepted backgrounds is published; ask the admissions office.")}
    match = _norm(value) in {_norm(a) for a in accepted}
    return {**result, "eligible": match,
            "reason": ("Listed among the accepted backgrounds." if match
                       else "Not in the published list of accepted backgrounds.")}


def get_tariffs(conn: Connection, code: str, academic_year: str | None = None) -> dict[str, Any]:
    prog = _program(conn, code)
    params: dict[str, Any] = {"pid": prog["id"]}
    sql = """SELECT academic_year, student_category::text AS student_category, amount, currency,
                    period::text AS period, installments,
                    CASE WHEN period = 'month' AND installments IS NOT NULL
                         THEN amount * installments END AS year_total_estimate,
                    is_confirmed, notes, source_url
             FROM tariff WHERE program_id = %(pid)s"""
    if academic_year:
        sql += " AND academic_year = %(year)s"
        params["year"] = academic_year
    tariffs = conn.execute(sql + " ORDER BY academic_year DESC, student_category", params).fetchall()
    rules = conn.execute(
        "SELECT rule, percent, source_url FROM fee_rule WHERE institution_id = %s ORDER BY id",
        (prog["institution_id"],),
    ).fetchall()
    if not tariffs:
        message = "No fee is published for this program; ask the admissions office."
    elif all(t["is_confirmed"] for t in tariffs):
        message = "Official fees."
    else:
        message = "Fees as shown on the website, not yet confirmed by the admissions office."
    return {"program_code": prog["code"], "program_name": prog["name"], "published": bool(tariffs),
            "tariffs": tariffs, "fee_rules": rules, "message": message}
