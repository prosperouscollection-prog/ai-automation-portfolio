# AI Video Automation Pipeline Workflow Design

This document describes the full `n8n + OpenAI API + Google Sheets` workflow for Project 7.

## Goal

Accept a topic by webhook, generate a short-form video content package, log the result to Google Sheets, and return the content as JSON.

## High-Level Flow

```text
Webhook
  -> Set Topic
  -> OpenAI: Generate Script
  -> OpenAI: Generate Captions
  -> OpenAI: Generate Hashtags
  -> OpenAI: Generate Thumbnail Text
  -> Set Response Payload
  -> Google Sheets: Append Row
  -> Respond to Webhook
```

## n8n Nodes

### 1. Webhook

- Node Type: `Webhook`
- Method: `POST`
- Path: `/video-content`
- Purpose: Accept the incoming topic from a client app, form, or demo request.

Example request body:

```json
{
  "topic": "5 reasons to choose Invisalign"
}
```

Expected behavior:

- Reject empty requests
- Pass the topic to the next node

### 2. Set Topic

- Node Type: `Set`
- Purpose: Normalize the incoming payload into a clean shape for the rest of the workflow

Fields to set:

- `topic` -> `{{$json.topic}}`
- `timestamp` -> `{{$now}}`

### 3. OpenAI: Generate Script

- Node Type: `OpenAI Chat`
- Purpose: Generate a 60-second short-form video script with a hook, body, and CTA

Prompt:

```text
You are an expert short-form video scriptwriter for local businesses.

Create a 60-second vertical video script for this topic: "{topic}"

Requirements:
- Write for a dental office audience
- Keep the tone clear, modern, helpful, and conversion-focused
- Include:
  1. Hook
  2. Body
  3. CTA
- Make the hook strong enough to stop the scroll
- Make the body easy to speak on camera
- Make the CTA invite the viewer to book, call, or message
- Return plain text only in this format:

Hook: ...
Body: ...
CTA: ...
```

Output field:

- `script`

### 4. OpenAI: Generate Captions

- Node Type: `OpenAI Chat`
- Purpose: Generate 5 caption options for Instagram, TikTok, and Facebook

Prompt:

```text
You are an expert social media copywriter for local businesses.

Create 5 short-form social media captions for this topic: "{topic}"

Requirements:
- Write for Instagram, TikTok, and Facebook
- Keep each caption engaging and easy to skim
- Use a friendly, local-business tone
- Include subtle calls to action where appropriate
- Return plain text only
- Number each caption from 1 to 5
```

Output field:

- `captions`

### 5. OpenAI: Generate Hashtags

- Node Type: `OpenAI Chat`
- Purpose: Generate 10 relevant hashtags for the topic

Prompt:

```text
You are an expert social media strategist for local businesses.

Generate 10 relevant hashtags for this topic: "{topic}"

Requirements:
- Focus on discoverability and local-business relevance
- Include hashtags related to dentistry, Invisalign, smile transformation, and oral health when relevant
- Return plain text only
- Output exactly 10 hashtags in one line separated by spaces
```

Output field:

- `hashtags`

### 6. OpenAI: Generate Thumbnail Text

- Node Type: `OpenAI Chat`
- Purpose: Generate a short thumbnail overlay text suggestion

Prompt:

```text
You are an expert short-form video creative strategist.

Generate one thumbnail text overlay for this topic: "{topic}"

Requirements:
- Keep it punchy
- Maximum 6 words
- Make it attention-grabbing
- Return plain text only
- Do not include quotation marks
```

Output field:

- `thumbnail_text`

### 7. Set Response Payload

- Node Type: `Set`
- Purpose: Assemble all generated content into one clean JSON payload for both storage and response

Fields to set:

- `topic`
- `script`
- `captions`
- `hashtags`
- `thumbnail_text`
- `timestamp`

Recommended JSON response shape:

```json
{
  "success": true,
  "topic": "5 reasons to choose Invisalign",
  "script": "Hook: ...\nBody: ...\nCTA: ...",
  "captions": [
    "...",
    "...",
    "...",
    "...",
    "..."
  ],
  "hashtags": [
    "#Invisalign",
    "#SmileMakeover",
    "#DentalCare",
    "#Orthodontics",
    "#ClearAligners",
    "#HealthySmile",
    "#ConfidentSmile",
    "#SmileTransformation",
    "#DentistTips",
    "#LocalDentist"
  ],
  "thumbnail_text": "Why Invisalign Wins",
  "timestamp": "2026-03-27T12:00:00Z"
}
```

### 8. Google Sheets: Append Row

- Node Type: `Google Sheets`
- Operation: `Append`
- Purpose: Store every content package for later review, reuse, or reporting

Sheet columns:

| Column | Value |
| --- | --- |
| Topic | topic |
| Script | full script text |
| Captions | captions joined with line breaks |
| Hashtags | hashtags joined with spaces |
| Thumbnail Text | thumbnail_text |
| Timestamp | timestamp |

Recommended formatting:

- `Script`: multiline text
- `Captions`: 5 captions joined with `\n\n`
- `Hashtags`: single line string

### 9. Respond to Webhook

- Node Type: `Respond to Webhook`
- Purpose: Return the generated content package to the caller

Response body:

```json
{
  "success": true,
  "topic": "5 reasons to choose Invisalign",
  "script": "Hook: ...\nBody: ...\nCTA: ...",
  "captions": [
    "...",
    "...",
    "...",
    "...",
    "..."
  ],
  "hashtags": [
    "#Invisalign",
    "#SmileMakeover",
    "#DentalCare",
    "#Orthodontics",
    "#ClearAligners",
    "#HealthySmile",
    "#ConfidentSmile",
    "#SmileTransformation",
    "#DentistTips",
    "#LocalDentist"
  ],
  "thumbnail_text": "Why Invisalign Wins",
  "timestamp": "2026-03-27T12:00:00Z"
}
```

## Node Connection Order

Connect the nodes in this exact sequence:

1. `Webhook`
2. `Set Topic`
3. `OpenAI: Generate Script`
4. `OpenAI: Generate Captions`
5. `OpenAI: Generate Hashtags`
6. `OpenAI: Generate Thumbnail Text`
7. `Set Response Payload`
8. `Google Sheets: Append Row`
9. `Respond to Webhook`

## Notes for Demo Use

- Use the topic `5 reasons to choose Invisalign` during demos because it produces a strong dental-office marketing example.
- Show the final JSON response first, then open Google Sheets to prove the workflow logged the content automatically.
- Position the system as a repeatable content engine, not just a one-off text generator.
