"""
Prompt builders for Project 7: AI Video Automation Pipeline.

This module has a single responsibility: generate consistent prompt strings for
each content-generation step in the workflow. Keeping prompts in one module
makes the pipeline easier to maintain, test, and extend without changing n8n
workflow logic elsewhere.
"""

from __future__ import annotations


def _normalize_topic(topic: str) -> str:
    """Validate and normalize a topic before building prompt text."""
    cleaned_topic = topic.strip()
    if not cleaned_topic:
        raise ValueError("Topic must be a non-empty string.")
    return cleaned_topic


def SCRIPT_PROMPT(topic: str) -> str:
    """Return the script-generation prompt for a given topic."""
    cleaned_topic = _normalize_topic(topic)
    return f"""
You are an expert short-form video scriptwriter for local businesses.

Create a 60-second vertical video script for this topic: "{cleaned_topic}"

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
""".strip()


def CAPTIONS_PROMPT(topic: str) -> str:
    """Return the caption-generation prompt for a given topic."""
    cleaned_topic = _normalize_topic(topic)
    return f"""
You are an expert social media copywriter for local businesses.

Create 5 short-form social media captions for this topic: "{cleaned_topic}"

Requirements:
- Write for Instagram, TikTok, and Facebook
- Keep each caption engaging and easy to skim
- Use a friendly, local-business tone
- Include subtle calls to action where appropriate
- Return plain text only
- Number each caption from 1 to 5
""".strip()


def HASHTAGS_PROMPT(topic: str) -> str:
    """Return the hashtag-generation prompt for a given topic."""
    cleaned_topic = _normalize_topic(topic)
    return f"""
You are an expert social media strategist for local businesses.

Generate 10 relevant hashtags for this topic: "{cleaned_topic}"

Requirements:
- Focus on discoverability and local-business relevance
- Include hashtags related to dentistry, Invisalign, smile transformation, and oral health when relevant
- Return plain text only
- Output exactly 10 hashtags in one line separated by spaces
""".strip()


def THUMBNAIL_PROMPT(topic: str) -> str:
    """Return the thumbnail-text prompt for a given topic."""
    cleaned_topic = _normalize_topic(topic)
    return f"""
You are an expert short-form video creative strategist.

Generate one thumbnail text overlay for this topic: "{cleaned_topic}"

Requirements:
- Keep it punchy
- Maximum 6 words
- Make it attention-grabbing
- Return plain text only
- Do not include quotation marks
""".strip()
