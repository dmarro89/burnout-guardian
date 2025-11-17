import asyncio
import json
from datetime import date
from typing import Optional

from google.genai import types

from burnout_guardian.agent_app import runner
from burnout_guardian.app.run_weekly_report import clean_json_fences


async def run_single_scenario(
    scenario_name: str,
    user_id: str,
    period_start: date,
    period_end: date,
    session_id: Optional[str] = None,
) -> None:
    """Runs the full Burnout Guardian pipeline for one scenario and validates the output."""

    if session_id is None:
        session_id = f"eval-e2e-{scenario_name}"

    prompt = (
        "Run a weekly burnout check.\n\n"
        f"user_id: {user_id}\n"
        f"period_start: {period_start.isoformat()}\n"
        f"period_end: {period_end.isoformat()}\n\n"
        "Return ONLY the weekly_report JSON. Do not include explanations."
    )

    user_content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
    )

    final_text = None

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text and text != "None":
                final_text = text

    if not final_text:
        print(f"[{scenario_name}] No final response from agent")
        return

    cleaned = clean_json_fences(final_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"[{scenario_name}] Invalid JSON in final response")
        print(cleaned)
        return

    weekly_report = data.get("weekly_report")
    if not isinstance(weekly_report, dict):
        print(f"[{scenario_name}] Missing or invalid 'weekly_report' object")
        print(json.dumps(data, indent=2))
        return

    required_keys = [
        "user_id",
        "period_start",
        "period_end",
        "risk_level",
        "summary_message",
        "suggested_actions",
    ]
    missing = [k for k in required_keys if k not in weekly_report]
    if missing:
        print(f"[{scenario_name}] Missing keys in weekly_report: {missing}")
        print(json.dumps(weekly_report, indent=2))
        return

    if not isinstance(weekly_report["suggested_actions"], list) or not weekly_report["suggested_actions"]:
        print(f"[{scenario_name}] suggested_actions is missing or empty")
        print(json.dumps(weekly_report, indent=2))
        return

    risk = weekly_report.get("risk_level")
    print(f"[{scenario_name}] weekly_report OK (risk_level={risk})")


async def run_all_e2e_evals() -> None:
    """Runs end-to-end evaluation scenarios."""

    await run_single_scenario(
        scenario_name="demo_baseline_week",
        user_id="demo-user",
        period_start=date(2025, 11, 10),
        period_end=date(2025, 11, 16),
    )


def main() -> None:
    asyncio.run(run_all_e2e_evals())


if __name__ == "__main__":
    main()
