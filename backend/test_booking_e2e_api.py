"""Optional API-level booking flow test against a running backend instance.

Required env vars:
- BASE_URL (e.g. http://localhost:8000)
- TOKEN (JWT bearer token)
- ROBOT_ID (active robot id)
"""

from __future__ import annotations

import os
from datetime import datetime

import pytest
requests = pytest.importorskip("requests")


BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
TOKEN = os.getenv("TOKEN", "")
ROBOT_ID = os.getenv("ROBOT_ID", "")


@pytest.mark.skipif(
    not (BASE_URL and TOKEN and ROBOT_ID),
    reason="Set BASE_URL, TOKEN, and ROBOT_ID to run API booking e2e test.",
)
def test_available_slots_to_create_booking_flow():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    today = datetime.now().strftime("%Y-%m-%d")

    slots_resp = requests.get(
        f"{BASE_URL}/bookings/available-slots",
        params={"date": today, "robot_id": int(ROBOT_ID)},
        headers=headers,
        timeout=30,
    )
    assert slots_resp.status_code == 200, slots_resp.text

    slots_payload = slots_resp.json()
    available_slots = slots_payload.get("available_slots", [])
    assert available_slots, "No available slots returned for today"

    selected_slot = available_slots[0]
    create_resp = requests.post(
        f"{BASE_URL}/bookings",
        json={
            "robot_id": int(ROBOT_ID),
            "date": selected_slot["date"],
            "start_time": selected_slot["start_time"],
            "end_time": selected_slot["end_time"],
        },
        headers=headers,
        timeout=30,
    )
    assert create_resp.status_code == 200, create_resp.text

    booking = create_resp.json()
    assert booking["robot_id"] == int(ROBOT_ID)
    assert booking["date"] == selected_slot["date"]
    assert booking["start_time"] == selected_slot["start_time"]
    assert booking["end_time"] == selected_slot["end_time"]
    assert booking.get("id") is not None
