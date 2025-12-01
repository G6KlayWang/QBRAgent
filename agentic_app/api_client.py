from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from requests import Response


class SymmonsAPIError(RuntimeError):
    """Raised when the Symmons WTW API returns an error response."""


@dataclass
class SymmonsAPIClient:
    """Lightweight client with automatic login + retry on 401."""

    base_url: str
    username: str
    password: str
    token_ttl_seconds: int = 3300  # refresh a little before 1h expiry
    session: requests.Session = field(default_factory=requests.Session)
    _jwt: Optional[str] = field(default=None, init=False, repr=False)
    _token_acquired_at: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.session.headers.update({"Accept": "application/json"})
        cached = os.getenv("SYM_API_JWT")
        if cached:
            self._jwt = cached.strip() or None
            self._token_acquired_at = time.monotonic()

    # --- Public API -----------------------------------------------------------------

    def list_property_groups(self, **filters: Any) -> Dict[str, Any]:
        """Return paginated property group list."""
        return self._get("/api/v2/property-groups", params=filters)

    def get_property_group(self, group_id: int | str) -> Dict[str, Any]:
        return self._get(f"/api/v2/property-group/{group_id}")

    def get_property(self, property_id: int | str) -> Dict[str, Any]:
        return self._get(f"/api/v2/property/{property_id}")

    def list_water_roi(self, property_id: int | str) -> Dict[str, Any]:
        return self._get(f"/api/v2/water-roi/list/{property_id}")

    def property_counts(self, property_id: int | str) -> Dict[str, Any]:
        return self._get(f"/api/v2/property/{property_id}/counts")

    def report_property_summary(
        self, property_id: int | str, *, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        payload: Dict[str, Any]
        if isinstance(property_id, int) or str(property_id).isdigit():
            payload = {
                "propertyId": int(property_id),
                "startDate": start_date,
                "endDate": end_date,
            }
        else:
            payload = {
                "propertyId": property_id,
                "startDate": start_date,
                "endDate": end_date,
            }
        return self._post("/api/v2/report/property-summary", json_payload=payload)

    def call_endpoint(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized = path if path.startswith("/") else f"/{path}"
        resp = self._request(
            method.upper(),
            normalized,
            params=params,
            json_payload=json_payload,
        )
        return self._parse_json(resp)

    # --- Internal helpers -----------------------------------------------------------

    def _get(
        self, path: str, *, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        resp = self._request("GET", path, params=params)
        return self._parse_json(resp)

    def _post(
        self, path: str, *, json_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        resp = self._request("POST", path, json_payload=json_payload)
        return self._parse_json(resp)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
        retry: bool = True,
    ) -> Response:
        token = self._ensure_token()
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = self.session.request(
            method,
            url,
            params=params,
            json=json_payload,
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 401 and retry:
            self._jwt = None
            self._token_acquired_at = 0
            token = self._ensure_token(force=True)
            headers["Authorization"] = f"Bearer {token}"
            resp = self.session.request(
                method,
                url,
                params=params,
                json=json_payload,
                headers=headers,
                timeout=30,
            )
        if resp.status_code >= 400:
            raise SymmonsAPIError(
                f"{method} {path} failed with {resp.status_code}: {resp.text}"
            )
        return resp

    def _ensure_token(self, force: bool = False) -> Optional[str]:
        if not force and self._jwt and not self._token_expired():
            return self._jwt
        self._jwt = self._login()
        self._token_acquired_at = time.monotonic()
        if self._jwt:
            os.environ["SYM_API_JWT"] = self._jwt
        return self._jwt

    def _token_expired(self) -> bool:
        if not self._jwt:
            return True
        return (time.monotonic() - self._token_acquired_at) > self.token_ttl_seconds

    def _login(self) -> Optional[str]:
        payload = {"user": self.username, "password": self.password}
        resp = self.session.post(
            f"{self.base_url}/api/v2/login",
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise SymmonsAPIError(
                f"Login failed with {resp.status_code}: {resp.text}"
            )
        data = self._parse_json(resp)
        token = self._extract_token(data)
        return token

    @staticmethod
    def _parse_json(resp: Response) -> Dict[str, Any]:
        try:
            return resp.json()
        except ValueError as exc:
            raise SymmonsAPIError(
                f"Invalid JSON response from {resp.request.method} {resp.request.url}"
            ) from exc

    @staticmethod
    def _extract_token(payload: Dict[str, Any]) -> Optional[str]:
        for key in ("token", "accessToken", "jwt", "idToken", "bearer", "key_0"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        # Some APIs wrap the token in nested fields
        if "model" in payload and isinstance(payload["model"], dict):
            return SymmonsAPIClient._extract_token(payload["model"])
        return None


def from_env() -> SymmonsAPIClient:
    """Factory loading configuration from environment variables."""
    base_url = os.getenv("SYM_BASE_URL")
    username = os.getenv("SYM_API_EMAIL")
    password = os.getenv("SYM_API_PASSWORD")
    if not base_url or not username or not password:
        raise ValueError(
            "SYM_BASE_URL, SYM_API_EMAIL, and SYM_API_PASSWORD must be set."
        )
    return SymmonsAPIClient(base_url=base_url, username=username, password=password)
