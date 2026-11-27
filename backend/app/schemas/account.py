from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["candidate", "interviewer", "admin"]
StaffRole = Literal["interviewer", "admin"]


class AccountPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    institution_id: int | None
    is_active: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = 900
    user: AccountPublic


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(max_length=128)


class ActivateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invitation_token: str = Field(min_length=40, max_length=150)
    password: str = Field(min_length=12, max_length=128)


class StaffCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    role: StaffRole
    institution_id: int | None = None


class AccountUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: StaffRole | None = None
    institution_id: int | None = None
    is_active: bool | None = None


class AccountListResponse(BaseModel):
    items: list[AccountPublic]


class InvitationResponse(BaseModel):
    invitation_token: str
    expires_at: datetime


class CandidateProfileResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    birth_year: int | None
    city: str | None
    nationality: str | None
    current_level: str | None
    bac_section: str | None
    bac_year: int | None
    bac_average: str | None
    last_diploma: str | None
    last_diploma_specialty: str | None
    favorite_subjects: list[str] | None
    interests: list[str] | None
    career_goal: str | None
    constraints: str | None
    preferred_language: str


class CandidateApplication(BaseModel):
    id: int
    program_id: int
    program_name: str
    institution_code: str
    status: str
    consent_at: datetime | None
    submitted_at: datetime | None


class CandidateApplicationsResponse(BaseModel):
    items: list[CandidateApplication]
