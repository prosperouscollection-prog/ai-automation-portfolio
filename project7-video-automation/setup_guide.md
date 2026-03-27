# Setup Guide: AI Video Automation Pipeline

This guide explains how to import and configure `workflow.json` in n8n for Project 7.

## 1. Import the workflow

1. Open n8n.
2. Go to `Settings`.
3. Click `Import from File`.
4. Select `workflow.json` from the `project7-video-automation/` folder.
5. Confirm the import.

After import, you should see these nodes on the canvas from left to right:

1. `Webhook`
2. `OpenAI - Generate Script`
3. `OpenAI - Generate Captions`
4. `OpenAI - Generate Hashtags`
5. `OpenAI - Generate Thumbnail Text`
6. `Google Sheets - Append Row`
7. `Respond to Webhook`

## 2. Set the OpenAI API key as an n8n environment variable

This workflow does not use the n8n OpenAI credential type.

Instead, all 4 HTTP Request nodes read your API key from:

```text
OPENAI_API_KEY
```

### Option A: Local n8n in your terminal

Start n8n like this:

```bash
export OPENAI_API_KEY=sk-your-real-openai-key
n8n start
```

If you already have n8n running, stop it and restart it after setting the variable.

### Option B: Docker Compose

Add this to your `docker-compose.yml`:

```yaml
environment:
  - OPENAI_API_KEY=sk-your-real-openai-key
```

Then restart the container:

```bash
docker compose up -d
```

### Option C: `.env` file with Docker Compose

In your `.env` file:

```text
OPENAI_API_KEY=sk-your-real-openai-key
```

And in `docker-compose.yml`:

```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

This makes the workflow portable across different n8n installations without requiring manual OpenAI credential setup inside the UI.

## 3. Add Google Sheets credentials

1. Open the `Google Sheets - Append Row` node.
2. Create new `Google Sheets OAuth2` credentials.
3. Connect the Google account that owns the destination sheet.
4. Save the credential.
5. In the node, choose the spreadsheet you want to log to.
6. Select the worksheet tab you want to write into.

## 4. Prepare your Google Sheet

Create a sheet with this exact header row:

| Topic | Script | Captions | Hashtags | Thumbnail Text | Timestamp |
| --- | --- | --- | --- | --- | --- |

Then map the node to that sheet.

## 5. Activate the workflow

1. Click `Save`.
2. Toggle the workflow to `Active`.
3. Copy the production webhook URL shown in the `Webhook` node.

For local testing, the workflow expects this exact URL format:

```text
http://localhost:5678/webhook/video-automation?topic=5 reasons to choose Invisalign
```

## 6. Test the workflow

Use your browser or `curl` to hit the webhook.

Example:

```bash
curl "http://localhost:5678/webhook/video-automation?topic=5 reasons to choose Invisalign"
```

## 7. What the response should look like

The webhook should return JSON with:

- `success`
- `topic`
- `script`
- `captions`
- `hashtags`
- `thumbnail_text`
- `timestamp`

This gives you the full content package immediately after the workflow runs.

## 8. What to expect in Google Sheets

After the workflow completes, Google Sheets should get a new row containing:

- The original topic from the webhook query parameter
- The generated 60-second script
- The generated captions block
- The generated hashtag line
- The suggested thumbnail text
- An ISO timestamp showing when the content was created

In demo terms, this proves two things at once:

1. The AI generated the full content package.
2. The automation logged everything for reuse, editing, and team review.

## 9. Important notes

- No OpenAI credential is required in n8n for this version of the workflow.
- Make sure `OPENAI_API_KEY` is available to the running n8n process before testing.
- Replace the placeholder Google Sheet selection with your real sheet.
- Keep the webhook method as `GET` because this demo expects a query parameter topic.
- The 4 generation nodes are standard HTTP Request nodes calling the OpenAI REST API directly, which makes the workflow more stable across n8n versions.
- If you want cleaner captions or structured arrays later, you can add a parser node after each HTTP Request node, but this portfolio version keeps the workflow simple and import-ready.
