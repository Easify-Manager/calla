#!/bin/bash
set -e

echo "🚀 Setting up Calla Voice Platform..."

# Step 1: Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3.12-venv postgresql-client

# Step 2: Create virtual environment
echo "🐍 Creating Python virtual environment..."
cd backend
python3 -m venv venv

# Step 3: Install Python packages
echo "📚 Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Apply database migration
echo "💾 Applying database migration..."
if command -v psql &> /dev/null; then
    PGPASSWORD=1234 psql -h localhost -U postgres -d medvoice -f add_last_attempt_time_migration.sql || echo "⚠️  Migration might already be applied"
else
    echo "⚠️  PostgreSQL client not found. Please run migration manually:"
    echo "   psql -U postgres -d medvoice -f backend/add_last_attempt_time_migration.sql"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start ngrok:     ngrok http 8000"
echo "2. Update .env:     FRONTEND_URL with your ngrok URL"
echo "3. Start backend:   cd backend && source venv/bin/activate && python run.py"
echo ""
echo "🎉 Then test by adding a patient and medication!"
