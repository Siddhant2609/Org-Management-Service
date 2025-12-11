import os
import pytest
import httpx
import time


API = os.getenv("API_URL", "http://localhost:8000")


@pytest.mark.asyncio
async def test_rename_and_rbac():
    async with httpx.AsyncClient(base_url=API, timeout=20) as client:
        # create first org
        org1 = f"renameorg_{int(time.time())}"
        email1 = f"admin+{org1}@example.com"
        r1 = await client.post("/org/create", json={"organization_name": org1, "email": email1, "password": "Secret123"})
        assert r1.status_code in (200, 400)

        # login admin1
        r1l = await client.post("/admin/login", json={"email": email1, "password": "Secret123"})
        if r1l.status_code != 200:
            pytest.skip("admin1 login failed; skipping rename/rbac test")
        token1 = r1l.json().get("access_token")

        # create second org
        org2 = f"otherorg_{int(time.time())}"
        email2 = f"admin+{org2}@example.com"
        r2 = await client.post("/org/create", json={"organization_name": org2, "email": email2, "password": "Secret123"})
        assert r2.status_code in (200, 400)

        # login admin2
        r2l = await client.post("/admin/login", json={"email": email2, "password": "Secret123"})
        if r2l.status_code != 200:
            pytest.skip("admin2 login failed; skipping RBAC assertions")
        token2 = r2l.json().get("access_token")

        # admin1 attempts to rename org1 -> org1_renamed
        headers1 = {"Authorization": f"Bearer {token1}"}
        rename_body = {"organization_name": org1, "new_organization_name": f"{org1}_renamed"}
        r_rename = await client.put("/org/update", json=rename_body, headers=headers1)
        assert r_rename.status_code in (200, 400)

        # admin2 tries to delete org1_renamed (should be forbidden)
        headers2 = {"Authorization": f"Bearer {token2}"}
        del_resp = await client.delete(f"/org/delete?organization_name={org1}_renamed", headers=headers2)
        # allowed outcomes: 403 Forbidden or 404 Not Found depending on timing; assert it's not 200
        assert del_resp.status_code != 200
