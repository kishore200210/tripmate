# Deployment Guide

TripMate is packaged into production-ready Docker containers and orchestrated via Docker Compose.

## 🚢 Single-Node Production Deployment

For deployment to a single VPS (Virtual Private Server) such as an AWS EC2 instance, DigitalOcean Droplet, or Hetzner server:

1. **Provision the Server**: Ensure the server has at least 4GB RAM (required for YOLO11 and PostgreSQL). Install Docker and Docker Compose.
2. **Clone Repository**: Clone the code to the server.
3. **Configure Environment Variables**:
   Create a `.env` file in the `backend/` directory. You **must** change the default `SECRET_KEY` and provide valid `OPENAI_API_KEY` and Cloudinary credentials.
4. **Deploy**:
   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```
5. **Reverse Proxy**: We strongly recommend deploying Nginx or Traefik in front of the `frontend` container (port 3000) to handle SSL/TLS termination.

## 🔄 CI/CD Pipeline (GitHub Actions)

We utilize a robust GitHub Actions pipeline defined in `.github/workflows/ci-cd.yml`.

### Triggers
The pipeline runs on any Pull Request or Push to the `main` branch.

### Stages
1. **Linting**: Runs `flake8` for Python and `eslint` for Next.js.
2. **Backend Testing**: Provisions an ephemeral Postgres/Redis database, installs Python 3.11, and runs `pytest`.
3. **Frontend Testing**: Runs Jest unit tests and Playwright headless browser E2E tests.
4. **Docker Validation**: Dry-runs the multi-stage Docker builds to ensure no dependencies are broken.
5. **Deploy (Mock)**: A deployment script stub that triggers only on the `main` branch after all tests pass.

### Required GitHub Secrets
If you modify the `deploy` step to push to a real server, you will need to add these secrets to your GitHub Repository Settings:
- `DOCKER_USERNAME` / `DOCKER_PASSWORD`
- `SERVER_SSH_KEY`
- `SERVER_HOST`
