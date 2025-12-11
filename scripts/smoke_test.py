"""Lightweight smoke test for the API.

Creates a temporary org, logs in the admin, then deletes the org.

Usage:
    $ python scripts/smoke_test.py

Set API_URL env var to point to a running API (default: http://localhost:8000).
"""

import os
import asyncio
import httpx
import time

API = os.getenv("API_URL", "http://localhost:8000")


async def main():
    async with httpx.AsyncClient(base_url=API, timeout=10) as client:
        org_name = f"acme_{int(time.time())}"
        print("Creating organization:", org_name)
        # use a safe email (local-part can include +) because some org_name values may contain underscores
        admin_email = f"admin+{org_name}@example.com"
        r = await client.post(
            "/org/create",
            json={"organization_name": org_name, "email": admin_email, "password": "Abc123"},
        )
        print("create status:", r.status_code, r.text)
        if r.status_code != 200:
            return

        print("Logging in as admin")
        r2 = await client.post("/admin/login", json={"email": admin_email, "password": "Abc123"})
        print("login status:", r2.status_code, r2.text)
        if r2.status_code != 200:
            return
        token = r2.json().get("access_token")

        print("Deleting organization using token")
        headers = {"Authorization": f"Bearer {token}"}
        r3 = await client.delete(f"/org/delete?organization_name={org_name}", headers=headers)
        print("delete status:", r3.status_code, r3.text)


if __name__ == "__main__":
    asyncio.run(main())
