"""Evaluation tests for deterministic Burnout Guardian helpers."""

from datetime import datetime

from burnout_guardian.tools.calendar_tool import get_calendar_events
from burnout_guardian.tools.worklog_tool import get_workdays
from burnout_guardian.tools.checkins_tool import get_weekly_checkin
from burnout_guardian.tools.profile_tool import get_profile_and_history
from burnout_guardian.app.evaluate_e2e import _clean_json_fences


def test_calendar_events_structure() -> None:
    """Calendar events helper should return well formed entries."""
    start = "2025-11-10T00:00:00"
    end = "2025-11-16T23:59:59"
    data = get_calendar_events("demo-user", start, end)

    assert "events" in data, "calendar tool must include an 'events' list"
    events = data["events"]
    assert isinstance(events, list) and events, "calendar tool must return at least one event"

    for event in events:
        assert {"id", "start_time", "end_time", "type"} <= event.keys()
        start_dt = datetime.fromisoformat(event["start_time"])
        end_dt = datetime.fromisoformat(event["end_time"])
        assert start_dt < end_dt, "event start must be before end"
        assert start <= event["start_time"] <= end, "event must fall within requested window"


def test_workdays_cover_week() -> None:
    """Worklog helper should return five ordered workdays with activity times."""
    week_start = "2025-11-10"
    data = get_workdays("demo-user", week_start, "2025-11-16")

    days = data["days"]
    assert len(days) == 5, "demo data should include Monday-Friday"

    parsed_dates = [datetime.fromisoformat(day["date"]) for day in days]
    assert parsed_dates == sorted(parsed_dates), "days must be chronological"

    for day in days:
        assert {"date", "first_activity_time", "last_activity_time", "tasks_completed"} <= day.keys()
        assert day["first_activity_time"] < day["last_activity_time"]
        assert day["tasks_completed"] >= 0


def test_weekly_checkin_levels() -> None:
    """Check-in helper must keep energy/stress inside 1..5."""
    checkin = get_weekly_checkin("demo-user", "2025-11-10")
    for field in ("energy_level", "stress_level"):
        assert 1 <= checkin[field] <= 5, f"{field} should stay within 1..5"


def test_profile_history_structure() -> None:
    """Profile helper must expose both profile and history sections."""
    data = get_profile_and_history("demo-user")
    assert set(data.keys()) == {"user_profile", "history_summary"}

    profile = data["user_profile"]
    history = data["history_summary"]

    assert profile["user_id"] == "demo-user"
    assert "preferred_work_hours" in profile
    assert history["weeks_observed"] >= 1
    assert history["num_high_risk_weeks_last_month"] >= 0


def test_clean_json_fences_handles_code_blocks() -> None:
    """Helper should strip ```json fences so downstream parsing works."""
    fenced = """```json
{
  "weekly_report": {"user_id": "demo-user"}
}
```"""
    assert _clean_json_fences(fenced).startswith("{")
