from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from campsite_watch_checker import AvailabilityClient, NotificationClient
from campsite_watch_models import AvailabilityResult, Watch


class BCParksAvailabilityClient(AvailabilityClient):
    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint

    def fetch(self, watch: Watch) -> AvailabilityResult:
        if not self.endpoint:
            return AvailabilityResult(is_available=False, available_dates=[], raw_payload={"source": "stub"})

        params = {
            "park": watch.park_code,
            "site": watch.site_code,
            "start": watch.start_date.isoformat(),
            "end": watch.end_date.isoformat(),
            "partySize": str(watch.party_size),
        }
        url = f"{self.endpoint}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AvailabilityMonitor/1.0",
                "Accept": "application/json,text/html",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            return AvailabilityResult(
                is_available=False,
                available_dates=[],
                raw_payload={"error": str(exc), "url": url},
            )

        payload = self._parse_payload(content)
        available_dates = payload.get("available_dates", [])
        is_available = bool(payload.get("is_available", bool(available_dates)))
        return AvailabilityResult(
            is_available=is_available,
            available_dates=[str(d) for d in available_dates],
            raw_payload=payload,
        )

    @staticmethod
    def _parse_payload(content: str) -> dict:
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {"raw": parsed}
        except json.JSONDecodeError:
            return {"raw_html": content[:2000]}


class ConsoleNotificationClient(NotificationClient):
    def send(self, watch: Watch, message: str) -> None:
        print(f"[notify] watch={watch.id} user={watch.user_id} {message}")
