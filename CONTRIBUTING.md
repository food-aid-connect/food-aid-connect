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

<type>(FAC-XX): <short description>

The Jira key (FAC-XX) is mandatory: it links the commit to the Jira ticket.

Examples:

feat(FAC-41): add batch creation endpoint
fix(FAC-41): validate batch expiry date
docs(FAC-19): update README
test(FAC-48): add reservation tests

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
