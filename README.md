# Burnout Guardian

> Stop before your job stops you.

Burnout Guardian is a small multi-agent system that looks at how you worked during the week and tells you, in plain language, if you’re drifting into burnout territory – plus a few concrete things you can change for next week.

I built it as the capstone project for the **Google Agents Intensive**. It’s not meant to “fix” toxic environments (nothing does), but it can at least make early signals visible instead of letting them pile up quietly in your calendar.

---

## 1. What problem it tries to solve

Most knowledge workers live in some version of this loop:

- weeks packed with meetings and late evenings,
- a vague feeling of “I’m exhausted but I can’t even explain why”,
- and no simple way to see how their week actually looked from a burnout point of view.

Companies sometimes run surveys or send wellbeing emails, but those are usually disconnected from the *real* signals: calendars, workload patterns, and how people actually feel over time.

**Burnout Guardian** focuses on one simple thing:

> Once per week, take a snapshot of how you worked, estimate your burnout risk, and suggest 2–3 small, realistic changes for the next week.

No dashboards, no 20-page reports. Just one weekly check and a short, honest summary.

---

## 2. What Burnout Guardian actually does

Given:

- `user_id`
- `period_start` (YYYY-MM-DD)
- `period_end` (YYYY-MM-DD)

the system:

1. **Collects a synthetic “week snapshot”**  
   (calendar events, workdays, a weekly self-checkin).

2. **Computes simple metrics** for that week, such as:
   - total hours worked,
   - average hours per day,
   - how many late evenings,
   - whether weekends were touched,
   - how much time was spent in meetings,
   - how often the person had no real breaks,
   - self-reported energy and stress (if available).

3. **Estimates burnout risk** for that period, taking into account:
   - the person’s preferred work hours,
   - their limits (max hours, late evenings, weekend policy),
   - and a short history of recent weeks.

4. **Produces a weekly report**:
   - a short summary in natural language,
   - a `risk_level` (`low`, `medium`, `high`),
   - 2–3 concrete actions the person can experiment with next week.

Everything is returned as a single JSON object:

```json
{
  "weekly_report": {
    "user_id": "demo-user",
    "period_start": "2025-11-10",
    "period_end": "2025-11-16",
    "risk_level": "medium",
    "summary_message": "This week looks quite intense...",
    "suggested_actions": [
      {
        "type": "schedule_change",
        "description": "Try blocking out 30 minutes each day for a real lunch break.",
        "impact": "Stepping away can help you recharge and reduce feelings of overwhelm."
      }
    ]
  }
}
```
---

## 3. How this maps to the course feature list

The project uses several of the concepts from the “Features to Include in Your Agent Submission” list.  
Here’s how Burnout Guardian lines up with that checklist.

### Multi-agent system

- **Agent powered by an LLM**  
  All four sub-agents (`data_collector`, `workload_analyzer`, `risk_scorer`, `wellbeing_coach`) are LLM-powered agents.

- **Sequential agents**  
  The root `burnout_guardian` agent is a **SequentialAgent** that runs the four sub-agents in order:
  1. collect data  
  2. compute metrics  
  3. score risk  
  4. coach the user  

---

### Tools

- **Custom tools**  
  Implemented for domain-specific data:
  - `get_calendar_events`
  - `get_workdays`
  - `get_weekly_checkin`
  - `get_profile_and_history`

- **Built-in tools (Code Execution)**  
  The `workload_analyzer` uses the built-in **Code Execution** tool to run small Python snippets for:
  - time arithmetic,
  - aggregations,
  - averages across days.

---

### Sessions & Memory

- **Sessions & state management**  
  - Uses `InMemorySessionService` in the ADK `Runner`.
  - Sessions are created per `(user_id, period)` and reused as needed.

- **Long term memory**  
  - Uses `InMemoryMemoryService`.
  - The `wellbeing_coach`:
    - can load previous sessions via `preload_memory`,
    - and a callback automatically saves the current session to memory after each weekly report.
  - This lets the agent compare the current week with recent weeks for the same user.

---

### Observability

- **Logging, Tracing, Metrics**  
  A custom `LoggingPlugin` logs:
  - user messages,
  - agent start/completion,
  - LLM requests and responses (including token usage),
  - tool calls and their arguments,
  - session IDs and invocation IDs.

  This is enough to trace the full multi-agent flow for a single weekly run and to debug behaviors.

---

### Agent evaluation

- **Agent evaluation**  
  A small end-to-end evaluation script:
  - runs the full weekly pipeline for a sample period,
  - parses the final response as JSON,
  - validates the `weekly_report` schema (required keys and non-empty actions),
  - fails loudly if the contract is broken.

  It is not a formal benchmark, but it protects the main contract of the agent while iterating.

---

### Agent deployment

- **Agent deployment**  
  The project exposes a small HTTP API:

  - `POST /weekly-report` (FastAPI)
  - wraps the same `run_weekly_report` function used by the CLI,
  - returns the final `weekly_report` JSON.

  This entrypoint can be containerised and deployed on **Cloud Run** or a similar cloud runtime, which matches the “Agent Engine or similar Cloud-based runtime” requirement from the course.
