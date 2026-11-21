from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class Campaign(BaseModel):
    institution: str
    academic_year: str
    opens_at: date | None = None
    closes_at: date | None = None
    status: str


class AcceptedBackgrounds(BaseModel):
    bac_section: list[str] = []
    prepa_track: list[str] = []
    licence_specialty: list[str] = []
    diploma: list[str] = []


class Admission(BaseModel):
    program_code: str
    program_name: str
    entry_level: str
    selection_steps: list[str] = []
    min_average: Decimal | None = None
    language_requirement: str | None = None
    required_documents: list[str] = []
    notes: str | None = None
    source_url: str | None = None
    accepted_backgrounds: AcceptedBackgrounds
    campaign: Campaign | None = None


class Eligibility(BaseModel):
    program_code: str
    kind: str
    value: str
    eligible: bool | None
    reason: str


class Tariff(BaseModel):
    academic_year: str
    student_category: str
    amount: Decimal
    currency: str
    period: str
    installments: int | None = None
    year_total_estimate: Decimal | None = None
    is_confirmed: bool
    notes: str | None = None
    source_url: str | None = None


class FeeRule(BaseModel):
    rule: str
    percent: Decimal | None = None
    source_url: str | None = None


class ProgramTariffs(BaseModel):
    program_code: str
    program_name: str
    published: bool
    tariffs: list[Tariff]
    fee_rules: list[FeeRule]
    message: str
