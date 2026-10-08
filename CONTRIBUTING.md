# 🤝 Contributing to BizInsight AI

Thank you for your interest in contributing to **BizInsight AI**! With 24+ forks and growing community interest, we want to make collaboration as smooth as possible. This guide covers everything you need to get started.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Branch Naming Conventions](#branch-naming-conventions)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Issue Reporting](#issue-reporting)
- [Contribution Best Practices](#contribution-best-practices)

---

## 📜 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Be constructive in feedback, patient with new contributors, and collaborative in discussions.

---

## 🚀 Getting Started

### 1. Fork & Clone

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/BizInsight-AI.git
cd BizInsight-AI
```

### 2. Set Up the Upstream Remote

```bash
git remote add upstream https://github.com/Prateekiiitg56/BizInsight-AI.git
git fetch upstream
```

### 3. Run the Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python download_model.py
cp .env.example .env            # set JWT_SECRET; OPENROUTER_API_KEY is optional
uvicorn bizinsight_api.main:app --port 8001 --reload
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### 4. Run the Frontend

```bash
cd frontend
cp .env.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8001
npm install
npm run dev
```

---

## 📂 Project Structure

```
BizInsight-AI/
├── backend/            # FastAPI API, RAG assistant, clustering, tests
├── frontend/           # Next.js web app
├── docs/               # Architecture notes
├── README.md
└── CONTRIBUTING.md     # This file
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit together.

---

## 🌿 Branch Naming Conventions

Always create a new branch from an updated `main`. Use the following prefixes:

| Type | Format | Example |
|------|--------|---------|
| New feature | `feature/<short-description>` | `feature/multi-language-sentiment` |
| Bug fix | `bugfix/<short-description>` | `bugfix/pdf-chart-overlap` |
| Documentation | `docs/<short-description>` | `docs/update-readme` |
| Refactoring | `refactor/<short-description>` | `refactor/database-connection` |
| Testing | `test/<short-description>` | `test/sentiment-analysis-unit` |
| Hotfix (urgent) | `hotfix/<short-description>` | `hotfix/api-key-crash` |

```bash
# Always sync with upstream before branching
git checkout main
git pull upstream main

# Create your branch
git checkout -b feature/your-feature-name
```

---

## ✍️ Commit Message Format

Follow the **Conventional Commits** standard for clear, scannable history.

### Format

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

### Types

| Type | When to Use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, missing semicolons — no logic change |
| `refactor` | Code restructuring without feature/fix |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates |

### Examples

```bash
feat(dashboard): add sentiment trend line chart

fix(database): handle empty review strings on insert

docs(readme): update installation steps for Windows

refactor(clustering): extract category mapping into helper function
```

### Rules

- Use the **imperative mood** in the summary: "add feature" not "added feature"
- Keep the summary under **72 characters**
- Reference related issues in the footer: `Closes #42`

---

## 🔀 Pull Request Process

### Before Submitting

- [ ] Your branch is up to date with `upstream/main`
- [ ] Backend tests pass (`cd backend && python -m pytest -q tests`)
- [ ] Frontend checks pass (`cd frontend && npm run lint && npx tsc --noEmit && npm run build`)
- [ ] Code follows the style guidelines below
- [ ] You have tested your changes manually
- [ ] No sensitive data (API keys, `.env`) is included

### Submitting a PR

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on the **main repository** on GitHub.

3. Fill in the PR template with:
   - **What** this PR does
   - **Why** the change is needed
   - **How** to test it
   - Screenshots (if UI changes are involved)
   - Reference to any related issue: `Closes #<issue-number>`

### PR Review Criteria

- Maintainers aim to review PRs within **3–5 business days**
- At least **1 maintainer approval** is required before merging
- Resolve all review comments before re-requesting a review
- Avoid unnecessary force-pushes to a PR branch after review has started, but rebasing or squashing is permitted to maintain a clean history.

---

## 🎨 Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) conventions
- Use **4 spaces** for indentation (no tabs)
- Maximum line length: **100 characters**
- Use **descriptive variable names** (`sentiment_score` not `s`)

### Functions & Modules

- Every function must have a **docstring** explaining its purpose, parameters, and return value:
  ```python
  def get_sentiment(text: str) -> float:
      """
      Compute the sentiment polarity of a given text string.

      Args:
          text (str): Customer review text.

      Returns:
          float: Polarity score between -1.0 (negative) and 1.0 (positive).
      """
      return vader_analyzer.polarity_scores(text)["compound"]
  ```

- Keep functions **focused** — one responsibility per function
- Avoid deeply nested logic; extract helpers where possible

### Imports

- Group imports in this order, separated by a blank line:
  1. Standard library (`os`, `tempfile`)
  2. Third-party (`fastapi`, `pandas`)
  3. Local modules (`database`, `bizinsight_api`)

### Frontend

- TypeScript everywhere; add response types to `frontend/src/lib/types.ts`
- Call the backend only through `frontend/src/lib/api-client.ts`
- Reuse the shared styles in `globals.css` (`.card`, `.btn-primary`, `.input`, …) and components in `src/components`

### Security

- **Never hardcode API keys** — always use environment variables (`.env`)
- **Never commit** `.env`, `bizinsight.db`, or any file with credentials
- Validate all user inputs before writing to the database

---

## 🧪 Testing Requirements

The backend has a pytest suite in `backend/tests` that CI runs on every pull request — add tests for any backend change. Also verify the following manually for UI changes:

### Manual Checklist

| Area | Test Case |
|------|-----------|
| **Data Upload** | Upload `reviews.csv` — confirm rows appear in the dashboard |
| **Sentiment** | Verify positive/negative counts update correctly |
| **Empty Input** | Upload a CSV with blank reviews — confirm graceful error handling |
| **Export** | Click "Export CSV" on the dashboard — confirm the download contains your reviews |
| **AI Assistant** | Enter a question — confirm a valid AI response is returned |
| **Clear Data** | Click "Delete all" on the upload page — confirm data is removed |
| **Edge Cases** | Upload a CSV missing the `review` column — confirm error message displays |

### CSV Format for Testing

```
review
"Great service, very happy!"
"Terrible experience, never coming back."
"Average quality, nothing special."
```

> 💡 If you add new features, document the manual test steps in your PR description.

---

## 🐛 Issue Reporting

### Before Opening an Issue

- Search [existing issues](https://github.com/Prateekiiitg56/BizInsight-AI/issues) to avoid duplicates
- Try to reproduce the issue on a fresh clone with a clean environment

### Bug Report Template

```
**Description**
A clear description of what the bug is.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. Windows 11, Ubuntu 22.04]
- Python version: [e.g. 3.10.5]
- Browser: [e.g. Chrome 124]

**Screenshots / Logs**
If applicable, add screenshots or paste error logs.
```

### Feature Request Template

```
**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
Describe the feature you'd like to see.

**Alternatives Considered**
Any other approaches you've thought about.

**Additional Context**
Any mockups, examples, or references.
```

### Issue Labels

| Label | Meaning |
|-------|---------|
| `bug` | Something isn't working |
| `enhancement` | New feature request |
| `documentation` | Docs improvement needed |
| `good first issue` | Great for new contributors |
| `help wanted` | Maintainers need community input |

---

## ✅ Contribution Best Practices

- **Start small.** First-time contributors should look for issues tagged `good first issue`.
- **Communicate early.** Comment on an issue before starting work to avoid duplicate effort.
- **Keep PRs focused.** One feature or fix per PR — do not bundle unrelated changes.
- **Write self-documenting code.** Clear names and structure reduce the need for comments.
- **Respect existing patterns.** Match the style and structure of the surrounding code.
- **Update the README** if your change affects setup, usage, or project structure.
- **Be responsive.** If a maintainer requests changes, try to respond within a week.

---

## 🙋 Need Help?

If you have questions about contributing:

- Open a [GitHub Discussion](https://github.com/Prateekiiitg56/BizInsight-AI/discussions)
- Or tag `@Prateekiiitg56` in a relevant issue

---

*Thank you for helping make BizInsight AI better for everyone! 🚀*
