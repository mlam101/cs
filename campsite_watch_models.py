from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Watch:
    id: int
    user_id: int
    park_code: str
    site_code: str
    start_date: date
    end_date: date
    party_size: int
    check_frequency_minutes: int
    active: bool
    created_at: datetime


@dataclass(frozen=True)
class AvailabilityResult:
    is_available: bool
    available_dates: list[str]
    raw_payload: dict
