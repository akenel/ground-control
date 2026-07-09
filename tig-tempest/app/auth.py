"""TIG · Tempest — OIDC against Keycloak (GO-LIVE Phase 3).

Copied from freehold's auth.py — the whole login dance in one readable file.
Tempest's app is a *confidential* client: it holds a secret and keeps tokens on
the server; the browser only ever gets a signed session cookie, never a token.

Split horizon (on purpose):
  - PUBLIC  (KC_PUBLIC_URL)   — where the BROWSER is sent.
  - INTERNAL(KC_INTERNAL_URL) — where the APP talks to Keycloak, server-to-server.
The token ISSUER is always the PUBLIC url, so validation is deterministic.
"""
import base64
import hashlib
import os
import secrets
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

APP_ENV = os.getenv("APP_ENV", "dev")
# One shared Keycloak holds all three realms; each environment uses its own.
_REALM_BY_ENV = {"sandbox": "tempest-sbx", "staging": "tempest-stg", "production": "tempest-prd"}
REALM = os.getenv("KC_REALM") or _REALM_BY_ENV.get(APP_ENV, "tempest-sbx")
PUBLIC = os.getenv("KC_PUBLIC_URL", "http://localhost:8081").rstrip("/")
INTERNAL = os.getenv("KC_INTERNAL_URL", "http://tempest-kc:8080").rstrip("/")
CLIENT_ID = os.getenv("KC_CLIENT_ID", "tempest-web")
CLIENT_SECRET = os.getenv("KC_CLIENT_SECRET", "tempest-dev-secret-change-me")

ISSUER = f"{PUBLIC}/realms/{REALM}"
AUTH_URL = f"{PUBLIC}/realms/{REALM}/protocol/openid-connect/auth"                 # browser
REGISTER_URL = f"{PUBLIC}/realms/{REALM}/protocol/openid-connect/registrations"    # browser (sign-up)
LOGOUT_URL = f"{PUBLIC}/realms/{REALM}/protocol/openid-connect/logout"             # browser
TOKEN_URL = f"{INTERNAL}/realms/{REALM}/protocol/openid-connect/token"    # backend
CERTS_URL = f"{INTERNAL}/realms/{REALM}/protocol/openid-connect/certs"    # backend

# Fetches + caches Keycloak's public signing keys (JWKS). Lazy: no call until first verify.
_jwks = PyJWKClient(CERTS_URL)


def new_secret() -> str:
    return secrets.token_urlsafe(16)


def make_pkce() -> tuple[str, str]:
    """(verifier, challenge) for PKCE S256."""
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _flow_params(redirect_uri: str, state: str, nonce: str, challenge: str) -> str:
    return urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": redirect_uri,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })


def build_auth_redirect(redirect_uri, state, nonce, challenge) -> str:
    """The URL we send the browser to — Keycloak's hosted LOGIN page."""
    return f"{AUTH_URL}?{_flow_params(redirect_uri, state, nonce, challenge)}"


def build_register_redirect(redirect_uri, state, nonce, challenge) -> str:
    """Same flow, but starts on Keycloak's SIGN-UP page. New users land back at
    /auth/callback already logged in — one code path."""
    return f"{REGISTER_URL}?{_flow_params(redirect_uri, state, nonce, challenge)}"


async def exchange_code(code: str, redirect_uri: str, verifier: str) -> dict:
    """Trade the one-time code for tokens (server-to-server, with the client secret)."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": verifier,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()


def verify_id_token(id_token: str, nonce: str | None) -> dict:
    """Verify signature (via JWKS), audience, issuer — then the nonce we planted."""
    key = _jwks.get_signing_key_from_jwt(id_token).key
    claims = jwt.decode(id_token, key, algorithms=["RS256"], audience=CLIENT_ID, issuer=ISSUER)
    if nonce and claims.get("nonce") != nonce:
        raise ValueError("nonce mismatch")
    return claims


def roles_from_access(access_token: str) -> list[str]:
    """Realm roles live in the ACCESS token under realm_access.roles."""
    key = _jwks.get_signing_key_from_jwt(access_token).key
    claims = jwt.decode(
        access_token, key, algorithms=["RS256"], issuer=ISSUER,
        options={"verify_aud": False},   # access-token audience is 'account', not us
    )
    return claims.get("realm_access", {}).get("roles", [])


def logout_redirect(id_token: str, post_logout: str) -> str:
    """RP-initiated logout — end the Keycloak session too, then come back home."""
    query = urlencode({
        "id_token_hint": id_token,
        "post_logout_redirect_uri": post_logout,
        "client_id": CLIENT_ID,
    })
    return f"{LOGOUT_URL}?{query}"
