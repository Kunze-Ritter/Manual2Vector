# KRAI Chat Agent - n8n Startup Script
# PowerShell Script zum Starten des Chat Agents

Write-Host "🤖 KRAI Chat Agent - n8n Startup" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if Docker is running
Write-Host "`n🔍 Checking Docker status..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not running!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and start it first." -ForegroundColor Red
    exit 1
}

# Check if docker-compose exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path "backend/.env")) {
    Write-Host "⚠️  backend/.env not found!" -ForegroundColor Yellow
    Write-Host "Please copy backend/env.example to backend/.env and configure it." -ForegroundColor Yellow
    Write-Host "Required variables:" -ForegroundColor Yellow
    Write-Host "  - SUPABASE_URL" -ForegroundColor Yellow
    Write-Host "  - SUPABASE_KEY" -ForegroundColor Yellow
    Write-Host "  - R2_ACCOUNT_ID" -ForegroundColor Yellow
    Write-Host "  - R2_ACCESS_KEY_ID" -ForegroundColor Yellow
    Write-Host "  - R2_SECRET_ACCESS_KEY" -ForegroundColor Yellow
}

# Start n8n with docker-compose
Write-Host "`n🚀 Starting KRAI Chat Agent (n8n)..." -ForegroundColor Yellow
Write-Host "This will start n8n in Docker container..." -ForegroundColor Yellow

try {
    docker-compose up -d
    Write-Host "✅ n8n started successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start n8n!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Wait a moment for n8n to start
Write-Host "`n⏳ Waiting for n8n to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if n8n is running
Write-Host "`n🔍 Checking n8n status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ n8n is running and accessible!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  n8n is starting but not yet ready..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  n8n is still starting up..." -ForegroundColor Yellow
}

# Display access information
Write-Host "`n🎉 KRAI Chat Agent is ready!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "📱 n8n Web Interface:" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:5678" -ForegroundColor White
Write-Host "   Login: admin" -ForegroundColor White
Write-Host "   Password: krai_chat_agent_2024" -ForegroundColor White

Write-Host "`n🔗 Chat Agent Webhook:" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:5678/webhook/chat" -ForegroundColor White
Write-Host "   Method: POST" -ForegroundColor White
Write-Host "   Content-Type: application/json" -ForegroundColor White

Write-Host "`n📋 Available Commands:" -ForegroundColor Cyan
Write-Host "   /status - System status check" -ForegroundColor White
Write-Host "   /search [text] - Search documents" -ForegroundColor White
Write-Host "   /models [name] - Search models" -ForegroundColor White
Write-Host "   /help - Show help" -ForegroundColor White

Write-Host "`n🧪 Test Command:" -ForegroundColor Cyan
Write-Host "   curl -X POST http://localhost:5678/webhook/chat -H 'Content-Type: application/json' -d '{\"message\": \"/status\"}'" -ForegroundColor White

Write-Host "`n📚 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:5678 in your browser" -ForegroundColor White
Write-Host "2. Login with admin/krai_chat_agent_2024" -ForegroundColor White
Write-Host "3. Import the workflow from n8n_workflows/krai-chat-agent.json" -ForegroundColor White
Write-Host "4. Configure Supabase credentials" -ForegroundColor White
Write-Host "5. Activate the workflow" -ForegroundColor White
Write-Host "6. Test with the curl command above" -ForegroundColor White

Write-Host "`n🛑 To stop the Chat Agent:" -ForegroundColor Yellow
Write-Host "   docker-compose down" -ForegroundColor White

Write-Host "`n📖 For detailed setup instructions, see:" -ForegroundColor Cyan
Write-Host "   N8N_CHAT_AGENT_SETUP.md" -ForegroundColor White

Write-Host "`n🎯 Happy chatting with your KRAI Engine! 🤖" -ForegroundColor Green
