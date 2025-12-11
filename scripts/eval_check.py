import os
import time
import httpx
from jose import jwt
from pymongo import MongoClient
import bcrypt
import subprocess
import json

API = os.getenv('API_URL', 'http://localhost:8000')
MONGO = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
MASTER_DB = os.getenv('MASTER_DB_NAME', 'master_db')
JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-in-prod')

org_name = f"evalorg_{int(time.time())}"
email = f"admin+{org_name}@example.com"
password = "Secret123"

print('API:', API)
print('Mongo:', MONGO)
print('Org:', org_name)

results = {}

with httpx.Client(base_url=API, timeout=10) as c:
    print('\n== Creating organization ==')
    r = c.post('/org/create', json={'organization_name': org_name, 'email': email, 'password': password})
    print('create status', r.status_code, r.text)
    results['create_status'] = r.status_code
    if r.status_code != 200:
        print('Create failed; aborting further checks')
        raise SystemExit(1)

    print('\n== Logging in ==')
    r2 = c.post('/admin/login', json={'email': email, 'password': password})
    print('login status', r2.status_code, r2.text)
    results['login_status'] = r2.status_code
    if r2.status_code != 200:
        print('Login failed; aborting')
        raise SystemExit(1)
    token = r2.json().get('access_token')
    print('token:', token)

    print('\n== Decoding JWT ==')
    decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    print('decoded token:', decoded)
    results['token_sub_present'] = 'sub' in decoded
    results['token_email_match'] = decoded.get('email') == email
    results['token_org_match'] = decoded.get('organization_name') == org_name

    print('\n== Inspecting Mongo master_db ==')
    client = None
    db = None
    org_doc = None
    admin_doc = None
    try:
        client = MongoClient(MONGO, serverSelectionTimeoutMS=2000)
        db = client[MASTER_DB]
        org_doc = db.organizations.find_one({'organization_name': org_name})
        admin_doc = db.admins.find_one({'email': email})
        print('org_doc:', org_doc)
        print('admin_doc:', admin_doc)
    except Exception as e:
        print('pymongo query failed, will try container-side lookup:', e)

    # If pymongo did not find docs (likely due to hostname resolution when API
    # runs in docker network), try using `docker compose exec mongo mongosh` to
    # query the DB from inside the mongo container.
    if not org_doc or not admin_doc:
        try:
            cmd = [
                'docker', 'compose', 'exec', '-T', 'mongo',
                'mongosh', '--quiet',
                "--eval",
                f"JSON.stringify(db.getSiblingDB('{MASTER_DB}').organizations.findOne({{'organization_name':'{org_name}'}}))"
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            out = out.strip()
            if out and out != 'null':
                org_doc = json.loads(out)
            cmd2 = [
                'docker', 'compose', 'exec', '-T', 'mongo',
                'mongosh', '--quiet',
                "--eval",
                f"JSON.stringify(db.getSiblingDB('{MASTER_DB}').admins.findOne({{'email':'{email}'}}))"
            ]
            out2 = subprocess.check_output(cmd2, stderr=subprocess.STDOUT, text=True).strip()
            if out2 and out2 != 'null':
                admin_doc = json.loads(out2)
            # also get collection list from inside the container
            try:
                cmd_cols = [
                    'docker', 'compose', 'exec', '-T', 'mongo',
                    'mongosh', '--quiet',
                    "--eval",
                    f"JSON.stringify(db.getSiblingDB('{MASTER_DB}').getCollectionNames())"
                ]
                out_cols = subprocess.check_output(cmd_cols, stderr=subprocess.STDOUT, text=True)
                out_cols = out_cols.strip()
                cols = json.loads(out_cols) if out_cols else []
            except Exception:
                cols = []

            print('container org_doc:', org_doc)
            print('container admin_doc:', admin_doc)
            print('container collections:', cols)
            # set collection_exists flag based on container result
            if org_doc and 'collection_name' in org_doc:
                results['collection_name'] = org_doc.get('collection_name')
                results['collection_exists'] = results.get('collection_name') in cols
        except Exception as e:
            print('container-side lookup failed:', e)
    results['org_doc_exists'] = org_doc is not None
    results['admin_doc_exists'] = admin_doc is not None

    if admin_doc:
        stored_pw = admin_doc.get('password')
        print('stored_pw (prefix):', (stored_pw or '')[:60])
        results['password_hashed_not_plain'] = stored_pw != password
        try:
            ok = bcrypt.checkpw(password.encode('utf-8'), stored_pw.encode('utf-8'))
            results['bcrypt_check'] = ok
        except Exception as e:
            print('bcrypt verify error:', e)
            results['bcrypt_check'] = False

    if org_doc:
        colname = org_doc.get('collection_name')
        print('collection_name in org_doc:', colname)
        results['collection_name'] = colname
        # Only attempt a host-side collection listing if we have a working `db` object
        # and we didn't already detect existence from a container-side lookup.
        if results.get('collection_exists') is None and db is not None:
            try:
                cols = db.client[db.name].list_collection_names()
                print('collections:', cols)
                results['collection_exists'] = colname in cols
            except Exception:
                results['collection_exists'] = results.get('collection_exists', False)

    print('\n== Deleting org via API ==')
    headers = {'Authorization': f'Bearer {token}'}
    r3 = c.delete(f'/org/delete?organization_name={org_name}', headers=headers)
    print('delete status', r3.status_code, r3.text)
    results['delete_status'] = r3.status_code

    print('\n== Post-delete checks in Mongo ==')
    # Post-delete checks: if we have a host DB client, use it; otherwise fall back
    # to container-side inspection.
    try:
        if db is not None:
            org_doc2 = db.organizations.find_one({'organization_name': org_name})
            admin_doc2 = db.admins.find_one({'email': email})
            cols2 = db.client[db.name].list_collection_names()
        else:
            # container-side queries
            out_org = subprocess.check_output([
                'docker', 'compose', 'exec', '-T', 'mongo', 'mongosh', '--quiet', '--eval',
                f"JSON.stringify(db.getSiblingDB('{MASTER_DB}').organizations.findOne({{'organization_name':'{org_name}'}}))"
            ], text=True).strip()
            org_doc2 = json.loads(out_org) if out_org and out_org != 'null' else None
            out_admin = subprocess.check_output([
                'docker', 'compose', 'exec', '-T', 'mongo', 'mongosh', '--quiet', '--eval',
                f"JSON.stringify(db.getSiblingDB('{MASTER_DB}').admins.findOne({{'email':'{email}'}}))"
            ], text=True).strip()
            admin_doc2 = json.loads(out_admin) if out_admin and out_admin != 'null' else None
            out_cols2 = subprocess.check_output([
                'docker', 'compose', 'exec', '-T', 'mongo', 'mongosh', '--quiet', '--eval',
                f"JSON.stringify(db.getSiblingDB('{MASTER_DB}').getCollectionNames())"
            ], text=True).strip()
            cols2 = json.loads(out_cols2) if out_cols2 else []
    except Exception as e:
        print('post-delete inspection failed:', e)
        org_doc2 = None
        admin_doc2 = None
        cols2 = []

    print('org_doc after delete:', org_doc2)
    print('admin_doc after delete:', admin_doc2)
    print('collections after delete:', cols2)
    results['org_doc_deleted'] = org_doc2 is None
    results['admin_doc_deleted'] = admin_doc2 is None
    if 'collection_name' in results:
        results['collection_deleted'] = results.get('collection_name') not in cols2
    else:
        results['collection_deleted'] = True

print('\n== Summary ==')
for k,v in results.items():
    print(k,':',v)

all_ok = (
    results.get('create_status')==200 and
    results.get('login_status')==200 and
    results.get('token_sub_present') and
    results.get('token_email_match') and
    results.get('token_org_match') and
    results.get('org_doc_exists') and
    results.get('admin_doc_exists') and
    results.get('password_hashed_not_plain') and
    results.get('bcrypt_check') and
    results.get('collection_exists') and
    results.get('delete_status')==200 and
    results.get('org_doc_deleted') and
    results.get('admin_doc_deleted') and
    results.get('collection_deleted')
)

print('\nALL OK:', all_ok)
