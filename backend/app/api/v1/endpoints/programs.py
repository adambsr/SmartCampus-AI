"""SA-20: catalog endpoints, read-only, used by the frontend and the AI agent."""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from psycopg import Connection

from app.db.session import get_db
from app.schemas.program import Institution, ProgramDetail, ProgramList
from app.services import programs as service

router = APIRouter()

Level = Literal["prepa", "licence", "ingenieur", "mastere", "mba", "architecture"]


@router.get("/institutions", response_model=list[Institution], summary="List IIT and ISB")
def list_institutions(db: Connection = Depends(get_db)):
    return service.list_institutions(db)


@router.get("/programs", response_model=ProgramList, summary="Search the program catalog")
def list_programs(
    institution: str | None = Query(None, description="IIT or ISB"),
    level: Level | None = Query(None),
    field: str | None = Query(None, description="Part of the field, e.g. 'informatique'"),
    language: str | None = Query(None, description="Teaching language: fr or en"),
    q: str | None = Query(None, min_length=2, description="Free text in name, code, field"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Connection = Depends(get_db),
):
    return service.list_programs(db, institution=institution, level=level, field=field,
                                 language=language, q=q, limit=limit, offset=offset)


@router.get("/programs/{code}", response_model=ProgramDetail, summary="One program in detail")
def get_program(code: str, db: Connection = Depends(get_db)):
    return service.get_program(db, code)
