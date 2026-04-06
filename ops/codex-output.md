# Codex Output
loop_cycle: pilot-email-draft-prompt-fix

## Task
Updated the prospect pilot draft prompt so the AI now gets the business context and cold outreach rules needed to write a tighter email for Detroit small business owners.

## Files Changed
- `v1-revenue-system/scripts/run_prospect_pilot.py`
- `v1-revenue-system/lead_revenue_pipeline.py`
- `ops/codex-output.md`

## What Changed
- In `main()` inside `run_prospect_pilot.py`, replaced the old draft payload with:
  - `business_name: record.get("business name")`
  - `owner_email: record.get("owner_email")`
  - `industry: record.get("source") or "retail"`
  - `domain: record.get("domain")`
  - `system_prompt: <new cold outreach instruction block>`
- In `OpenAIDraftClient.generate()` inside `lead_revenue_pipeline.py`, added support for a custom `system_prompt` so the pilot can actually use the richer instructions.
- Kept the existing fallback prompt path for other callers that do not pass `system_prompt`.

## Prompt Intent
The new pilot prompt tells the model to:
- write a short cold email for Genesis AI Systems
- sound like a real person
- keep the subject under 8 words
- open with a real business pain point
- keep the body to 2 to 3 short sentences
- ask for 10 minutes this week
- sign off with Trendell Fordham and Genesis AI Systems
- avoid Calendly, placeholders, and buzzwords
- return one email only as JSON

## Verification
- Confirmed the updated pilot call site now passes the richer payload.
- Confirmed the shared draft client reads and uses `system_prompt` when present.
- No runtime send was triggered.

## Commit Message
`fix(pilot): richer draft prompt for email copy quality`
