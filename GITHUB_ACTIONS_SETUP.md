# GitHub Actions Workflow Trigger Setup

## Problem
When you use Telegram commands like `/prospects` (lead generator), `/content` (marketing agent), etc., they trigger GitHub Actions workflows. If `GITHUB_TOKEN` isn't configured on Render, the workflow trigger fails silently, showing "❌ Lead generator failed."

## Solution: Add GITHUB_TOKEN to Render

### Step 1: Create a Personal Access Token on GitHub

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Set these details:
   - **Token name:** `Genesis AI Render Trigger`
   - **Expiration:** 90 days (or Never, up to you)
   - **Scopes:** Check these boxes:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
     - ✅ `actions` (Manage GitHub Actions)
4. Click "Generate token"
5. **Copy the token** (you'll only see it once!)

### Step 2: Add to Render Dashboard

1. Go to https://dashboard.render.com
2. Select your app: `genesis-ai-systems-demo`
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Key: `GITHUB_TOKEN`
6. Value: `ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (paste your token)
7. Click "Add"
8. Click "Deploy" at the top to apply changes

### Step 3: Test It

1. Open Telegram and send `/prospects` to Genesis AI Systems bot
2. You should see: `✅ Lead Generator running!`
3. Wait ~10 seconds, then check https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions to see the workflow run

## How It Works

When you run a Telegram command:
- Demo server on Render sends a request to GitHub API
- GitHub Actions starts the workflow (e.g., lead_generator_agent.yml)
- Workflow runs and finds prospects, sends SMS alerts, etc.
- Results appear within minutes

## Workflow Commands

- `/prospects` → Runs `lead_generator_agent.yml`
- `/content` → Runs `marketing_agent.yml`
- `/followup` → Runs `sales_agent.yml`
- `/deploy` → Runs `deploy_agent.yml`

## Troubleshooting

If workflows still don't trigger:
1. Verify the token is set on Render (refresh the page)
2. Check token has `workflow` scope on GitHub
3. Verify repository name: `prosperouscollection-prog/ai-automation-portfolio`
4. Check GitHub Actions logs for detailed errors

