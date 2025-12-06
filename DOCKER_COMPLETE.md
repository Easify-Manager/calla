# ✅ Docker Setup Complete!

## What Was Created

### Docker Configuration Files
- ✅ `docker-compose.yml` - Orchestrates all 3 services
- ✅ `backend/Dockerfile` - Backend container image
- ✅ `frontend/Dockerfile` - Frontend container image (multi-stage)
- ✅ `backend/.dockerignore` - Excludes unnecessary files
- ✅ `frontend/.dockerignore` - Excludes unnecessary files

### Environment Configuration
- ✅ `.env` - Root environment variables (with your Gemini key)
- ✅ `.env.example` - Template for new deployments
- ✅ `frontend/next.config.ts` - Updated for standalone Docker build

### Documentation
- ✅ `DOCKER_SETUP.md` - Complete Docker guide
- ✅ `README.md` - Main project documentation
- ✅ `start.sh` - Quick start script

## 🚀 How to Run

### Option 1: Docker Compose (Recommended)
```bash
docker compose up -d
```

### Option 2: Start Script
```bash
./start.sh
```

### Option 3: Manual
```bash
# 1. Ensure .env has GEMINI_API_KEY
# 2. Start services
docker compose up -d

# 3. Check status
docker compose ps

# 4. View logs
docker compose logs -f
```

## 📊 Services Overview

| Service | Container | Port | URL |
|---------|-----------|------|-----|
| Frontend | `calla_frontend` | 3000 | http://localhost:3000 |
| Backend | `calla_backend` | 8000 | http://localhost:8000 |
| Database | `calla_postgres` | 5432 | localhost:5432 |

## 🎯 Quick Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# View logs (all services)
docker compose logs -f

# View specific service logs
docker compose logs -f backend

# Restart a service
docker compose restart backend

# Rebuild after code changes
docker compose up -d --build

# Check service health
docker compose ps

# Execute command in container
docker compose exec backend bash

# Database access
docker compose exec db psql -U medvoice -d medvoice
```

## 🔧 Configuration Details

### Network
All services communicate on `calla-network`:
- Services can reach each other using container names
- Backend connects to database using `db:5432`
- Frontend calls backend using `http://backend:8000` (internal)

### Volumes
- **postgres_data**: Persists database data
- **./backend:/app**: Backend code (hot reload)
- **./frontend**: Frontend code (production build)

### Health Checks
All services have health checks:
- **Backend**: Checks `/docs` endpoint every 30s
- **Frontend**: Checks root endpoint every 30s
- **Database**: Runs `pg_isready` every 10s

### Environment Variables (Passed to Containers)

**Backend receives:**
```env
DATABASE_URL=postgresql+asyncpg://medvoice:medvoice_secret@db:5432/medvoice
DATABASE_URL_SYNC=postgresql://medvoice:medvoice_secret@db:5432/medvoice
JWT_SECRET=your-secret-key-here
GEMINI_API_KEY=<from .env>
LLM_MODEL=gemini/gemini-2.0-flash
GEMINI_LIVE_MODEL=gemini-2.0-flash-exp
FRONTEND_URL=http://localhost:3000
```

**Frontend receives:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=production
```

## 🔄 Development Workflow

### Making Changes

**Backend (Python):**
1. Edit files in `./backend/`
2. Changes auto-reload (no restart needed)
3. Check logs: `docker compose logs -f backend`

**Frontend (Next.js):**
1. Edit files in `./frontend/`
2. Rebuild: `docker compose up -d --build frontend`
3. Check logs: `docker compose logs -f frontend`

**Database:**
1. Modify `backend/init.sql`
2. Recreate: `docker compose down -v && docker compose up -d`

### Adding Dependencies

**Backend:**
```bash
# Edit backend/requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# Rebuild
docker compose up -d --build backend
```

**Frontend:**
```bash
# Edit frontend/package.json
# Then rebuild
docker compose up -d --build frontend
```

## 📝 Testing the Setup

### 1. Verify Services Are Running
```bash
docker compose ps
```

Expected output:
```
NAME              STATUS
calla_backend     Up (healthy)
calla_frontend    Up (healthy)
calla_postgres    Up (healthy)
```

### 2. Check Logs for Errors
```bash
docker compose logs backend
```

Look for:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Access Frontend
Open http://localhost:3000 in your browser

### 4. Check Backend API
Open http://localhost:8000/docs

### 5. Test Database Connection
```bash
docker compose exec backend python -c "from app.database import engine; print('✅ Database connected')"
```

## 🐛 Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs db
```

**Common issues:**
- Port 3000/8000/5432 already in use
- Missing GEMINI_API_KEY in .env
- Docker daemon not running

### Port Conflicts

**Find what's using the port:**
```bash
sudo lsof -i:8000  # Backend
sudo lsof -i:3000  # Frontend
sudo lsof -i:5432  # Database
```

**Kill the process:**
```bash
sudo kill -9 <PID>
```

### Database Connection Failed

**Verify database is running:**
```bash
docker compose ps db
```

**Check database logs:**
```bash
docker compose logs db
```

**Test connection:**
```bash
docker compose exec db psql -U medvoice -d medvoice -c "SELECT 1"
```

### Backend Hot Reload Not Working

**Restart backend:**
```bash
docker compose restart backend
```

**Check volume mount:**
```bash
docker compose exec backend ls -la /app
```

### Frontend Build Fails

**Check build logs:**
```bash
docker compose logs frontend
```

**Rebuild from scratch:**
```bash
docker compose down
docker compose build --no-cache frontend
docker compose up -d
```

## 🔐 Production Considerations

### Security
- [ ] Change `JWT_SECRET` to a strong random value
- [ ] Use environment-specific `.env` files
- [ ] Don't commit `.env` to git (.gitignore included)
- [ ] Enable HTTPS (add Nginx/Traefik)
- [ ] Restrict database to internal network only

### Performance
- [ ] Set resource limits in docker-compose.yml
- [ ] Use production database (not Docker for large scale)
- [ ] Enable caching
- [ ] Configure CDN for frontend

### Monitoring
- [ ] Set up log aggregation (ELK, Loki)
- [ ] Configure metrics (Prometheus)
- [ ] Set up alerts
- [ ] Health check monitoring

### Backup
```bash
# Backup database
docker compose exec db pg_dump -U medvoice medvoice > backup.sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U medvoice -d medvoice
```

## 📚 Additional Documentation

- **Docker Setup**: [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Detailed Docker guide
- **Manual Setup**: [QUICKSTART.md](./QUICKSTART.md) - Non-Docker setup
- **Backend**: [backend/README.md](./backend/README.md) - Backend details
- **Frontend**: [frontend/README.md](./frontend/README.md) - Frontend details
- **Patient App**: [patient_app/README.md](./patient_app/README.md) - Mobile app

## 🎉 Next Steps

1. **Start the platform:**
   ```bash
   docker compose up -d
   ```

2. **Access frontend:**
   Open http://localhost:3000

3. **Register as caregiver:**
   Create your account

4. **Add a patient:**
   Use the dashboard

5. **Setup patient mobile app:**
   See `patient_app/README.md`

6. **Test voice call:**
   Trigger a call from the dashboard

---

**Everything is now containerized and ready to run with a single command!** 🚀
