from __future__ import annotations

import json
import os
import threading
import time
from datetime import date

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

from campsite_watch_checker import WatchChecker
from campsite_watch_clients import BCParksAvailabilityClient, ConsoleNotificationClient
from campsite_watch_storage import Storage

INDEX_TEMPLATE = """
<!doctype html>
<html>
  <head><title>BC Campsite Watcher</title></head>
  <body>
    <h1>BC Campsite Watcher</h1>
    <form method="post" action="{{ url_for('create_watch_page') }}">
      <input name="email" placeholder="Email" required>
      <input name="phone" placeholder="Phone (optional)">
      <input name="park_code" placeholder="Park code" required>
      <input name="site_code" placeholder="Site code" required>
      <input name="start_date" type="date" required>
      <input name="end_date" type="date" required>
      <input name="party_size" type="number" min="1" value="2" required>
      <input name="check_frequency_minutes" type="number" min="5" value="10" required>
      <button type="submit">Create watch</button>
    </form>

    <h2>Watches</h2>
    {% for watch in watches %}
      <div style="margin-bottom: 16px; padding: 8px; border: 1px solid #ccc;">
        <strong>#{{ watch.id }}</strong> {{ watch.park_code }}/{{ watch.site_code }}
        ({{ watch.start_date }} to {{ watch.end_date }})
        Active: {{ watch.active }}
        <form method="post" action="{{ url_for('toggle_watch_page', watch_id=watch.id) }}">
          <input type="hidden" name="active" value="{{ 'false' if watch.active else 'true' }}">
          <button type="submit">{{ 'Pause' if watch.active else 'Resume' }}</button>
        </form>
        <a href="{{ url_for('get_checks_page', watch_id=watch.id) }}">Checks</a>
        <a href="{{ url_for('get_alerts_page', watch_id=watch.id) }}">Alerts</a>
      </div>
    {% else %}
      <p>No watches yet.</p>
    {% endfor %}
  </body>
</html>
"""


class CheckerScheduler:
    def __init__(self, checker: WatchChecker, interval_seconds: int = 300):
        self.checker = checker
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self.checker.run_all()
            self._stop_event.wait(timeout=self.interval_seconds)


def create_app() -> Flask:
    db_path = os.environ.get("CAMPSITE_DB_PATH", "./data/campsite_watch.db")
    checker_interval_seconds = int(os.environ.get("CHECK_INTERVAL_SECONDS", "300"))
    availability_endpoint = os.environ.get("BC_AVAILABILITY_ENDPOINT")

    storage = Storage(db_path)
    checker = WatchChecker(
        storage=storage,
        availability_client=BCParksAvailabilityClient(availability_endpoint),
        notification_client=ConsoleNotificationClient(),
    )

    app = Flask(__name__)
    scheduler = CheckerScheduler(checker=checker, interval_seconds=checker_interval_seconds)
    scheduler.start()

    @app.get("/")
    def index():
        user_id = request.args.get("user_id", type=int)
        watches = storage.list_watches(user_id=user_id) if user_id else []
        return render_template_string(INDEX_TEMPLATE, watches=watches)

    @app.post("/")
    def create_watch_page():
        payload = request.form
        user_id = storage.ensure_user(payload["email"], payload.get("phone"))
        watch_id = storage.create_watch(
            user_id=user_id,
            park_code=payload["park_code"],
            site_code=payload["site_code"],
            start_date=date.fromisoformat(payload["start_date"]),
            end_date=date.fromisoformat(payload["end_date"]),
            party_size=int(payload["party_size"]),
            check_frequency_minutes=int(payload["check_frequency_minutes"]),
            active=True,
        )
        return redirect(url_for("index", user_id=user_id, watch_id=watch_id))

    @app.post("/watches/<int:watch_id>/active")
    def toggle_watch_page(watch_id: int):
        active = request.form.get("active", "false") == "true"
        storage.set_watch_active(watch_id, active)
        return redirect(request.referrer or url_for("index"))

    @app.get("/watches/<int:watch_id>/checks")
    def get_checks_page(watch_id: int):
        return jsonify(storage.list_checks(watch_id))

    @app.get("/watches/<int:watch_id>/alerts")
    def get_alerts_page(watch_id: int):
        return jsonify(storage.list_alerts(watch_id))

    @app.post("/api/watches")
    def create_watch_api():
        payload = request.get_json(force=True)
        user_id = storage.ensure_user(payload["email"], payload.get("phone"))
        watch_id = storage.create_watch(
            user_id=user_id,
            park_code=payload["park_code"],
            site_code=payload["site_code"],
            start_date=date.fromisoformat(payload["start_date"]),
            end_date=date.fromisoformat(payload["end_date"]),
            party_size=int(payload["party_size"]),
            check_frequency_minutes=int(payload.get("check_frequency_minutes", 10)),
            active=bool(payload.get("active", True)),
        )
        return jsonify({"id": watch_id, "user_id": user_id}), 201

    @app.get("/api/watches")
    def list_watches_api():
        user_id = request.args.get("user_id", type=int)
        if user_id is None:
            return jsonify({"error": "user_id is required"}), 400
        watches = storage.list_watches(user_id=user_id)
        return jsonify(
            [
                {
                    "id": w.id,
                    "user_id": w.user_id,
                    "park_code": w.park_code,
                    "site_code": w.site_code,
                    "start_date": w.start_date.isoformat(),
                    "end_date": w.end_date.isoformat(),
                    "party_size": w.party_size,
                    "check_frequency_minutes": w.check_frequency_minutes,
                    "active": w.active,
                    "created_at": w.created_at.isoformat(),
                }
                for w in watches
            ]
        )

    @app.patch("/api/watches/<int:watch_id>")
    def patch_watch_api(watch_id: int):
        payload = request.get_json(force=True)
        if "active" not in payload:
            return jsonify({"error": "active is required"}), 400
        updated = storage.set_watch_active(watch_id, bool(payload["active"]))
        if not updated:
            return jsonify({"error": "watch not found"}), 404
        return jsonify({"id": watch_id, "active": bool(payload["active"])})

    @app.get("/api/watches/<int:watch_id>/checks")
    def watch_checks_api(watch_id: int):
        return jsonify(storage.list_checks(watch_id))

    @app.get("/api/watches/<int:watch_id>/alerts")
    def watch_alerts_api(watch_id: int):
        return jsonify(storage.list_alerts(watch_id))

    @app.post("/api/run-checks")
    def run_checks_api():
        checker.run_all()
        return jsonify({"status": "ok"})

    @app.get("/api/health")
    def health_api():
        return jsonify({"status": "ok", "scheduler_interval_seconds": checker_interval_seconds})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
