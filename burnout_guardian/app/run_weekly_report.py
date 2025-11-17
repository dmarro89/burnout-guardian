import asyncio
from datetime import date
import json
from typing import Any, Dict

from google.genai import types

from burnout_guardian.agent_app import runner


def clean_json_fences(text: str) -> str:
    """Remove ```json fences if present and return raw JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.lstrip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return cleaned


async def run_weekly_report(
    user_id: str,
    period_start: date,
    period_end: date,
    session_id: str = "weekly-demo-session",
) -> Dict[str, Any]:
    """Runs a full weekly burnout check for a given user and prints the report."""

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
        raise RuntimeError("No final response from agent")

    cleaned = clean_json_fences(final_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Agent returned invalid JSON: {e}") from e

    return data


async def _demo() -> None:
    result = await run_weekly_report(
        user_id="demo-user",
        period_start=date(2025, 11, 10),
        period_end=date(2025, 11, 16),
    )

    print(json.dumps(result, indent=2))


def main() -> None:
    asyncio.run(_demo())


if __name__ == "__main__":
    main()
