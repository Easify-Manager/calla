# 🚀 Quick Start - 5 Minutes to First Call!

Your Twilio credentials are already configured! Here's what to do:

## ✅ Twilio Configuration (DONE!)
```
Account SID: AC1ed80c3e7bcb0c8dc18dfa4d873a08c2
Phone Number: +1 (616) 219-8901
Status: ✅ Configured in backend/.env
```

## 📋 Step-by-Step Setup

### 1. Run Setup Script (One Time)
```bash
cd /home/then/calla
./setup.sh
```

This will:
- Install system dependencies (python3-venv, postgresql-client)
- Create Python virtual environment
- Install all required packages (including twilio)
- Apply database migration

### 2. Start ngrok (Required for Local Testing)

In a **new terminal**:
```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

**Copy that ngrok URL!** (e.g., `https://abc123.ngrok.io`)

### 3. Update Backend URL

Edit `backend/.env` and update:
```bash
FRONTEND_URL=https://abc123.ngrok.io
```
(Replace with your actual ngrok URL)

### 4. Start Backend

In a **new terminal**:
```bash
cd /home/then/calla/backend
source venv/bin/activate
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Scheduler started with Twilio voice call reminder jobs
```

### 5. Test the System!

#### Option A: Using the Web Dashboard

1. Open browser: http://localhost:3000
2. Create a caregiver account
3. Login
4. Add a patient with **your phone number**
5. Add a medication scheduled for **2 minutes from now**
6. Wait for the call!

#### Option B: Using curl (Quick Test)

```bash
# 1. Register caregiver
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "full_name": "Test Caregiver",
    "phone_number": "+1234567890"
  }'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }' | jq -r '.access_token')

# 3. Add patient
PATIENT_ID=$(curl -X POST http://localhost:8000/api/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test Patient",
    "phone_number": "+1YOUR_PHONE_NUMBER"
  }' | jq -r '.id')

# 4. Add medication (scheduled for 2 minutes from now)
# Calculate time: current time + 2 minutes
TIME=$(date -u -d '+2 minutes' '+%H:%M')

curl -X POST http://localhost:8000/api/medications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"$PATIENT_ID\",
    \"drug_name\": \"Test Medication\",
    \"dosage\": \"10mg\",
    \"specific_times\": [\"$TIME\"],
    \"is_active\": true
  }"

# 5. Wait for call in ~2 minutes!
```

## 📞 What to Expect

When the call comes:

1. **Phone rings** - Answer it!
2. **You hear:** "Hello [your name]"
3. **Then Gemini says:** "It's time to take your Test Medication, 10mg. Have you taken it yet?"
4. **You say (naturally):**
   - "Yes, I took it"
   - "Already did"
   - "Of course"
   - Or "Not yet" (will retry in 3 min)

5. **Gemini responds:** "Wonderful! Thank you for taking care of yourself!"
6. **Call ends**
7. **Check database** - Reminder marked as "confirmed"!

## 🎤 Natural Language Examples

You can speak naturally! Try:
- ✅ "Yes"
- ✅ "I took it"
- ✅ "Already did"
- ✅ "Of course"
- ✅ "Just took it now"
- ❌ "Not yet" (triggers retry)
- ❌ "I need more time" (triggers retry)
- ❓ "Who is this?" (Gemini explains)

## 🐛 Troubleshooting

### "No calls coming"
```bash
# Check scheduler is running
docker logs calla_backend | grep "Scheduler started"

# Check reminders were created
docker exec -it calla_postgres psql -U postgres -d medvoice -c "SELECT * FROM scheduled_reminders ORDER BY created_at DESC LIMIT 5;"
```

### "Call connects but silent"
```bash
# Check Gemini API key is valid
echo $GEMINI_API_KEY

# Check WebSocket connection
docker logs calla_backend | grep "Twilio stream started"
```

### "Backend won't start"
```bash
# Make sure database is running
docker-compose up -d db

# Check database connection
PGPASSWORD=1234 psql -h localhost -U postgres -d medvoice -c "SELECT 1;"
```

## 📊 Monitoring

Watch backend logs in real-time:
```bash
cd backend
source venv/bin/activate
python run.py
```

You'll see:
```
INFO: Triggered Twilio call abc123 for reminder def456
INFO: Twilio stream started: MZ789...
INFO: Gemini: Hello Mary, it's time to take your Lisinopril...
INFO: Patient confirmed medication for reminder def456
```

## 🎯 Success Checklist

- [ ] Setup script ran successfully
- [ ] ngrok is running and URL is copied
- [ ] Backend `.env` updated with ngrok URL
- [ ] Backend started without errors
- [ ] Patient added with real phone number
- [ ] Medication scheduled for near future
- [ ] Call received and answered
- [ ] Natural conversation with Gemini worked
- [ ] Confirmation logged in database

## 🚀 You're Done!

Once you receive a call and have a conversation with Gemini, your system is fully working!

### What Happens Next?

1. **Automatic retries** - If patient doesn't answer, system retries after 3 minutes
2. **Up to 3 attempts** - Each with 3-minute intervals
3. **Caregiver alerting** - After 3 failed attempts, caregiver gets a call
4. **Daily reminders** - System auto-generates reminders at midnight

---

**Need Help?** Check:
- `IMPLEMENTATION_COMPLETE.md` - Full guide
- `NATURAL_LANGUAGE_GUIDE.md` - Technical details
- Backend logs for errors
- Twilio console logs: https://console.twilio.com/logs
