"""Pytest coverage for booking lead-time and slot-generation alignment."""

from __future__ import annotations

import inspect
import os
import sys
import types
from datetime import datetime, timedelta
import pytest

# Allow importing backend/services without requiring full runtime dependencies
if "database" not in sys.modules:
    database_stub = types.ModuleType("database")

    class DatabaseManager:  # pragma: no cover - compatibility stub
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

from services import booking_service as booking_service_module
from services.booking_service import BookingService


class MockBookingDB:
    def __init__(self, bookings=None):
        self._bookings = bookings or []
        self.created_payload = None

    def get_active_robots(self):
        return [{"id": 1, "type": "turtlebot", "status": "active", "name": "TB3"}]

    def get_robot_by_id(self, robot_id):
        return {"id": robot_id, "type": "turtlebot", "container_image": "test-image"}

    def get_bookings_for_date_range(self, *_args, **_kwargs):
        return list(self._bookings)

    def create_booking(self, **kwargs):
        self.created_payload = kwargs
        return {
            "id": 123,
            "user_id": kwargs["user_id"],
            "robot_id": kwargs["robot_id"],
            "robot_type": kwargs.get("robot_type") or "turtlebot",
            "date": kwargs["date"],
            "start_time": kwargs["start_time"],
            "end_time": kwargs["end_time"],
            "status": "active",
            "created_at": "2026-03-26T10:00:00",
        }


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


def test_validate_booking_time_allows_one_minute_future_when_lead_time_zero(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")

    service = BookingService(MockBookingDB())
    date = frozen_now.strftime("%Y-%m-%d")

    assert service.validate_booking_time(date, "10:01", "10:31") is True


def test_validate_booking_time_rejects_past_start_when_lead_time_zero(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")

    service = BookingService(MockBookingDB())
    date = frozen_now.strftime("%Y-%m-%d")

    assert service.validate_booking_time(date, "09:59", "10:29") is False


def test_validate_booking_time_rejects_start_within_15_minutes(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "15")

    service = BookingService(MockBookingDB())
    date = frozen_now.strftime("%Y-%m-%d")

    assert service.validate_booking_time(date, "10:05", "10:35") is False


def test_validate_booking_time_accepts_hh_mm_ss(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")

    service = BookingService(MockBookingDB())
    date = frozen_now.strftime("%Y-%m-%d")

    assert service.validate_booking_time(date, "10:01:00", "10:31:00") is True


def test_create_booking_requires_robot_id(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")

    service = BookingService(MockBookingDB())
    date = frozen_now.strftime("%Y-%m-%d")

    with pytest.raises(booking_service_module.HTTPException) as exc_info:
        service.create_booking(
            user_id=1,
            robot_id=None,
            robot_type="turtlebot",
            date=date,
            start_time="11:00",
            end_time="12:00",
        )

    assert exc_info.value.status_code == 400
    assert "robot_id is required" in str(exc_info.value.detail)


def test_no_hardcoded_ten_minute_lead_time_in_booking_logic():
    validate_src = inspect.getsource(BookingService.validate_booking_time)
    slot_src = inspect.getsource(BookingService.get_available_time_slots)

    assert "timedelta(minutes=10)" not in validate_src
    assert "timedelta(minutes=10)" not in slot_src


def test_available_slots_today_with_zero_lead_time_only_include_future_slots(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 30)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")

    service = BookingService(MockBookingDB())
    date = frozen_now.strftime("%Y-%m-%d")

    slots = service.get_available_time_slots(date=date, robot_id=1)
    start_times = {slot["start_time"] for slot in slots}

    assert "10:00" not in start_times
    assert "11:00" in start_times
    assert min(start_times) >= "11:00"


def test_available_slots_today_with_15_minute_lead_time_excludes_near_term_slots(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 50)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "15")

    service = BookingService(MockBookingDB())
    date = frozen_now.strftime("%Y-%m-%d")

    slots = service.get_available_time_slots(date=date, robot_id=1)
    start_times = {slot["start_time"] for slot in slots}

    assert "11:00" not in start_times  # within 15-minute lead window at 10:50
    assert "12:00" in start_times


# ---------------------------------------------------------------------------
# BOOKING_MAX_DAYS_AHEAD tests
# ---------------------------------------------------------------------------

def test_validate_booking_time_rejects_date_beyond_max_days_ahead(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "7")

    service = BookingService(MockBookingDB())
    # 8 days ahead – beyond the window
    future_date = (frozen_now + timedelta(days=8)).strftime("%Y-%m-%d")

    assert service.validate_booking_time(future_date, "10:00", "11:00") is False


def test_validate_booking_time_allows_date_at_max_days_ahead_boundary(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "7")

    service = BookingService(MockBookingDB())
    # Exactly 7 days ahead – within the window
    future_date = (frozen_now + timedelta(days=7)).strftime("%Y-%m-%d")

    assert service.validate_booking_time(future_date, "10:00", "11:00") is True


def test_available_slots_returns_empty_beyond_max_days_ahead(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "7")

    service = BookingService(MockBookingDB())
    future_date = (frozen_now + timedelta(days=8)).strftime("%Y-%m-%d")

    slots = service.get_available_time_slots(date=future_date, robot_id=1)
    assert slots == []


def test_available_slots_returns_slots_within_max_days_ahead(monkeypatch):
    frozen_now = datetime(2026, 3, 26, 10, 0)
    _freeze_now(monkeypatch, frozen_now)
    monkeypatch.setenv("MIN_BOOKING_LEAD_TIME_MINUTES", "0")
    monkeypatch.setenv("BOOKING_MAX_DAYS_AHEAD", "7")

    service = BookingService(MockBookingDB())
    future_date = (frozen_now + timedelta(days=7)).strftime("%Y-%m-%d")

    slots = service.get_available_time_slots(date=future_date, robot_id=1)
    # Future date with no existing bookings – all 9 working-hour slots should be available
    assert len(slots) == 9


def test_max_days_ahead_default_is_seven(monkeypatch):
    """When BOOKING_MAX_DAYS_AHEAD is not set the default must be 7."""
    monkeypatch.delenv("BOOKING_MAX_DAYS_AHEAD", raising=False)
    service = BookingService(MockBookingDB())
    assert service.max_booking_days_ahead == 7
