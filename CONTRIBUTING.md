# Contributing to Food-Aid Connect

## Branch naming

Create a separate branch for each task.

Use:

feature/<JIRA-key>-short-description

For bug fixes:

fix/<JIRA-key>-short-description

Examples:

feature/FAC-19-github-setup
feature/FAC-20-flask-skeleton

## Commit messages

Use short and meaningful commit messages.

Format:

<type>: <short description>

Examples:

feat: add batch creation endpoint
fix: validate batch expiry date
docs: update README
test: add reservation tests

## Pull requests

- Create a pull request for changes to main.
- Include the Jira issue key.
- Explain what changed.
- Explain what was tested.
- Request at least one review.
- Make sure CI checks pass before merging.

## General rules

- Keep commits focused.
- Do not commit passwords, API keys, .env files or other secrets.
- Follow the existing project structure.
- Keep documentation updated when necessary.
