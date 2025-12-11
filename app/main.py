from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routers.org_router import router as org_router
from app.routers.auth_router import router as auth_router
from app.database import ensure_indexes
from app.errors import AppError

import importlib
import types
import os


app = FastAPI(title="Org Management Service")


@app.on_event("startup")
async def on_startup():
    # ensure DB indexes exist
    try:
        await ensure_indexes()
    except Exception:
        print("warning: failed to ensure indexes at startup")

    # runtime shim: some bcrypt wheels (platform builds) don't expose the
    # `__about__` attribute that passlib's bcrypt handler sometimes reads.
    # This is harmless but noisy; if missing, add a minimal shim so passlib
    # can probe the module without raising AttributeError during backend
    # detection.
    try:
        bcrypt = importlib.import_module("bcrypt")
        if not hasattr(bcrypt, "__about__"):
            bcrypt.__about__ = types.SimpleNamespace(__version__=getattr(bcrypt, "__version__", None))
    except Exception:
        # don't fail startup on this; bcrypt may not be installed in some envs
        pass

    # Optionally enforce a non-default JWT secret. This is disabled by default
    # to avoid breaking local development. Set REQUIRE_JWT_SECRET=1 in your
    # production environment to fail startup when a weak/default secret is used.
    from app.utils.security import SECRET_KEY
    if os.getenv("REQUIRE_JWT_SECRET", "0") == "1":
        if not SECRET_KEY or SECRET_KEY == "change-me-in-prod":
            raise RuntimeError("JWT_SECRET is not set or uses the default value. Set environment variable JWT_SECRET to a strong secret and restart (or unset REQUIRE_JWT_SECRET to disable this check).")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    # Return a structured JSON error body for all AppError instances
    payload = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }
    if getattr(exc, "details", None) is not None:
        payload["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Fallback: avoid leaking internals, return a generic 500 structure
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "internal server error"}})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Return validation errors in the same structured error format
    try:
        raw = exc.errors()
        # Normalize to a compact list of {loc, msg, type}
        details = []
        for e in raw:
            details.append({
                "loc": e.get("loc"),
                "msg": e.get("msg"),
                "type": e.get("type"),
            })
    except Exception:
        details = [{"msg": str(exc)}]
    payload = {
        "error": {
            "code": "validation_error",
            "message": "request validation failed",
            "details": details,
        }
    }
    return JSONResponse(status_code=422, content=payload)



@app.get("/health")
async def health():
    # check DB connectivity for readiness
    from app.database import get_master_db
    db = get_master_db()
    try:
        await db.command({"ping": 1})
        return {"status": "ok", "db": "ok"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable", "db": "unavailable"})


# include modular routers
app.include_router(org_router, prefix="/org")
app.include_router(auth_router, prefix="/admin")
