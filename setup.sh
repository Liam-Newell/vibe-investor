#!/bin/bash
# Vibe Investor - Easy Setup Script
# This script will get you up and running in under 5 minutes

set -e  # Exit on any error

echo "🚀 Vibe Investor Setup Script"
echo "==============================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p data logs config backups database/init monitoring backup caddy
echo "✅ Directories created"
echo ""

# Copy environment template
echo "⚙️  Setting up configuration..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ Configuration template created (.env)"
    echo "📝 Please edit .env file with your API keys and settings"
else
    echo "ℹ️  .env file already exists, skipping template copy"
fi
echo ""

# Generate secure passwords
echo "🔐 Generating secure passwords..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Update .env with generated passwords (if they're still the default)
if grep -q "secure_database_password_change_this" .env; then
    sed -i.bak "s/secure_database_password_change_this/$DB_PASSWORD/" .env
    echo "✅ Database password generated"
fi

if grep -q "secure_redis_password_change_this" .env; then
    sed -i.bak "s/secure_redis_password_change_this/$REDIS_PASSWORD/" .env
    echo "✅ Redis password generated"
fi
echo ""

# Create basic Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo "🐳 Creating basic Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 trader && chown -R trader:trader /app
USER trader

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "main.py"]
EOF
    echo "✅ Basic Dockerfile created"
fi

# Create basic requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo "📦 Creating basic requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core application
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
python-multipart==0.0.6

# Trading & Financial
anthropic==0.7.8
ib_insync==0.9.86
yfinance==0.2.18
pandas==2.1.4
numpy==1.25.2
ta-lib==0.4.28

# Scheduling & Background Tasks
apscheduler==3.10.4
celery==5.3.4

# Utilities
httpx==0.25.2
python-dotenv==1.0.0
loguru==0.7.2
typer==0.9.0

# Email
aiosmtplib==3.0.1
jinja2==3.1.2

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
EOF
    echo "✅ Basic requirements.txt created"
fi

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo ""
echo "1. Edit your configuration:"
echo "   nano .env"
echo ""
echo "2. Add your API keys (required):"
echo "   - CLAUDE_API_KEY=your_actual_claude_key"
echo "   - IBKR or Questtrade credentials"
echo ""
echo "3. Start the system:"
echo "   docker-compose up -d"
echo ""
echo "4. Access the dashboard:"
echo "   http://localhost:8080"
echo ""
echo "5. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "⚠️  IMPORTANT: System starts in PAPER TRADING mode by default!"
echo "   Only switch to live trading after 60+ days of successful paper trading."
echo ""

# Check if API keys are configured
echo "🔍 Configuration check:"
if grep -q "your_claude_api_key_here" .env; then
    echo "❌ Claude API key not configured - please add your key to .env"
else
    echo "✅ Claude API key appears to be configured"
fi

if grep -q "your-email@gmail.com" .env; then
    echo "❌ Email settings not configured - please update email settings in .env"
else
    echo "✅ Email settings appear to be configured"
fi

echo ""
echo "📚 For more information, see README.md"
echo "🐛 For issues, check the logs: docker-compose logs"
echo ""
echo "Happy trading! 📈" 