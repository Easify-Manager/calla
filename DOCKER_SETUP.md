# Docker Setup Guide - Calla Platform

## Quick Start (Recommended)

Run the entire Calla platform with a single command:

```bash
docker compose up -d
```

That's it! All services will start:
- ✅ PostgreSQL database
- ✅ FastAPI backend
- ✅ Next.js frontend

## Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- Gemini API key from https://aistudio.google.com/

## Initial Setup

### 1. Configure Environment Variables

Edit the `.env` file in the project root:

```bash
# Required
GEMINI_API_KEY=your_actual_gemini_api_key

# Optional (defaults provided)
JWT_SECRET=your-secret-key-change-in-production
FIREBASE_CREDENTIALS_PATH=backend/firebase-service-account.json
```

**Get Gemini API Key:**
1. Go to https://aistudio.google.com/
2. Click "Get API Key"
3. Copy your API key
4. Paste it in `.env`

### 2. Start All Services

```bash
docker compose up -d
```

**Services will be available at:**
- Frontend (Next.js): http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### 3. Check Service Status

```bash
docker compose ps
```

Expected output:
```
NAME              IMAGE                 STATUS
calla_backend     calla-backend         Up (healthy)
calla_frontend    calla-frontend        Up (healthy)
calla_postgres    postgres:16-alpine    Up (healthy)
```

### 4. View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

## Service Details

### PostgreSQL Database
- **Container**: `calla_postgres`
- **Port**: 5432
- **Database**: `medvoice`
- **User**: `medvoice`
- **Data**: Persisted in Docker volume `postgres_data`

### Backend (FastAPI)
- **Container**: `calla_backend`
- **Port**: 8000
- **Hot Reload**: Enabled (code changes auto-reload)
- **Health Check**: `/docs` endpoint

### Frontend (Next.js)
- **Container**: `calla_frontend`
- **Port**: 3000
- **Build**: Production optimized
- **Environment**: Production mode

## Common Commands

### Start Services
```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d backend
```

### Stop Services
```bash
# Stop all services
docker compose down

# Stop and remove volumes (⚠️ deletes database data)
docker compose down -v
```

### Restart Services
```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
```

### Rebuild Services
```bash
# Rebuild after code changes
docker compose up -d --build

# Rebuild specific service
docker compose up -d --build backend
```

### View Logs
```bash
# All logs (follow mode)
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Specific service
docker compose logs -f backend
```

### Execute Commands in Containers
```bash
# Backend shell
docker compose exec backend bash

# Database shell
docker compose exec db psql -U medvoice -d medvoice

# Frontend shell
docker compose exec frontend sh
```

## Development Workflow

### 1. Making Code Changes

**Backend Changes:**
- Edit files in `./backend/`
- Changes auto-reload (hot reload enabled)
- No rebuild needed

**Frontend Changes:**
- Edit files in `./frontend/`
- Requires rebuild: `docker compose up -d --build frontend`

**Database Changes:**
- Modify `backend/init.sql`
- Recreate database:
  ```bash
  docker compose down -v
  docker compose up -d
  ```

### 2. Adding Dependencies

**Backend (Python):**
```bash
# Add to backend/requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# Rebuild backend
docker compose up -d --build backend
```

**Frontend (Node.js):**
```bash
# Add to frontend/package.json
# Then rebuild
docker compose up -d --build frontend
```

### 3. Database Management

**Access Database:**
```bash
docker compose exec db psql -U medvoice -d medvoice
```

**Backup Database:**
```bash
docker compose exec db pg_dump -U medvoice medvoice > backup.sql
```

**Restore Database:**
```bash
cat backup.sql | docker compose exec -T db psql -U medvoice -d medvoice
```

**Reset Database:**
```bash
docker compose down -v
docker compose up -d
```

## Environment Variables

### Root `.env` (Docker Compose)
```env
GEMINI_API_KEY=your_key          # Required
JWT_SECRET=your_secret           # Optional
FIREBASE_CREDENTIALS_PATH=path   # Optional
```

