from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional
from datetime import datetime

# Organization name must be alphanumeric with optional - or _ and between 2 and 64 chars
# pydantic v2 uses `pattern` parameter for regex-like constraint
OrgName = constr(strip_whitespace=True, min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class OrgCreate(BaseModel):
    organization_name: OrgName
    email: EmailStr
    password: constr(min_length=6)


class OrgUpdate(BaseModel):
    organization_name: OrgName
    new_organization_name: Optional[OrgName] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=6)] = None

    @validator("new_organization_name")
    def not_same_as_old(cls, v, values):
        if v and "organization_name" in values and v == values["organization_name"]:
            raise ValueError("new_organization_name must be different from organization_name")
        return v


class OrgResponse(BaseModel):
    organization_name: str
    collection_name: str
    admin_email: EmailStr
    created_at: datetime


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
