"""Archived helper: create an org then fetch it via the API.

Kept for reference. This script is not used by CI; place any future
one-off dev helpers under `scripts/archived/`.

Usage:
    API_URL=http://localhost:8000 python scripts/archived/create_and_get.py
"""

import os
import httpx


def main():
    api = os.getenv("API_URL", "http://localhost:8000")
    org = os.getenv("ORG_NAME", "recheckorg")
    email = os.getenv("ADMIN_EMAIL", "admin+recheckorg@example.com")
    pw = os.getenv("ADMIN_PW", "Secret123")
    with httpx.Client(base_url=api, timeout=10) as c:
        r = c.post(
            "/org/create", json={"organization_name": org, "email": email, "password": pw}
        )
        print("CREATE", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)

        r2 = c.get(f"/org/get?organization_name={org}")
        print("GET", r2.status_code)
        try:
            print(r2.json())
        except Exception:
            print(r2.text)


if __name__ == "__main__":
    main()
