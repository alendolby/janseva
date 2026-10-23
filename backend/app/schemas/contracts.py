from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
RoleName = Literal["CITIZEN", "OFFICE", "ADMIN"]
Severity = Literal["Low", "Moderate", "High", "Critical"]
class Register(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    @field_validator("password")
    @classmethod
    def password_policy(cls, v):
        if not (any(x.isupper() for x in v) and any(x.islower() for x in v) and any(x.isdigit() for x in v)):
            raise ValueError("Use at least 12 characters with upper case, lower case and a number")
        return v
class Login(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)
class AuthRequest(BaseModel):
    email: EmailStr
class TokenUse(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str | None = Field(default=None, min_length=12, max_length=128)
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; email: str; name: str; role: RoleName; office_id: str | None
    active: bool; verified: bool
class AuthOut(BaseModel):
    access_token: str; token_type: str = "bearer"; user: UserOut
class Message(BaseModel):
    message: str
class ProfileEdit(BaseModel):
    name: str = Field(min_length=2, max_length=100)
class CaseCreate(BaseModel):
    title: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=15, max_length=5000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str = Field(min_length=3, max_length=255)
    category_id: str | None = None
class Action(BaseModel):
    note: str = Field(default="", max_length=5000)
    office_id: str | None = None
    officer_id: str | None = None
    category_id: str | None = None
class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(max_length=2000)
class UserEdit(BaseModel):
    active: bool | None = None
    role: RoleName | None = None
    office_id: str | None = None
class RuleIn(BaseModel):
    category_id: str; ward_id: str; office_id: str
    active: bool = True
    source: str = Field(min_length=5, max_length=255)
    verified: bool = False
class PolicyIn(BaseModel):
    category_id: str; severity: Severity
    hours: int = Field(gt=0, le=8760)
    warning_hours: int = Field(ge=0)
    escalation_office_id: str | None = None
class DepartmentIn(BaseModel):
    name: str = Field(min_length=3, max_length=120)
class OfficeIn(DepartmentIn):
    department_id: str; local_body_id: str; parent_office_id: str | None = None
class DistrictIn(DepartmentIn):
    pass
class LocalBodyIn(DepartmentIn):
    district_id: str
class WardIn(DepartmentIn):
    local_body_id: str
    boundary: dict
    source: str = Field(min_length=5, max_length=255)
    verified: bool = False
class TextIn(BaseModel):
    text: str = Field(min_length=10, max_length=5000)
class DuplicateIn(TextIn):
    category_id: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
class CaseOut(BaseModel):
    public_case_id: str; title: str; description: str; status: str; priority: str
    severity_score: int; category_id: str | None; category: str | None
    assigned_office_id: str | None; office: str | None; assigned_officer_id: str | None
    routing_review_required: bool; sla_deadline: str | None
    created_at: str; updated_at: str; resolved_at: str | None; resolution_note: str | None
class CasePage(BaseModel):
    items: list[CaseOut]; total: int; page: int; size: int
