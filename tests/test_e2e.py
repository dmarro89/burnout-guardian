"""Lightweight end-to-end style tests for the evaluation pipeline."""

import asyncio
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from types import SimpleNamespace

from burnout_guardian.app import evaluate_e2e


class _DummyEvent:
    """Mimics the ADK event interface used in run_single_scenario."""

    def __init__(self, text: str | None):
        self._text = text
        self.content = SimpleNamespace(parts=[SimpleNamespace(text=text)])

    def is_final_response(self) -> bool:
        return True


class _DummySessionService:
    async def create_session(self, **kwargs) -> None:
        self.last_call = kwargs


class _DummyRunner:
    """Minimal runner substitute that yields predefined events."""

    def __init__(self, responses: list[str]):
        self._responses = responses
        self.session_service = _DummySessionService()
        self.app_name = "burnout_guardian_test"

    async def run_async(self, **kwargs):
        for text in self._responses:
            yield _DummyEvent(text)


def _run_and_capture(coro) -> str:
    """Execute the async scenario helper and capture stdout."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        asyncio.run(coro)
    return buffer.getvalue()


def test_run_single_scenario_success():
    """run_single_scenario should report success when JSON is valid."""
    weekly_report_json = """
    {
      "weekly_report": {
        "user_id": "demo-user",
        "period_start": "2025-11-10",
        "period_end": "2025-11-16",
        "risk_level": "medium",
        "summary_message": "All good",
        "suggested_actions": [{"type": "boundary", "description": "log off by 18:30", "impact": "protect evenings"}]
      }
    }
    """
    fake_runner = _DummyRunner([weekly_report_json])
    original_runner = evaluate_e2e.runner
    evaluate_e2e.runner = fake_runner
    try:
        output = _run_and_capture(
            evaluate_e2e.run_single_scenario(
                scenario_name="demo_success",
                user_id="demo-user",
                period_start=date(2025, 11, 10),
                period_end=date(2025, 11, 16),
                session_id="test-session",
            )
        )
    finally:
        evaluate_e2e.runner = original_runner

    assert "weekly_report OK" in output


def test_run_single_scenario_missing_weekly_report():
    """run_single_scenario should flag responses missing weekly_report."""
    invalid_json = '{"not_weekly": {}}'
    fake_runner = _DummyRunner([invalid_json])
    original_runner = evaluate_e2e.runner
    evaluate_e2e.runner = fake_runner
    try:
        output = _run_and_capture(
            evaluate_e2e.run_single_scenario(
                scenario_name="demo_missing_report",
                user_id="demo-user",
                period_start=date(2025, 11, 10),
                period_end=date(2025, 11, 16),
                session_id="test-session",
            )
        )
    finally:
        evaluate_e2e.runner = original_runner

    assert "Missing or invalid 'weekly_report'" in output
