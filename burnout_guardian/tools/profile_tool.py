from typing import Dict, Any


def get_profile_and_history(user_id: str) -> Dict[str, Any]:
    """Returns the user's work boundaries and a short history summary.

    Args:
        user_id: The id of the user, e.g. "demo-user".

    Returns:
        A dictionary with:
          - user_profile: the person's own limits and preferences
          - history_summary: a compact view of recent weeks
    """
    user_profile = {
        "user_id": user_id,
        "preferred_work_hours": {"start": "09:00", "end": "18:00"},
        "max_hours_per_week": 45,
        "max_late_evenings_per_week": 2,
        "allow_weekend_work": False,
    }

    history_summary = {
        "weeks_observed": 4,
        "avg_hours_last_weeks": 48.0,
        "trend_stress_level": "up",  # "up" | "down" | "flat"
        "num_high_risk_weeks_last_month": 2,
    }

    return {
        "user_profile": user_profile,
        "history_summary": history_summary,
    }
