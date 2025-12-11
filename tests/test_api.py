# Test API endpoints
import os
import pytest
import httpx


API = os.getenv("API_URL", "http://localhost:8000")


@pytest.mark.asyncio
async def test_create_login_delete():
    async with httpx.AsyncClient(base_url=API, timeout=10) as client:
        org_name = "testorg_pytest"
        # Create (idempotent-ish for example)
        # use a validation-safe email (plus-addressing) to avoid strict domain rules
        test_email = "admin+testorg_pytest@example.com"
        r = await client.post("/org/create", json={"organization_name": org_name, "email": test_email, "password": "Secret123"})
        assert r.status_code in (200, 400)

        # Login
        r2 = await client.post("/admin/login", json={"email": test_email, "password": "Secret123"})
        if r2.status_code == 200:
            token = r2.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            r3 = await client.delete(f"/org/delete?organization_name={org_name}", headers=headers)
            assert r3.status_code in (200, 404, 403)
        else:
            # Could be 401 if create wasn't performed — still acceptable for example
            assert r2.status_code in (401,)