#!/usr/bin/env python3
"""Provision the tempest-sbx realm into a RUNNING Keycloak, via the admin API.

Realms only import on a *fresh* KC DB; the shared auth.wolfhold.app is already
running with data — so we create/reconcile the realm live instead. Idempotent:
safe to re-run (creates the realm if missing, always re-sets the client secret).
Stdlib only — runs on the box (or anywhere that can reach the admin API + has the
master admin password).

Env:
  KC_ADMIN_URL       default https://auth.wolfhold.app
  KC_ADMIN_USER      Keycloak bootstrap admin (master realm)   [required]
  KC_ADMIN_PASSWORD  ^                                          [required]
  KC_CLIENT_SECRET   tempest-web client secret to set (must equal the app's)  [required]
  REALM_FILE         default ../keycloak/realms/tempest-sbx-realm.json
  KC_SSL_REQUIRED    default 'external' (use 'none' only for plain-HTTP testing)

Usage:  python3 ops/provision-realm.py
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.getenv("KC_ADMIN_URL", "https://auth.wolfhold.app").rstrip("/")
USER = os.getenv("KC_ADMIN_USER", "admin")
PASS = os.getenv("KC_ADMIN_PASSWORD", "")
SECRET = os.getenv("KC_CLIENT_SECRET", "")
SSL = os.getenv("KC_SSL_REQUIRED", "external")
REALM_FILE = os.getenv("REALM_FILE", os.path.join(
    os.path.dirname(__file__), "..", "keycloak", "realms", "tempest-sbx-realm.json"))
CLIENT_ID = "tempest-web"


def _req(method, path, token=None, data=None, form=False):
    headers, body = {}, None
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            is_json = r.headers.get_content_type() == "application/json"
            return r.status, (json.loads(raw) if raw and is_json else (raw.decode() if raw else ""))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def admin_token():
    st, body = _req("POST", "/realms/master/protocol/openid-connect/token", data={
        "grant_type": "password", "client_id": "admin-cli", "username": USER, "password": PASS,
    }, form=True)
    if st != 200:
        sys.exit(f"✗ admin login failed ({st}): {body}")
    return body["access_token"]


def main():
    if not PASS:
        sys.exit("✗ set KC_ADMIN_PASSWORD")
    if not SECRET:
        sys.exit("✗ set KC_CLIENT_SECRET")

    with open(os.path.abspath(REALM_FILE)) as f:
        realm = json.load(f)
    realm["sslRequired"] = SSL
    for c in realm.get("clients", []):
        if c.get("clientId") == CLIENT_ID:
            c["secret"] = SECRET
    name = realm["realm"]

    tok = admin_token()
    print(f"→ admin OK at {BASE}")

    st, _ = _req("GET", f"/admin/realms/{name}", token=tok)
    if st == 404:
        st, body = _req("POST", "/admin/realms", token=tok, data=realm)
        if st not in (201, 204):
            sys.exit(f"✗ create realm failed ({st}): {body}")
        print(f"✓ created realm '{name}' (client, roles, demo users imported)")
    elif st == 200:
        print(f"• realm '{name}' already exists — reconciling")
    else:
        sys.exit(f"✗ probing realm failed ({st})")

    # Reconcile the client secret (idempotent) — always align it to KC_CLIENT_SECRET.
    st, clients = _req("GET", f"/admin/realms/{name}/clients?clientId={CLIENT_ID}", token=tok)
    if st == 200 and clients:
        client = clients[0]
        client["secret"] = SECRET
        st, body = _req("PUT", f"/admin/realms/{name}/clients/{client['id']}", token=tok, data=client)
        if st in (200, 204):
            print(f"✓ '{CLIENT_ID}' client secret aligned")
        else:
            sys.exit(f"✗ set client secret failed ({st}): {body}")
    else:
        sys.exit(f"✗ could not find '{CLIENT_ID}' client ({st})")

    print(f"done — realm '{name}' ready on {BASE}")


if __name__ == "__main__":
    main()
