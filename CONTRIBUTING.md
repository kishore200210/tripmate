# Contributing to TripMate

First off, thank you for considering contributing to TripMate! It's people like you that make TripMate such a great tool for AI-powered travel planning.

## 1. Branching Strategy

We follow a simplified Git Flow.
- `main`: Production-ready code. Commits here automatically trigger the CI/CD deployment pipeline.
- `feature/*`: For new features (e.g., `feature/add-currency-conversion`).
- `bugfix/*`: For fixing bugs (e.g., `bugfix/fix-pdf-generation`).

## 2. Pull Request Process

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests!
3. Ensure the test suite passes locally (`pytest` and `npm run test`).
4. Ensure your code lints (`flake8` and `npm run lint`).
5. Issue the Pull Request.

Our GitHub Actions CI/CD pipeline will automatically run against your PR. **Your PR will not be merged if the CI pipeline fails.**

## 3. Code Standards

- **Python**: We adhere strictly to PEP8. Use `black` for formatting and `flake8` for linting.
- **TypeScript**: We use strict typings. Avoid `any` types wherever possible. ESLint is configured to catch standard Next.js errors.
- **Commit Messages**: We prefer Conventional Commits format (e.g., `feat: added AI agent memory`, `fix: resolved crashing Redis broker`).
