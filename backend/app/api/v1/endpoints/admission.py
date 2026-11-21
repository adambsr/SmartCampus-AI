"""SA-21: admission rules, eligibility, fees and campaigns (read-only)."""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from psycopg import Connection

from app.db.session import get_db
from app.schemas.admission import Admission, Campaign, Eligibility, ProgramTariffs
from app.services import admission as service

router = APIRouter()

BackgroundKind = Literal["bac_section", "prepa_track", "licence_specialty", "diploma"]


@router.get("/programs/{code}/admission", response_model=Admission,
            summary="How to enter a program")
def get_admission(code: str, db: Connection = Depends(get_db)):
    return service.get_admission(db, code)


@router.get("/programs/{code}/eligibility", response_model=Eligibility,
            summary="Is this background accepted for the program?")
def check_eligibility(
    code: str,
    kind: BackgroundKind = Query(..., description="bac_section, prepa_track, licence_specialty or diploma"),
    value: str = Query(..., min_length=1, description="e.g. 'Math', 'MP', 'Informatique de gestion'"),
    db: Connection = Depends(get_db),
):
    return service.check_eligibility(db, code, kind, value)


@router.get("/programs/{code}/tariffs", response_model=ProgramTariffs,
            summary="Fees and fee rules for a program")
def get_tariffs(
    code: str,
    academic_year: str | None = Query(None, pattern=r"^\d{4}-\d{4}$", examples=["2026-2027"]),
    db: Connection = Depends(get_db),
):
    return service.get_tariffs(db, code, academic_year)


@router.get("/campaigns", response_model=list[Campaign], summary="Admission campaigns")
def list_campaigns(
    institution: str | None = Query(None, description="IIT or ISB"),
    status: Literal["planned", "open", "closed"] | None = Query(None),
    db: Connection = Depends(get_db),
):
    return service.list_campaigns(db, institution, status)
