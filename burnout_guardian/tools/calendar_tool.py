from datetime import datetime
from typing import Dict, List, Any


def get_calendar_events(user_id: str, start: str, end: str) -> Dict[str, List[Dict[str, Any]]]:
    """Return a simple list of calendar events for the given user and date range.

    Args:
        user_id: The id of the user, e.g. "demo-user".
        start: Start of the period in ISO format, e.g. "2025-11-10T00:00:00".
        end: End of the period in ISO format, e.g. "2025-11-16T23:59:59".

    Returns:
        A dictionary with a single key 'events', containing a list of events.
        Each event has:
          - id: a string identifier
          - start_time: ISO string
          - end_time: ISO string
          - type: "meeting" | "focus" | "work" | "break" | "other"
    """
    # For now this is a fake data source with a few hard-coded events.
    start_dt = datetime.fromisoformat(start)
    week_start = start_dt.date().isoformat()

    events = [
        {
            "id": f"{user_id}-mon-morning-meeting",
            "start_time": f"{week_start}T09:00:00",
            "end_time": f"{week_start}T10:00:00",
            "type": "meeting",
        },
        {
            "id": f"{user_id}-mon-afternoon-focus",
            "start_time": f"{week_start}T15:00:00",
            "end_time": f"{week_start}T17:00:00",
            "type": "focus",
        },
        {
            "id": f"{user_id}-mon-late-evening-work",
            "start_time": f"{week_start}T20:30:00",
            "end_time": f"{week_start}T22:00:00",
            "type": "work",
        },
    ]

    return {"events": events}
