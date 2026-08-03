import tempfile
import unittest
from datetime import date

from campsite_watch_checker import WatchChecker
from campsite_watch_models import AvailabilityResult
from campsite_watch_storage import Storage


class FakeAvailabilityClient:
    def __init__(self, results):
        self.results = list(results)

    def fetch(self, watch):
        return self.results.pop(0)


class FakeNotificationClient:
    def __init__(self):
        self.messages = []

    def send(self, watch, message):
        self.messages.append((watch.id, message))


class CampsiteWatchTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = f"{self.tmpdir.name}/watch.db"
        self.storage = Storage(self.db_path)
        self.user_id = self.storage.ensure_user("u@example.com")
        self.watch_id = self.storage.create_watch(
            user_id=self.user_id,
            park_code="garibaldi",
            site_code="helmet",
            start_date=date.fromisoformat("2026-08-10"),
            end_date=date.fromisoformat("2026-08-12"),
            party_size=2,
            check_frequency_minutes=10,
            active=True,
        )
        self.watch = self.storage.get_watch(self.watch_id)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_alert_sent_on_new_availability(self):
        availability = FakeAvailabilityClient(
            [
                AvailabilityResult(False, [], {"is_available": False}),
                AvailabilityResult(True, ["2026-08-11"], {"is_available": True, "available_dates": ["2026-08-11"]}),
            ]
        )
        notifications = FakeNotificationClient()
        checker = WatchChecker(
            storage=self.storage,
            availability_client=availability,
            notification_client=notifications,
        )

        checker.run_watch(self.watch)
        checker.run_watch(self.watch)

        alerts = self.storage.list_alerts(self.watch_id)
        checks = self.storage.list_checks(self.watch_id)

        self.assertEqual(len(checks), 2)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(len(notifications.messages), 1)

    def test_duplicate_availability_hash_does_not_send_again(self):
        first = AvailabilityResult(True, ["2026-08-10"], {"available_dates": ["2026-08-10"], "is_available": True})
        second = AvailabilityResult(False, [], {"is_available": False})
        third = AvailabilityResult(True, ["2026-08-10"], {"available_dates": ["2026-08-10"], "is_available": True})
        availability = FakeAvailabilityClient([first, second, third])
        notifications = FakeNotificationClient()
        checker = WatchChecker(
            storage=self.storage,
            availability_client=availability,
            notification_client=notifications,
        )

        checker.run_watch(self.watch)
        checker.run_watch(self.watch)
        checker.run_watch(self.watch)

        self.assertEqual(len(self.storage.list_alerts(self.watch_id)), 1)
        self.assertEqual(len(notifications.messages), 1)


if __name__ == "__main__":
    unittest.main()
