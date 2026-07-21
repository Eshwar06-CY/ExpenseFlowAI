# ExpenseFlow AI — Production Deployment Guide

This document covers Docker-based container deployments and system preparation checklist items.

---

## 🚀 Quickstart: Docker Compose Deployment

The fastest way to deploy the entire stack is by using the multi-container configuration defined in the root folder.

### 1. Configure the Environment
Copy the env template to `.env` and configure credentials:
```bash
cp .env.example .env
```
Ensure you change the `JWT_SECRET` and set secure passwords for `MYSQL_ROOT_PASSWORD` and `MYSQL_PASSWORD`.

### 2. Build & Launch Containers
Compile backend wheels and Vite bundle chunks, and launch Nginx, FastAPI, and MySQL in detached mode:
```bash
docker-compose up -d --build
```

### 3. Apply Database Migrations
Run Alembic migrations to construct the database schemas:
```bash
docker-compose exec backend alembic upgrade head
```

---

## 🩺 Monitoring & Diagnostics

### Health Check Endpoint
- **API Endpoint:** `/api/v1/health`
- **Output Schema:**
  ```json
  {
    "status": "healthy",
    "service": "expenseflow-backend",
    "version": "1.0.0",
    "database": "healthy",
    "uptime": "2h 45m 12s"
  }
  ```
Load balancers or external uptime checkers should point to this URL.

### Container Logging
Inspect application logs directly:
```bash
# View backend server logs
docker-compose logs -f backend

# View audit logs containing user interactions
docker-compose logs -f backend | grep AUDIT
```

---

## 🔒 Production Hardening Checklist

1. [ ] **JWT Key Rotation:** Set `JWT_SECRET` in environment parameters to a strong random 256-bit key. Never use the development default key in public servers.
2. [ ] **Nginx SSL:** Update `frontend/nginx.conf` or configure a reverse proxy (e.g. Traefik, AWS ALB) to manage TLS/SSL termination.
3. [ ] **CORS Restrictions:** Set `CORS_ORIGINS` to your app's explicit domain name, instead of leaving defaults active.
4. [ ] **Database Backups:** Configure cron jobs to back up the MySQL volume `/var/lib/mysql` regularly.
