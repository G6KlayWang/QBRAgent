from __future__ import annotations

import os
import time
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from requests import Response
from dotenv import load_dotenv

# Load .env from the project root (one directory up from tests/, if running there)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))



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
    _jwt: str | None = field(default=None, init=False, repr=False)
    _token_acquired_at: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.session.headers.update({"Accept": "application/json"})
        cached = os.getenv("SYM_API_JWT")
        if cached:
            self._jwt = cached.strip() or None
            self._token_acquired_at = time.monotonic()

    # ---  API -----------------------------------------------------------------

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
        headers = {"Authorization": f"Bearer {token}"}
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

    def _ensure_token(self, force: bool = False) -> str:
        if not force and self._jwt and not self._token_expired():
            return self._jwt
        self._jwt = self._login()
        self._token_acquired_at = time.monotonic()
        if not self._jwt:
            raise SymmonsAPIError("Failed to acquire authentication token")
        os.environ["SYM_API_JWT"] = self._jwt
        return self._jwt

    def _token_expired(self) -> bool:
        if not self._jwt:
            return True
        return (time.monotonic() - self._token_acquired_at) > self.token_ttl_seconds

    # log in
    def _login(self) -> str:
        payload = {"user": self.username, "password": self.password}
        resp = self.session.post(
            f"{self.base_url}/api/v2/login",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            raise SymmonsAPIError(
                f"Login failed with {resp.status_code}: {resp.text}"
            )
        data = self._parse_json(resp)
        token = self._extract_token(data)
        if not token:
            raise SymmonsAPIError(
                f"Login succeeded but token not found in response. Response: {data}"
            )
        return token

    # -------------------------------------------------------------------------------

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
        for key in ("jws", "token", "accessToken", "jwt", "idToken", "bearer", "key_0"):
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


import pandas as pd

def export_symmons_workbook(filename: str = "symmons_workbook.xlsx") -> None:
    """Fetch groups, assignments, and property details, export to Excel."""
    client = from_env()
    print("🔐 Authenticating...")
    groups_data = client.list_property_groups()
    groups = groups_data.get("modelPage", {}).get("data", [])
    print(f"✅ Found {len(groups)} property groups")

    # --- Sheet 1: Property Groups --------------------------------------------------
    df_groups = pd.DataFrame(groups)

    # --- Sheet 2: Assignments ------------------------------------------------------
    all_assignments: list[dict[str, Any]] = []

    for g in groups:
        group_id = g["id"]
        group_name = g["name"]
        print(f"📦 Fetching assignments for group '{group_name}' (ID {group_id})...")
        details = client.get_property_group(group_id)
        assignments = details.get("model", {}).get("assignments", [])
        for a in assignments:
            all_assignments.append({
                "group_id": group_id,
                "group_name": group_name,
                "hotel_id": a.get("hotelId"),
                "property_name": a.get("propertyName"),
                "is_assigned": a.get("isAssigned"),
                "group_type": details.get("model", {}).get("groupTypeLabel"),
            })
    df_assignments = pd.DataFrame(all_assignments)

    # --- Optionally Sheet 3: Property Details --------------------------------------
    # We'll only fetch details for assigned ones to keep it efficient
    property_rows: list[dict[str, Any]] = []
    assigned_ids = [a["hotel_id"] for a in all_assignments if a["is_assigned"]]
    print(f"🏨 Fetching details for {len(assigned_ids)} assigned properties...")
    for pid in assigned_ids:
        try:
            pdata = client.get_property(pid)
            if isinstance(pdata, dict):
                pdata["property_id"] = pid
                property_rows.append(pdata)
        except SymmonsAPIError as e:
            print(f"⚠️ Failed to fetch property {pid}: {e}")
    df_properties = pd.DataFrame(property_rows)

    # --- Write to Excel workbook ---------------------------------------------------
    print(f"💾 Writing workbook to {filename}...")
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df_groups.to_excel(writer, index=False, sheet_name="Groups")
        df_assignments.to_excel(writer, index=False, sheet_name="Assignments")
        if not df_properties.empty:
            df_properties.to_excel(writer, index=False, sheet_name="Properties")

    print(f" Workbook saved: {filename}")


# if __name__ == "__main__":
#     try:
#         export_symmons_workbook("symmons_property_hierarchy.xlsx")
#     except Exception as ex:
#         print(f"⚠️ Unexpected error: {ex}")



import pandas as pd
import json

if __name__ == "__main__":
    try:
        client = from_env()
        group = client.get_property_group(4)  # Marriott (Brand)
        assigned = [a for a in group["model"]["assignments"] if a["isAssigned"]]

        for a in assigned:
            prop_id = a["hotelId"]
            prop_name = a["propertyName"]
            roi = client.list_water_roi(prop_id)

            if roi:  # only save if ROI exists
                key_metrics = []
                for record in roi:
                    key_metrics.append({
                        "Property": prop_name,
                        "Property_ID": prop_id,
                        "ROI_Record_ID": record["id"],
                        "Annualized_Volume": record.get("annualizedVolume"),
                        "Annualized_Cost": record.get("annualizedCost"),
                        "Annualized_Volume_Saved": record.get("annualVolumeSaved"),
                        "Annualized_Cost_Savings": record.get("annualizedCostSavings"),
                        "Range_Volume_Saved": record.get("rangeVolumeSaved"),
                        "Range_Pct_Saved": record.get("rangeVolumePctSaved"),
                        "Expected_Flow_Rate": record.get("expectedRangeFlowRate"),
                        "Is_Solved": record.get("isSolved"),
                        "Created_At": record.get("createdAt"),
                    })
                
                # Save to CSV
                df = pd.DataFrame(key_metrics)
                filename = f"roi_metrics_property_{prop_id}.csv"
                df.to_csv(filename, index=False)
                print(f"✅ Saved ROI metrics for {prop_name} → {filename}")
            else:
                print(f"📝 No ROI data for {prop_name} (ID {prop_id})")

    except SymmonsAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as ex:
        print(f"⚠️ Unexpected error: {ex}")
# property group 4 Marriott (Brand): ROI data for property AA – Symmons Test Property (ID 3) → 2 record(s)
# Property 'Hotel Quincy' (ID 9) has no ROI data recorded.


# property group 5 JG Test (Franchise Company)
# Property 'Alpha Flow – Godfrey' (ID 25) has no ROI data yet.


# property group 3 Test (Portfolio)
# - AA - Symmons Test Property (ID 3):  2 ROI record(s)
# - Alpha Flow - Wyndham (ID 24):  No ROI data yet
# - Hampton Inn & Suites Middletown (ID 8):  No ROI data yet
# - Hotel Quincy (ID 9):  No ROI data yet

# ID 1: Test Porfolio (Portfolio) 
# Assigned property IDs for Test Portfolio: [3, 27, 2]

#  ROI Summary for Test Portfolio:
# - AA – Symmons Test Property (ID 3):  2 ROI record(s)
# - Alpha Flow – Residence Inn Braintree (ID 27): No ROI data yet 
# - Hotel Symmons (ID 2):  No ROI data yet 


# ID 6: 0 property





##   - ID 4: Marriott (Brand) → 3 properties
##   - ID 5: JG Test (Franchise Company) → 1 properties
##   - ID 3: Test (Portfolio) → 4 properties
##   - ID 1: Test Porfolio (Portfolio) → 3 properties
##   - ID 6: Test Portfolio 2 (Portfolio) → 0 properties
## if __name__ == "__main__":
##    client = from_env()
##    groups = client.list_property_groups().get("modelPage", {}).get("data", [])

#     print("Property Groups:")
#     for g in groups:
#         group_id = g["id"]
#         group_name = g["name"]
#         group_type = g.get("groupTypeLabel", "Unknown")
#         property_count = g.get("propertyCount", 0)
#         print(f"  - ID {group_id}: {group_name} ({group_type}) → {property_count} properties")