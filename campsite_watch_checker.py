from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from campsite_watch_models import AvailabilityResult, Watch
from campsite_watch_storage import Storage


class AvailabilityClient:
    def fetch(self, watch: Watch) -> AvailabilityResult:
        raise NotImplementedError


class NotificationClient:
    def send(self, watch: Watch, message: str) -> None:
        raise NotImplementedError


class WatchChecker:
    def __init__(
        self,
        *,
        storage: Storage,
        availability_client: AvailabilityClient,
        notification_client: NotificationClient,
    ):
        self.storage = storage
        self.availability_client = availability_client
        self.notification_client = notification_client

    def run_all(self) -> None:
        for watch in self.storage.list_active_watches():
            self.run_watch(watch)

    def run_watch(self, watch: Watch) -> None:
        result = self.availability_client.fetch(watch)
        now = datetime.now(UTC)

        self.storage.create_check(
            watch_id=watch.id,
            checked_at=now,
            raw_response=result.raw_payload,
            is_available=result.is_available,
            available_dates=result.available_dates,
        )

        previous = self.storage.get_previous_state(watch.id)
        changed_to_available = previous is False and result.is_available
        first_available = previous is None and result.is_available
        if not (changed_to_available or first_available):
            return

        availability_hash = self.hash_availability(result)
        if self.storage.has_alert_hash(watch.id, availability_hash):
            return

        message = (
            f"Site {watch.site_code} is available from "
            f"{watch.start_date.isoformat()} to {watch.end_date.isoformat()}"
        )
        self.notification_client.send(watch, message)
        self.storage.create_alert(
            watch_id=watch.id,
            sent_at=now,
            channel="email",
            message=message,
            availability_hash=availability_hash,
        )

    @staticmethod
    def hash_availability(result: AvailabilityResult) -> str:
        payload = {
            "is_available": result.is_available,
            "available_dates": sorted(result.available_dates),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
