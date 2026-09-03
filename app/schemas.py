from datetime import date as date_type, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)
    college: str | None = None
    branch: str | None = None
    year: int | None = Field(default=None, ge=1, le=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StudentProfileUpdate(BaseModel):
    name: str | None = None
    college: str | None = None
    branch: str | None = None
    year: int | None = Field(default=None, ge=1, le=10)


class StudentOut(ORMModel):
    id: int
    name: str
    email: EmailStr
    college: str | None
    branch: str | None
    year: int | None
    career_goal: str | None


class SkillCreate(BaseModel):
    skill_id: int
    current_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(default=0, ge=0, le=100)


class SkillOut(ORMModel):
    id: int
    skill_id: int
    current_score: float
    confidence_score: float
    last_updated: datetime
    skill_name: str | None = None
    category: str | None = None


class SkillCatalogOut(ORMModel):
    id: int
    name: str
    category: str
    description: str | None


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    technologies: str | None = None
    date: date_type | None = None
    status: str = "in_progress"


class ProjectOut(ORMModel):
    id: int
    student_id: int
    title: str
    description: str | None
    technologies: str | None
    date: date_type | None
    status: str


class CertificationCreate(BaseModel):
    name: str
    issuing_organization: str | None = None
    date: date_type | None = None
    verification_status: str = "pending"


class CertificationOut(ORMModel):
    id: int
    student_id: int
    name: str
    issuing_organization: str | None
    date: date_type | None
    verification_status: str


class CareerOut(ORMModel):
    id: int
    name: str
    description: str | None


class CareerSkillOut(BaseModel):
    skill_id: int
    skill_name: str
    required_score: float
    importance: float


class CareerGoalRequest(BaseModel):
    career_id: int


class AssessmentCreate(BaseModel):
    skill_id: int
    score: float = Field(ge=0, le=100)
    date: date_type | None = None


class AssessmentOut(ORMModel):
    id: int
    student_id: int
    skill_id: int
    score: float
    date: date_type


class GapOut(BaseModel):
    skill_id: int
    skill_name: str
    current_score: float
    required_score: float
    gap: float
    importance: float
    priority: str
    status: str


class RoadmapStep(BaseModel):
    skill_name: str
    priority: str
    steps: list[str]


class FacultyOut(ORMModel):
    id: int
    name: str
    email: EmailStr
    department: str | None


class ProgressOut(BaseModel):
    skill_id: int
    skill_name: str
    latest_score: float
    previous_score: float | None
    change: float | None
    last_updated: date_type | None
    stagnant: bool
