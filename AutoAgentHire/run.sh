#!/bin/bash

# AutoAgentHire Application Startup Script

echo "🚀 Starting AutoAgentHire Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and credentials"
    echo "🛑 Exiting. Please configure .env file and run again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads
mkdir -p templates
mkdir -p logs

# Check if Chrome is installed (for Selenium)
if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    echo "⚠️  Chrome/Chromium not found. Installing..."
    
    # Install Chrome on Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y wget gnupg
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable
    fi
fi

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium

# Create default cover letter template if it doesn't exist
if [ ! -f "templates/cover_letter.txt" ]; then
    echo "📄 Creating default cover letter template..."
    cat > templates/cover_letter.txt << 'EOL'
Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With my background in {relevant_skills} and {years_experience} years of experience in {field}, I am confident that I would be a valuable addition to your team.

In my previous roles, I have:
{key_achievements}

I am particularly drawn to this opportunity because:
{why_interested}

I am excited about the possibility of contributing to {company_name}'s continued success and would welcome the opportunity to discuss how my skills and experience align with your needs.

Thank you for your time and consideration.

Sincerely,
{candidate_name}
EOL
fi

# Check environment variables
echo "🔍 Checking configuration..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['OPENAI_API_KEY', 'LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD']
missing_vars = []

for var in required_vars:
    if not os.getenv(var) or os.getenv(var) == f'your_{var.lower()}_here':
        missing_vars.append(var)

if missing_vars:
    print(f'⚠️  Missing required environment variables: {missing_vars}')
    print('📝 Please update your .env file with valid values')
    exit(1)
else:
    print('✅ Configuration looks good!')
"

if [ $? -ne 0 ]; then
    echo "🛑 Configuration check failed. Please fix .env file."
    exit 1
fi

# Start the application
echo "🌟 Starting AutoAgentHire API server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔄 To stop the server, press Ctrl+C"
echo ""

# Run the FastAPI application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload