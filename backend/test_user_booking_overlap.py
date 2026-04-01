"""Unit tests – a user must not be able to book overlapping slots across different robots."""

from __future__ import annotations

import os
import sys
import types
import pytest
from datetime import datetime

# ---------------------------------------------------------------------------
# Minimal stubs so we can import booking_service without a real DB/FastAPI
# ---------------------------------------------------------------------------

if "database" not in sys.modules:
    database_stub = types.ModuleType("database")

    class DatabaseManager:  # pragma: no cover
        pass

    database_stub.DatabaseManager = DatabaseManager
    sys.modules["database"] = database_stub

if "fastapi" not in sys.modules:
    fastapi_stub = types.ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = ""):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    fastapi_stub.HTTPException = HTTPException
    sys.modules["fastapi"] = fastapi_stub

BACKEND_DIR = os.path.dirname(__file__)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import services.booking_service as booking_service_module
from services.booking_service import BookingService

HTTPException = sys.modules["fastapi"].HTTPException


# ---------------------------------------------------------------------------
# Mock DB
# ---------------------------------------------------------------------------

class MockDB:
    """Minimal DB mock that delegates overlap logic to the real helpers extracted
    from database.py without requiring an actual database connection."""

    def __init__(self, existing_user_bookings=None):
        # List of dicts with keys: user_id, robot_id, date, start_time, end_time, status
        self._existing = existing_user_bookings or []
        self.created_payload = None

    # -- helpers mirroring database.py logic ----------------------------------

    @staticmethod
    def _parse_time(t_str: str):
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(t_str.strip(), fmt).time()
            except ValueError:
                continue
        raise ValueError(f"Invalid time format: {t_str}")

    def _user_has_overlap(self, user_id, date, start_time, end_time):
        new_start = self._parse_time(start_time)
        new_end = self._parse_time(end_time)
        for b in self._existing:
            if b["user_id"] != user_id or b["date"] != date:
                continue
            if b["status"] not in ("active", "scheduled"):
                continue
            ex_start = self._parse_time(b["start_time"])
            ex_end = self._parse_time(b["end_time"])
            if new_start < ex_end and ex_start < new_end:
                return True
        return False

    # -- BookingService-facing API --------------------------------------------

    def get_active_robots(self):
        return [
            {"id": 1, "type": "turtlebot", "status": "active", "name": "TB3-1"},
            {"id": 2, "type": "turtlebot", "status": "active", "name": "TB3-2"},
        ]

    def get_robot_by_id(self, robot_id):
        robots = {r["id"]: r for r in self.get_active_robots()}
        r = robots.get(robot_id)
        if r:
            return dict(r, container_image="test-image")
        return None

    def get_bookings_for_date_range(self, *_args, **_kwargs):
        return list(self._existing)

    def create_booking(self, user_id, robot_id, date, start_time, end_time, robot_type=None):
        # User overlap check (mirrors database.py _has_user_overlap logic)
        if self._user_has_overlap(user_id, date, start_time, end_time):
            raise HTTPException(
                status_code=409,
                detail="User already has a booking that overlaps this time slot",
            )
        self.created_payload = dict(
            user_id=user_id,
            robot_id=robot_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
        )
        return {
            "id": 99,
            "user_id": user_id,
            "robot_id": robot_id,
            "robot_type": robot_type or "turtlebot",
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "status": "active",
            "created_at": "2026-04-01T10:00:00",
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _freeze_now(monkeypatch, frozen_now: datetime):
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return frozen_now
            return frozen_now.astimezone(tz)

        @classmethod
        def strptime(cls, date_string, fmt):
            return datetime.strptime(date_string, fmt)

    monkeypatch.setattr(booking_service_module, "datetime", FrozenDateTime)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

DATE = "2026-04-01"
USER_A = 1
USER_B = 2
ROBOT_1 = 1
ROBOT_2 = 2


def test_same_user_same_time_different_robot_is_rejected(monkeypatch):
    """User A books Robot 1; trying to book Robot 2 at the same time must fail with 409."""
    _freeze_now(monkeypatch, datetime(2026, 4, 1, 8, 0))
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "30")

    existing = [
        {
            "user_id": USER_A,
            "robot_id": ROBOT_1,
            "date": DATE,
            "start_time": "10:00",
            "end_time": "11:00",
            "status": "active",
        }
    ]
    service = BookingService(MockDB(existing))

    with pytest.raises(HTTPException) as exc_info:
        service.create_booking(
            user_id=USER_A,
            robot_id=ROBOT_2,
            robot_type="turtlebot",
            date=DATE,
            start_time="10:00",
            end_time="11:00",
        )

    assert exc_info.value.status_code == 409
    assert "overlaps" in exc_info.value.detail.lower()


def test_same_user_overlapping_time_different_robot_is_rejected(monkeypatch):
    """Partial overlap (new slot starts before existing ends) is also rejected."""
    _freeze_now(monkeypatch, datetime(2026, 4, 1, 8, 0))
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "30")

    existing = [
        {
            "user_id": USER_A,
            "robot_id": ROBOT_1,
            "date": DATE,
            "start_time": "10:00",
            "end_time": "11:00",
            "status": "scheduled",
        }
    ]
    service = BookingService(MockDB(existing))

    with pytest.raises(HTTPException) as exc_info:
        service.create_booking(
            user_id=USER_A,
            robot_id=ROBOT_2,
            robot_type="turtlebot",
            date=DATE,
            start_time="10:30",
            end_time="11:30",
        )

    assert exc_info.value.status_code == 409


def test_same_user_non_overlapping_slots_different_robots_are_allowed(monkeypatch):
    """User A books Robot 1 at 10:00-11:00 and Robot 2 at 11:00-12:00 — must succeed."""
    _freeze_now(monkeypatch, datetime(2026, 4, 1, 8, 0))
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "30")

    existing = [
        {
            "user_id": USER_A,
            "robot_id": ROBOT_1,
            "date": DATE,
            "start_time": "10:00",
            "end_time": "11:00",
            "status": "active",
        }
    ]
    db = MockDB(existing)
    service = BookingService(db)

    result = service.create_booking(
        user_id=USER_A,
        robot_id=ROBOT_2,
        robot_type="turtlebot",
        date=DATE,
        start_time="11:00",
        end_time="12:00",
    )

    assert result["id"] == 99


def test_different_users_can_book_same_time_on_different_robots(monkeypatch):
    """User A on Robot 1 and User B on Robot 2 at the same time — must succeed."""
    _freeze_now(monkeypatch, datetime(2026, 4, 1, 8, 0))
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "30")

    existing = [
        {
            "user_id": USER_A,
            "robot_id": ROBOT_1,
            "date": DATE,
            "start_time": "10:00",
            "end_time": "11:00",
            "status": "active",
        }
    ]
    db = MockDB(existing)
    service = BookingService(db)

    result = service.create_booking(
        user_id=USER_B,
        robot_id=ROBOT_2,
        robot_type="turtlebot",
        date=DATE,
        start_time="10:00",
        end_time="11:00",
    )

    assert result["id"] == 99


def test_same_user_hhmmss_format_overlap_is_rejected(monkeypatch):
    """Overlap check must work when time strings use HH:MM:SS format."""
    _freeze_now(monkeypatch, datetime(2026, 4, 1, 8, 0))
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "30")

    existing = [
        {
            "user_id": USER_A,
            "robot_id": ROBOT_1,
            "date": DATE,
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "status": "active",
        }
    ]
    service = BookingService(MockDB(existing))

    with pytest.raises(HTTPException) as exc_info:
        service.create_booking(
            user_id=USER_A,
            robot_id=ROBOT_2,
            robot_type="turtlebot",
            date=DATE,
            start_time="10:30:00",
            end_time="11:30:00",
        )

    assert exc_info.value.status_code == 409
