"""Archived helper: fetch organization via API.

This script is preserved for reference. It performs a simple GET against
`/org/get?organization_name=NAME`. It is not used by the test suite or CI
and is kept under scripts/archived for clarity.

Usage:
    API_URL=http://localhost:8000 python scripts/archived/get_org.py
"""

import os
import httpx


def main():
    api = os.getenv("API_URL", "http://localhost:8000")
    org = os.getenv("ORG_NAME", "evalorg_1765488793")
    with httpx.Client(base_url=api, timeout=10) as c:
        r = c.get(f"/org/get?organization_name={org}")
        print("GET /org/get", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)


if __name__ == "__main__":
    main()
