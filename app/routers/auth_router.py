from fastapi import APIRouter, HTTPException, status
from app.models.schemas import AdminLogin, Token
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=Token)
async def admin_login(payload: AdminLogin):
    auth = AuthService()
    admin_info = await auth.authenticate_admin(payload.email, payload.password)
    if not admin_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = auth.create_token(admin_info)
    return {"access_token": token, "token_type": "bearer"}
