from datetime import date
from typing import Dict, List, Any


def get_workdays(user_id: str, period_start: str, period_end: str) -> Dict[str, List[Dict[str, Any]]]:
    """Returns a simple work log for each day in the given period.

    Args:
        user_id: The id of the user, e.g. "demo-user".
        period_start: Start date in ISO format "YYYY-MM-DD".
        period_end: End date in ISO format "YYYY-MM-DD".

    Returns:
        A dictionary with a single key 'days', containing a list of days.
        Each entry has:
          - date: "YYYY-MM-DD"
          - first_activity_time: "HH:MM"
          - last_activity_time: "HH:MM"
          - tasks_completed: int
    """
    start = date.fromisoformat(period_start)

    def t(h: int, m: int) -> str:
        return f"{h:02d}:{m:02d}"

    days: List[Dict[str, Any]] = [
        {
            "date": start.isoformat(),  
            "first_activity_time": t(8, 45),
            "last_activity_time": t(22, 0),
            "tasks_completed": 7,
        },
        {
            "date": (start.replace(day=start.day + 1)).isoformat(),  
            "first_activity_time": t(9, 10),
            "last_activity_time": t(19, 0),
            "tasks_completed": 5,
        },
        {
            "date": (start.replace(day=start.day + 2)).isoformat(),  
            "first_activity_time": t(9, 0),
            "last_activity_time": t(18, 30),
            "tasks_completed": 4,
        },
        {
            "date": (start.replace(day=start.day + 3)).isoformat(),  
            "first_activity_time": t(9, 15),
            "last_activity_time": t(21, 30),
            "tasks_completed": 6,
        },
        {
            "date": (start.replace(day=start.day + 4)).isoformat(),  
            "first_activity_time": t(9, 0),
            "last_activity_time": t(18, 0),
            "tasks_completed": 3,
        },
    ]

    return {"days": days}
