from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from burnout_guardian.app.run_weekly_report import run_weekly_report


app = FastAPI(
    title="Burnout Guardian",
    description="HTTP API for the Burnout Guardian weekly burnout check agent.",
    version="0.1.0",
)


class WeeklyReportRequest(BaseModel):
    user_id: str
    period_start: date
    period_end: date
    session_id: Optional[str] = None


@app.post("/weekly-report")
async def weekly_report_endpoint(req: WeeklyReportRequest):
    """
    Run a weekly burnout check for the given user and period.

    Returns the weekly_report JSON produced by the agent.
    """
    """
    Run a weekly burnout check for the given user and period.

    Returns the weekly_report JSON produced by the agent.
    """
    try:
        data = await run_weekly_report(
            user_id=req.user_id,
            period_start=req.period_start,
            period_end=req.period_end,
            session_id=req.session_id or "weekly-demo-session",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    weekly_report = data.get("weekly_report")
    if not isinstance(weekly_report, dict):
        raise HTTPException(
            status_code=500,
            detail="Missing or invalid 'weekly_report' object in agent response",
        )

    return data

