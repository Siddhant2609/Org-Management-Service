from fastapi import APIRouter, HTTPException, Header, status
from app.models.schemas import OrgCreate, OrgResponse, OrgUpdate
from app.services.org_service import OrganizationService
from typing import Optional
from app.utils.security import decode_token

router = APIRouter()


@router.post("/create", response_model=OrgResponse)
async def create_org(payload: OrgCreate):
    svc = OrganizationService()
    result = await svc.create_organization(payload.organization_name, payload.email, payload.password)
    return result


@router.get("/get", response_model=OrgResponse)
async def get_org(organization_name: str):
    svc = OrganizationService()
    org = await svc.get_organization(organization_name)
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    return org


@router.put("/update", response_model=OrgResponse)
async def update_org(payload: OrgUpdate):
    svc = OrganizationService()
    updated = await svc.update_organization(payload.organization_name, payload.new_organization_name, payload.email, payload.password)
    return updated


@router.delete("/delete")
async def delete_org(organization_name: str, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing auth token")
    token = authorization.split(" ")[-1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    requesting_email = payload.get("email")
    svc = OrganizationService()
    res = await svc.delete_organization(organization_name, requesting_email)
    return res
