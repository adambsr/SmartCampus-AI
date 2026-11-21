from pydantic import BaseModel


class Institution(BaseModel):
    code: str
    name: str
    city: str | None = None
    website: str | None = None
    program_count: int


class ProgramSummary(BaseModel):
    code: str
    name: str
    institution: str
    level: str
    program_type: str | None = None
    field: str | None = None
    duration_years: int | None = None
    teaching_language: str
    labels: list[str] = []
    source_url: str | None = None


class ProgramList(BaseModel):
    total: int
    items: list[ProgramSummary]


class Specialization(BaseModel):
    name: str
    description: str | None = None


class PathwayLink(BaseModel):
    code: str
    name: str
    condition: str | None = None


class ProgramDetail(ProgramSummary):
    institution_name: str
    credits: int | None = None
    start_month: int | None = None
    description: str | None = None
    career_outcomes: list[str] = []
    key_modules: list[str] = []
    specializations: list[Specialization] = []
    leads_to: list[PathwayLink] = []
    reachable_from: list[PathwayLink] = []
