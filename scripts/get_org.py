import os
import httpx
API = os.getenv('API_URL','http://localhost:8000')
org='evalorg_1765488793'
with httpx.Client(base_url=API, timeout=10) as c:
    r=c.get(f'/org/get?organization_name={org}')
    print('GET /org/get', r.status_code, r.text)

"""Pointer removed — use archived helper.

This file is intentionally minimal to avoid accidental use. For the
original helper, see `scripts/archived/get_org.py`.
"""

def main():
    print("Use scripts/archived/get_org.py instead.")


if __name__ == "__main__":
    main()


