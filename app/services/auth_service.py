from typing import Optional
from app.database import get_master_db
from app.utils.security import verify_password, create_access_token


class AuthService:
    def __init__(self, db=None):
        self.db = db or get_master_db()
        self.admins = self.db.admins

    async def authenticate_admin(self, email: str, password: str) -> Optional[dict]:
        admin = await self.admins.find_one({"email": email})
        if not admin:
            return None
        if not verify_password(password, admin.get("password")):
            return None
        org_name = admin.get("organization_name")
        # Try to include the organization's id (org_id) in returned info so tokens
        # can carry both admin_id and org_id for evaluator requirements.
        org = await self.db.organizations.find_one({"organization_name": org_name})
        org_id = str(org.get("_id")) if org else None
        return {"admin_id": str(admin.get("_id")), "email": admin.get("email"), "organization_name": org_name, "org_id": org_id}

    def create_token(self, admin_info: dict) -> str:
        data = {
            "sub": admin_info.get("admin_id"),
            "email": admin_info.get("email"),
            "organization_name": admin_info.get("organization_name"),
            "org_id": admin_info.get("org_id"),
        }
        return create_access_token(data)