### Backend Environment (Set in docker-compose.yml)
- `DATABASE_URL` - Async PostgreSQL connection
- `DATABASE_URL_SYNC` - Sync PostgreSQL connection
- `JWT_SECRET` - Authentication secret
- `GEMINI_API_KEY` - Gemini API key
- `LLM_MODEL` - LiteLLM model name
- `GEMINI_LIVE_MODEL` - Gemini Live model
- `FRONTEND_URL` - Frontend URL for CORS

### Frontend Environment
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NODE_ENV` - Node environment (production)

## Networking

All services are on the `calla-network` bridge network:

**Internal DNS:**
- Backend → `http://backend:8000`
- Frontend → `http://frontend:3000`
- Database → `postgresql://db:5432`

**External Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Database: localhost:5432

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs db
```

**Check status:**
```bash
docker compose ps
```

### Database Connection Issues

**Verify database is healthy:**
```bash
docker compose ps db
```

**Test connection:**
```bash
docker compose exec backend python -c "import asyncpg; print('OK')"
```

### Port Already in Use

**Find and kill process:**
```bash
# Port 8000
sudo lsof -ti:8000 | xargs kill -9

# Port 3000
sudo lsof -ti:3000 | xargs kill -9

# Port 5432
sudo lsof -ti:5432 | xargs kill -9
```

### Backend Not Hot Reloading

**Check volume mount:**
```bash
docker compose exec backend ls -la /app
```

**Restart backend:**
```bash
docker compose restart backend
```

### Frontend Build Fails

**Check Node version:**
```bash
docker compose exec frontend node --version
```

**Rebuild from scratch:**
```bash
docker compose down
docker compose build --no-cache frontend
docker compose up -d
```

### Out of Disk Space

**Clean up Docker:**
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup (⚠️ removes everything)
docker system prune -a --volumes
```

## Production Deployment

### 1. Update Environment Variables

```env
# Use strong secrets in production
JWT_SECRET=<generate-strong-random-secret>
```

### 2. Configure External Database

Update `docker-compose.yml`:
```yaml
backend:
  environment:
    DATABASE_URL: postgresql+asyncpg://user:pass@external-db:5432/db
```

### 3. Use Production Domains

```yaml
frontend:
  environment:
    NEXT_PUBLIC_API_URL: https://api.yourdomain.com

backend:
  environment:
    FRONTEND_URL: https://yourdomain.com
```

### 4. Add HTTPS (Nginx/Traefik)

Example with Nginx reverse proxy:
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### 5. Security Best Practices

- [ ] Use strong secrets
- [ ] Enable HTTPS/SSL
- [ ] Restrict PostgreSQL to internal network
- [ ] Set up firewall rules
- [ ] Regular backups
- [ ] Monitor logs
- [ ] Update dependencies regularly

## Health Checks

All services have health checks:

**Backend:**
- Endpoint: `GET /docs`
- Interval: 30s
- Timeout: 10s

**Frontend:**
- Endpoint: `GET /`
- Interval: 30s
- Timeout: 10s

**Database:**
- Command: `pg_isready`
- Interval: 10s
- Timeout: 5s

## Resource Limits (Optional)

Add to `docker-compose.yml`:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 512M
      reservations:
        memory: 256M
```

## Monitoring

### Check Resource Usage
```bash
docker stats
```

### Service Health
```bash
docker compose ps
docker inspect calla_backend | grep -A10 Health
```

### Container Logs
```bash
# Stream logs
docker compose logs -f --tail=100

# Save logs to file
docker compose logs > logs.txt
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start all services |
| `docker compose down` | Stop all services |
| `docker compose ps` | List services status |
| `docker compose logs -f` | View logs (follow) |
| `docker compose restart` | Restart all services |
| `docker compose up -d --build` | Rebuild and start |
| `docker compose exec backend bash` | Backend shell |
| `docker compose exec db psql -U medvoice` | Database shell |

## Next Steps

After running `docker compose up -d`:

1. **Access Frontend**: http://localhost:3000
2. **Check API**: http://localhost:8000/docs
3. **Create Admin Account**: Register via frontend
4. **Add Patients**: Use caregiver dashboard
5. **Setup Patient App**: See `/patient_app/README.md`

---

**Need Help?**
- View logs: `docker compose logs -f`
- Check status: `docker compose ps`
- Restart services: `docker compose restart`
