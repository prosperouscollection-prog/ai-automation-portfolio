# Prompt Versioning and Improvement

## Why Versioning Matters

Genesis AI Systems should treat prompts like product assets, not one-off text blobs. A prompt that improves lead quality, response rate, or booking rate should be documented the same way code changes are documented.

## Version Format

Use a simple versioning pattern:

- `v1.0`: first production-ready version
- `v1.1`: small wording improvement
- `v2.0`: major change in prompt structure, output schema, or role framing

Recommended naming format:

`[Prompt Name] v[Major].[Minor]`

Examples:

- `Lead Score Classifier v1.3`
- `Riley Dental Front Desk v2.0`
- `Monthly ROI Narrator v1.2`

## Change Log Template

For every prompt change, log:

- prompt name
- old version
- new version
- date changed
- what changed
- hypothesis
- result after test

## A/B Testing Workflow

1. Freeze the current production prompt as Version A.
2. Create one deliberate improvement as Version B.
3. Route a controlled percentage of traffic to each version.
4. Track measurable outcomes:
   - response quality score
   - booking rate
   - follow-up rate
   - client satisfaction signal
5. Review after at least `100` interactions.
6. Promote the winner and archive the loser.

## What to Test

Strong variables to test:

- role framing
- urgency criteria
- output structure
- response length
- escalation wording
- CTA phrasing

Weak variables to test:

- random synonyms
- cosmetic wording with no clear business hypothesis

## Documentation Discipline

Every meaningful prompt change should answer:

- what problem were we trying to fix?
- what did we change?
- what improved?
- is the gain worth keeping?

That discipline turns prompts into proprietary process, which is part of the Genesis AI Systems moat.
