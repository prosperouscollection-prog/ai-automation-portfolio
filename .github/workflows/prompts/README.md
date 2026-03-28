# Genesis AI Systems — Auto Prompt Deployer

## What This Does
Automatically runs all Codex prompts using the OpenAI API with a larger API context window instead of relying on the Codex desktop app context limit.

## How To Run

### Run all 4 prompts
```bash
cd .github/workflows/scripts
python run_all_prompts.py
```

### Run a specific prompt
```bash
cd .github/workflows/scripts
python run_all_prompts.py --prompt 1
```

### Run via GitHub Actions
1. Open the GitHub Actions tab.
2. Select `Auto Prompt Deployer`.
3. Click `Run workflow`.
4. Choose a prompt number where `0` means run all prompts.

## Cost
- Full run estimate: about `$0.35`
- Single prompt estimate: about `$0.09`

## Time
- Full run estimate: about `4 minutes`
- Single prompt estimate: about `1 minute`

## What Gets Created
- 49 files across the portfolio
- Branded Genesis AI Systems deliverables
- Production-ready implementation payloads

## Adding New Prompts
1. Create a new markdown file in `.github/workflows/prompts/`.
2. Name it using the pattern `prompt5_[description].md`.
3. Run `python run_all_prompts.py --prompt 5`.

## Self-Updating
The Evolution Agent can review these prompt payloads and update them when new platform capabilities, branding changes, or implementation requirements appear.

## Requirements
- `OPENAI_API_KEY` in `.env` or GitHub Actions secrets
- Minimum balance target: `$2.00`
- Default model: `gpt-4.1`
