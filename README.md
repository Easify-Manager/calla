# Calla - Voice-First Medication Adherence Platform

Complete platform for caregiver-managed medication reminders with AI-powered voice calls using Gemini 2.0 Flash Live.

## 🚀 Quick Start (Docker - Recommended)

### 1. Prerequisites
- Docker & Docker Compose
- Gemini API key from https://aistudio.google.com/

### 2. Setup Environment
```bash
# Edit .env and add your Gemini API key
nano .env
```

Add your API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Start Everything
```bash
docker compose up -d
```

That's it! The platform is now running:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. View Logs
```bash
docker compose logs -f
```

### 5. Stop Services
```bash
docker compose down
```

## 📁 Project Structure

```
calla/
├── backend/           # FastAPI backend
├── frontend/          # Next.js caregiver dashboard
├── patient_app/       # Flutter mobile app
├── docker-compose.yml # Docker orchestration
└── .env              # Environment configuration
```

## 📚 Documentation

- **Docker Setup**: [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Complete Docker guide
- **Quick Start**: [QUICKSTART.md](./QUICKSTART.md) - Manual setup guide
- **Backend**: [backend/README.md](./backend/README.md)
- **Frontend**: [frontend/README.md](./frontend/README.md)
- **Patient App**: [patient_app/README.md](./patient_app/README.md)

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Caregiver Web  │     │                 │     │                 │
│    Dashboard    │────▶│   Backend API   │────▶│  Gemini Live    │
│  (Next.js)      │     │   (FastAPI)     │◀────│     API         │
└─────────────────┘     │                 │     │                 │
                        │   PostgreSQL    │     │    LiteLLM      │
┌─────────────────┐     │                 │     │                 │
│   Patient App   │◀───▶│   WebSocket     │     │                 │
│   (Flutter)     │     └─────────────────┘     └─────────────────┘
└─────────────────┘
```

## 🎯 Features

### Caregiver Dashboard
- ✅ Patient management
- ✅ Medication scheduling
- ✅ Call history & transcripts
- ✅ Adherence tracking
- ✅ AI-powered prescription parsing

### Patient Mobile App
- ✅ Voice-first interaction (no app learning curve)
- ✅ Native incoming call UI (CallKit)
- ✅ Real-time voice with Gemini Live
- ✅ Live transcripts
- ✅ Push notifications

### Voice AI
- ✅ Natural conversation with Gemini 2.0 Flash Live
- ✅ Real-time audio streaming
- ✅ Context-aware responses
- ✅ Medication confirmation
- ✅ Side effect reporting

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL
- WebSocket (voice streaming)
- Gemini 2.0 Flash Live
- LiteLLM

**Frontend:**
- Next.js 15
- React
- TypeScript
- TailwindCSS

**Patient App:**
- Flutter
- Firebase Cloud Messaging
- CallKit (iOS)
- WebSocket audio streaming

## 🔧 Development

### With Docker (Recommended)
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build
```

### Manual Setup
See [QUICKSTART.md](./QUICKSTART.md) for manual setup instructions.

## 🧪 Testing

### Test the Complete Flow

1. **Access Frontend**: http://localhost:3000
2. **Register** as a caregiver
3. **Add a patient** with phone number
4. **Create medication** schedule
5. **Run patient app** on mobile device
6. **Trigger call** from dashboard
7. **Answer call** on patient app
8. **Test voice** conversation

## 📱 Patient App Setup

The Flutter patient app requires additional setup:

```bash
cd patient_app
flutter pub get
flutter run
```

See [patient_app/README.md](./patient_app/README.md) for detailed instructions.

## 🔐 Environment Variables

### Required
- `GEMINI_API_KEY` - Gemini API key (get from https://aistudio.google.com/)

### Optional
- `JWT_SECRET` - Authentication secret (default provided)
- `FIREBASE_CREDENTIALS_PATH` - Firebase config for push notifications

## 📊 Database

PostgreSQL database is automatically created and initialized by Docker.

**Access database:**
```bash
docker compose exec db psql -U medvoice -d medvoice
```

**Backup:**
```bash
docker compose exec db pg_dump -U medvoice medvoice > backup.sql
```

## 🚨 Troubleshooting

**Services won't start:**
```bash
docker compose logs -f
```

**Port conflicts:**
```bash
# Stop services using ports 3000, 8000, or 5432
docker compose down
```

**Reset everything:**
```bash
docker compose down -v
docker compose up -d
```

## 📈 Monitoring

**Check service health:**
```bash
docker compose ps
```

**View resource usage:**
```bash
docker stats
```

**Stream logs:**
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

Proprietary - Calla Health

## 🆘 Support

- **Documentation**: See `/docs` folder
- **Issues**: File a GitHub issue
- **Logs**: `docker compose logs -f`

---

**Built with ❤️ using Gemini 2.0 Flash Live**
