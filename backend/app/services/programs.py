"""Catalog queries (SA-20): institutions and programs."""
from typing import Any

from psycopg import Connection

from app.core.errors import AppError

LEVELS = ("prepa", "licence", "ingenieur", "mastere", "mba", "architecture")

_SUMMARY = """
    p.code, p.name, i.code AS institution, p.level::text AS level, p.program_type, p.field,
    p.duration_years, p.teaching_language, COALESCE(p.labels, '{}') AS labels, p.source_url
"""


def list_institutions(conn: Connection) -> list[dict[str, Any]]:
    return conn.execute(
        """SELECT i.code, i.name, i.city, i.website,
                  count(p.id) FILTER (WHERE p.is_active) AS program_count
           FROM institution i LEFT JOIN program p ON p.institution_id = i.id
           GROUP BY i.id ORDER BY i.code"""
    ).fetchall()


def list_programs(
    conn: Connection,
    *,
    institution: str | None = None,
    level: str | None = None,
    field: str | None = None,
    language: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    where = ["p.is_active"]
    params: dict[str, Any] = {}
    if institution:
        where.append("i.code = upper(%(institution)s)")
        params["institution"] = institution
    if level:
        where.append("p.level = %(level)s::program_level")
        params["level"] = level
    if field:
        where.append("p.field ILIKE %(field)s")
        params["field"] = f"%{field}%"
    if language:
        where.append("p.teaching_language = lower(%(language)s)")
        params["language"] = language
    if q:
        where.append("(p.name ILIKE %(q)s OR p.code ILIKE %(q)s OR p.field ILIKE %(q)s"
                     " OR p.description ILIKE %(q)s)")
        params["q"] = f"%{q}%"
    base = "FROM program p JOIN institution i ON i.id = p.institution_id WHERE " + " AND ".join(where)
    total = conn.execute("SELECT count(*) AS n " + base, params).fetchone()["n"]
    items = conn.execute(
        f"SELECT {_SUMMARY} {base} ORDER BY i.code, p.level, p.name"
        " LIMIT %(limit)s OFFSET %(offset)s",
        {**params, "limit": limit, "offset": offset},
    ).fetchall()
    return {"total": total, "items": items}


def get_program(conn: Connection, code: str) -> dict[str, Any]:
    row = conn.execute(
        f"""SELECT p.id, {_SUMMARY}, i.name AS institution_name, p.credits, p.start_month,
                   p.description, COALESCE(p.career_outcomes, '{{}}') AS career_outcomes,
                   COALESCE(p.key_modules, '{{}}') AS key_modules
            FROM program p JOIN institution i ON i.id = p.institution_id
            WHERE p.code = upper(%s) AND p.is_active""",
        (code,),
    ).fetchone()
    if row is None:
        raise AppError(code="PROGRAM_NOT_FOUND", message=f"No program with code {code}.",
                       status_code=404)
    pid = row.pop("id")
    row["specializations"] = conn.execute(
        "SELECT name, description FROM specialization WHERE program_id = %s ORDER BY name",
        (pid,),
    ).fetchall()
    row["leads_to"] = conn.execute(
        """SELECT p.code, p.name, w.condition FROM pathway w
           JOIN program p ON p.id = w.to_program_id WHERE w.from_program_id = %s ORDER BY p.code""",
        (pid,),
    ).fetchall()
    row["reachable_from"] = conn.execute(
        """SELECT p.code, p.name, w.condition FROM pathway w
           JOIN program p ON p.id = w.from_program_id WHERE w.to_program_id = %s ORDER BY p.code""",
        (pid,),
    ).fetchall()
    return row
