from datetime import date
from typing import Dict, Any


def get_weekly_checkin(user_id: str, week_start: str) -> Dict[str, Any]:
    """Returns a simple self-check for a given week.

    Args:
        user_id: The id of the user, e.g. "demo-user".
        week_start: Monday of the week in ISO format "YYYY-MM-DD".

    Returns:
        A dictionary describing how the person felt that week:
          - week_start: "YYYY-MM-DD"
          - energy_level: int from 1 (empty) to 5 (full of energy)
          - stress_level: int from 1 (very calm) to 5 (very stressed)
          - note: optional short text
    """
    _ = date.fromisoformat(week_start)  # validate the format

    return {
        "week_start": week_start,
        "energy_level": 3,
        "stress_level": 4,
        "note": "Back-to-back meetings and a couple of late evenings.",
    }
