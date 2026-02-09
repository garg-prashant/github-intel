"""LLM prompt templates for the 5 content types per repo."""

PROMPT_VERSION = "v1"

SYSTEM = """You are an expert technical writer. Write clear, concise markdown. Use code blocks with language tags when showing code. Be accurate and avoid fluff."""

WHAT_AND_WHY = """Repository: {full_name}
Description: {description}
Primary language: {primary_language}
Topics: {topics}
README excerpt (first 2000 chars): 
---
{readme_excerpt}
---

Write a short section "What and why" (about 150-250 words):
1. What this project is and what problem it solves.
2. Why it might be trending now.
3. When to use it (and when not to). Use markdown."""

QUICK_START = """Repository: {full_name}
Description: {description}
Primary language: {primary_language}
README excerpt:
---
{readme_excerpt}
---

Write a "Quick start" section (about 200-350 words) that a developer can follow in 10-15 minutes:
1. Installation (exact commands where possible).
2. Minimal runnable example (code block).
3. One realistic next step (e.g. config, first API call). Use markdown and code blocks with language tags."""

MENTAL_MODEL = """Repository: {full_name}
Description: {description}
README excerpt:
---
{readme_excerpt}
---

Write a "Mental model" section (about 150-250 words):
1. Core abstractions (main concepts and how they relate).
2. Data/control flow in one sentence each.
3. Where this fits in the ecosystem (similar tools, typical stack). Use markdown."""

PRACTICAL_RECIPE = """Repository: {full_name}
Description: {description}
Primary language: {primary_language}
README excerpt:
---
{readme_excerpt}
---

Write a "Practical recipe" section (about 200-300 words):
1. One concrete integration example (e.g. with FastAPI, or a DB).
2. Common mistakes or pitfalls to avoid.
3. Brief note on performance or security if relevant. Use markdown and code blocks."""

LEARNING_PATH = """Repository: {full_name}
Description: {description}
Topics: {topics}
README excerpt:
---
{readme_excerpt}
---

Write a "Learning path" section (about 150-250 words):
1. Prerequisites (skills or concepts to know first).
2. Related projects or topics to explore.
3. Suggested next steps after mastering basics. Use markdown."""

CONTENT_PROMPTS = {
    "what_and_why": WHAT_AND_WHY,
    "quick_start": QUICK_START,
    "mental_model": MENTAL_MODEL,
    "practical_recipe": PRACTICAL_RECIPE,
    "learning_path": LEARNING_PATH,
}
