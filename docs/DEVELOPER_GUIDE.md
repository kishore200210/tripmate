# Developer Guide

Welcome to the TripMate development team! This guide covers setting up your local environment outside of Docker, running tests, and debugging.

## 🛠️ Local Environment Setup (Manual)

If you need to run the services bare-metal for debugging purposes, follow these steps.

### Backend Setup
We use `poetry` or Python `venv` for dependency management.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the FastAPI Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

*Note: You must have local instances of PostgreSQL and Redis running on their default ports, or override the URLs in your `backend/.env` file.*

### Frontend Setup
We use `npm` for Node.js package management.

```bash
cd frontend
npm install

# Start the Next.js Dev Server
npm run dev
```
The frontend will be available at `http://localhost:3000`.

## 🧪 Testing

We strictly enforce a test-driven approach.

### Running Backend Tests (Pytest)
```bash
cd backend
source venv/bin/activate
pytest tests/
```

### Running Frontend Unit Tests (Jest)
```bash
cd frontend
npm run test
```

### Running E2E Tests (Playwright)
```bash
cd frontend
npx playwright test
```
*Playwright will automatically boot up the Next.js dev server on a localized port before executing the browser automation.*

## 👁️ Observability & Debugging

- **Sentry**: To test Sentry locally, ensure `SENTRY_DSN` is set in your `.env`. Throw a manual `raise Exception("test")` in a route to verify the stack trace appears in your Sentry dashboard.
- **Logfire**: Pydantic Logfire provides rich, structural logs in the terminal. If `LOGFIRE_TOKEN` is set, traces are also sent to your Logfire web UI.
- **Metrics**: Visit `http://localhost:8000/metrics` to see the raw Prometheus scrape data.
