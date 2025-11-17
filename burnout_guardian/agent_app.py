import logging

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import preload_memory

from burnout_guardian.tools.calendar_tool import get_calendar_events
from burnout_guardian.tools.worklog_tool import get_workdays
from burnout_guardian.tools.checkins_tool import get_weekly_checkin
from burnout_guardian.tools.profile_tool import get_profile_and_history


MODEL_ID = "gemini-2.0-flash"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


async def auto_save_to_memory(callback_context):
    """Automatically save the full session to memory after each agent turn."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )


def build_burnout_guardian_agent() -> SequentialAgent:
    """Builds the main Burnout Guardian agent with its sub-agents."""

    data_collector = LlmAgent(
        name="data_collector",
        model=MODEL_ID,
        description="Collects weekly work data (calendar, work log, check-ins).",
        instruction=(
            "Your job is to gather all relevant information about how the user worked "
            "during the given week.\n\n"
            "You MUST:\n"
            "1) Call get_calendar_events with the user id and the ISO start/end timestamps.\n"
            "2) Call get_workdays with the user id and the ISO start/end dates.\n"
            "3) Call get_weekly_checkin with the user id and the Monday of that week.\n\n"
            "You are NOT allowed to invent calendar events, workdays or check-ins. "
            "All such data MUST come from these tools. If you do not call the tools, "
            "your answer is considered incorrect.\n\n"
            "Then you combine the tool results into a single JSON object called 'week_snapshot'.\n"
            "The JSON MUST have exactly this shape:\n\n"
            "{\n"
            '  \"week_snapshot\": {\n'
            '    \"user_id\": \"...\",\n'
            '    \"period_start\": \"YYYY-MM-DD\",\n'
            '    \"period_end\": \"YYYY-MM-DD\",\n'
            '    \"calendar_events\": [\n'
            '      {\"id\": \"...\", \"start_time\": \"YYYY-MM-DDTHH:MM:SS\", '
            '\"end_time\": \"YYYY-MM-DDTHH:MM:SS\", \"type\": \"meeting|focus|work|break|other\"}\n'
            "    ],\n"
            '    \"workdays\": [\n'
            '      {\"date\": \"YYYY-MM-DD\", \"first_activity_time\": \"HH:MM\", '
            '\"last_activity_time\": \"HH:MM\", \"tasks_completed\": <int>}\n'
            "    ],\n"
            '    \"weekly_checkin\": {\n'
            '      \"week_start\": \"YYYY-MM-DD\",\n'
            '      \"energy_level\": <int 1-5>,\n'
            '      \"stress_level\": <int 1-5>,\n'
            '      \"note\": \"...\" (optional)\n'
            "    }\n"
            "  }\n"
            "}\n\n"
            "Do NOT return explanations, markdown or text outside that JSON. "
            "Do NOT return markdown code fences (no ```json). "
            "Your final answer MUST be only that JSON."
        ),
        tools=[
            get_calendar_events,
            get_workdays,
            get_weekly_checkin,
        ],
    )

    workload_analyzer = LlmAgent(
        name="workload_analyzer",
        model=MODEL_ID,
        code_executor=BuiltInCodeExecutor(),
        description="Turns a week of activity into simple metrics.",
        instruction=(
            "You receive as input the JSON produced by the data_collector.\n"
            "It always has this structure:\n"
            "{ \"week_snapshot\": { ... } }\n\n"
            "From this, you calculate simple metrics for that week:\n"
            "- total_hours: total hours worked in the period\n"
            "- avg_hours_per_day\n"
            "- late_evenings: number of days where work ended after the user's normal end time\n"
            "- weekend_days_worked\n"
            "- meeting_hours\n"
            "- num_meetings\n"
            "- days_without_real_breaks\n"
            "- checkin_energy (if present)\n"
            "- checkin_stress (if present)\n\n"
            "You are allowed to write and execute small Python code snippets using the "
            "built-in code execution tool to do time arithmetic or aggregations when needed. "
            "Use code execution when computing durations, sums or averages across days.\n\n"
            "You MUST respond with a JSON object called 'weekly_metrics' with exactly these keys:\n"
            "{\n"
            '  \"weekly_metrics\": {\n'
            '    \"user_id\": \"...\",\n'
            '    \"period_start\": \"YYYY-MM-DD\",\n'
            '    \"period_end\": \"YYYY-MM-DD\",\n'
            '    \"total_hours\": <float>,\n'
            '    \"avg_hours_per_day\": <float>,\n'
            '    \"late_evenings\": <int>,\n'
            '    \"weekend_days_worked\": <int>,\n'
            '    \"meeting_hours\": <float>,\n'
            '    \"num_meetings\": <int>,\n'
            '    \"days_without_real_breaks\": <int>,\n'
            '    \"checkin_energy\": <int or null>,\n'
            '    \"checkin_stress\": <int or null>\n'
            "  }\n"
            "}\n\n"
            "Do NOT add natural language explanations. Only return that JSON."
        ),
        tools=[],
    )

    risk_scorer = LlmAgent(
        name="risk_scorer",
        model=MODEL_ID,
        description="Estimates burnout risk for the week.",
        instruction=(
            "You receive a JSON object with weekly_metrics for a given period.\n"
            "Before deciding anything, you MUST call the get_profile_and_history "
            "tool to load the person's own limits and a short summary of recent weeks.\n\n"
            "The tool returns:\n"
            "{\n"
            '  \"user_profile\": {\n'
            '    \"user_id\": \"...\",\n'
            '    \"preferred_work_hours\": {\"start\": \"HH:MM\", \"end\": \"HH:MM\"},\n'
            '    \"max_hours_per_week\": <int>,\n'
            '    \"max_late_evenings_per_week\": <int>,\n'
            '    \"allow_weekend_work\": <true|false>\n'
            "  },\n"
            '  \"history_summary\": {\n'
            '    \"weeks_observed\": <int>,\n'
            '    \"avg_hours_last_weeks\": <float>,\n'
            '    \"trend_stress_level\": \"up\" | \"down\" | \"flat\",\\n'
            '    \"num_high_risk_weeks_last_month\": <int>\n'
            "  }\n"
            "}\n\n"
            "Combine weekly_metrics with user_profile and history_summary to decide:\n"
            "- risk_level: low | medium | high\n"
            "- score: a number between 0 and 1\n"
            "- reasons: 2–5 short sentences focusing on work patterns.\n\n"
            "You MUST respond with a JSON object called 'risk_assessment', like this:\n"
            "{\n"
            '  \"risk_assessment\": {\n'
            '    \"user_id\": \"...\",\n'
            '    \"period_start\": \"YYYY-MM-DD\",\n'
            '    \"period_end\": \"YYYY-MM-DD\",\n'
            '    \"risk_level\": \"low|medium|high\",\n'
            '    \"score\": <float between 0 and 1>,\n'
            '    \"reasons\": [\"...\", \"...\"]\n'
            "  }\n"
            "}\n\n"
            "Do NOT output anything outside that JSON."
        ),
        tools=[
            get_profile_and_history,
        ],
    )

    wellbeing_coach = LlmAgent(
        name="wellbeing_coach",
        model=MODEL_ID,
        description="Explains what is going on and suggests small changes.",
        instruction=(
            "You receive two JSON objects:\n"
            "- weekly_metrics: the numbers describing what happened this week.\n"
            "- risk_assessment: the risk level, score and reasons.\n\n"
            "Before answering, you MAY load previous sessions from memory. "
            "If memory has relevant past weeks for this same user, briefly compare "
            "the current week with the recent trend (for example: 'this is your third "
            "busy week in a row' or 'this week looks calmer than the last two').\n\n"
            "Your job is to talk to the user like a calm, honest colleague.\n"
            "You should:\n"
            "- Summarise the situation in one short, clear message.\n"
            "- Suggest 2–3 small, realistic changes the person can try next week.\n"
            "- Keep the focus on work patterns, not on judging the person.\n\n"
            "Suggested actions should be concrete, for example:\n"
            "- blocking meeting-free time,\n"
            "- setting a latest time to stop working,\n"
            "- taking one full day with no work.\n\n"
            "You MUST respond with a JSON object called 'weekly_report', like this:\n"
            "{\n"
            '  \"weekly_report\": {\n'
            '    \"user_id\": \"...\",\n'
            '    \"period_start\": \"YYYY-MM-DD\",\n'
            '    \"period_end\": \"YYYY-MM-DD\",\n'
            '    \"risk_level\": \"low|medium|high\",\n'
            '    \"summary_message\": \"short text...\",\n'
            '    \"suggested_actions\": [\n'
            '      {\n'
            '        \"type\": \"schedule_change\" | \"boundary\" | \"experiment\",\n'
            '        \"description\": \"what to do\",\n'
            '        \"impact\": \"why this helps\"\n'
            "      }\n"
            "    ]\n"
            "  }\n"
            "}\n\n"
            "Do NOT return any free text outside that JSON."
        ),
        tools=[
            preload_memory
        ],
        after_agent_callback=auto_save_to_memory,

    )

    burnout_guardian = SequentialAgent(
        name="burnout_guardian",
        sub_agents=[
            data_collector,
            workload_analyzer,
            risk_scorer,
            wellbeing_coach,
        ],
    )

    return burnout_guardian


# --- services + runner ----------------------------------------------------

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

runner = Runner(
    agent=build_burnout_guardian_agent(),
    session_service=session_service,
    memory_service=memory_service,
    app_name="burnout_guardian",
    plugins=[LoggingPlugin()],
)
