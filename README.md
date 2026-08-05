# TripMate Platform

An Enterprise AI Full Stack Travel Planning Platform.

## Architecture

TripMate is built on a modular monolith backend architecture (FastAPI) and a Next.js (App Router) frontend, containerized for scalable deployments. 

## Getting Started

1. Set up your environment variables:
   `cp .env.example .env` (Populate required variables).

2. Start the infrastructure (PostgreSQL, Redis):
   `docker-compose up -d`

3. Start Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. Start Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Design

Please see the `architecture_design.md` for a complete breakdown of our clean architecture, engineering principles, and coding standards.
