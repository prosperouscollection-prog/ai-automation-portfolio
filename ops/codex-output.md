# Task 2 — Validate Confidence Fix Targets

## Hunter confidence references
- There are no remaining `confidence_score` references in `.github/workflows/scripts/email_acquisition.py`.
- Current Hunter-aware ranking now uses `confidence` instead:
  - `.github/workflows/scripts/email_acquisition.py:235-244`
  - `.github/workflows/scripts/email_acquisition.py:414-416`
  - `.github/workflows/scripts/email_acquisition.py:527-533`
  - `.github/workflows/scripts/email_acquisition.py:582-587`
  - `.github/workflows/scripts/email_acquisition.py:607-624`
- Current code snippets:
  - `_candidate_strength()` reads `candidate.get("confidence", 0)`.
  - `_normalize_candidate()` stores `candidate["confidence"]`.
  - Pass builders for structured provider, website extraction, same-domain match, domain pattern, directory listing, and general-contact fallback all emit `confidence`, not `confidence_score`.

## Outscraper score references
- There are no Outscraper confidence-score dependencies left in the acquisition engine.
- The only remaining `score` references in `.github/workflows/scripts/email_acquisition.py` are the canonical sheet-row fields, not email-ranking logic:
  - `.github/workflows/scripts/email_acquisition.py:31`
  - `.github/workflows/scripts/email_acquisition.py:148-151`
  - `.github/workflows/scripts/email_acquisition.py:172`
- Current code snippets:
  - `build_canonical_sheet_row()` reads `record.get("score")` only to preserve the sheet’s score column and qualification status.
  - Acquisition ranking does not use `score` anywhere in `_candidate_strength()` or the email acquisition passes.

## Validation result
- Validation passed for the current worktree state: Hunter ranking now uses the real `confidence` field, and Outscraper does not rely on a confidence-score dependency in acquisition logic.
- No code was changed in this validation step.
