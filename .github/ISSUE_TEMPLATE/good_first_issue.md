---
name: Good First Issue
about: A well-scoped task for first-time or beginner contributors.
title: "[GOOD FIRST ISSUE] - <Brief Description>"
assignees: ''
---

## What Needs to Be Done
<!-- Provide a clear description of the exact task. -->
Clear description of the task.

## Why This Matters
<!-- Explain how this fits into the system. -->
How this fits into the larger system or improves the dashboard/analytics user experience.

## Files to Look At
<!-- Point the contributor to the exact files or directories relevant to this project. -->
- `app.py` / `auth.py` — Core Streamlit dashboard and registration application files
- `rag_api/` — FastAPI system, embeddings configurations, and ChromaDB vector store logic
- `clustering/` — Text preprocessing, sentence-transformers vectorization, and cluster visualization routes
- `database.py` — SQLite models and cross-session persistence

## Acceptance Criteria
<!-- What must be completed for this issue to be closed? -->
- [ ] Feature or fix works exactly as intended without breaking dashboard interactivity or RAG retrieval workflows.
- [ ] The code follows clean standards, uses safe exception handling, and includes docstrings where appropriate.
- [ ] Code changes are verified, tested locally, and are ready to be linked to an incoming PR.

## Tech Context
<!-- Any relevant background: which API endpoints to hit, UI files to modify, or dependencies to track. -->
Any relevant background about the BizInsight-AI architecture (Streamlit UI layout, SQLite tables, or OpenRouter LLM parsing) that will help a beginner get started quickly.

## Mentorship
Comment on this issue with your interest and it will be assigned to you according to GSSoC guidelines. The maintainer will guide you through your first PR.
