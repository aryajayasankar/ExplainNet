# Quick Deploy Script
# Run this after setting up Render, Supabase, and Vercel accounts

Write-Host "🚀 ExplainNet Deployment Helper" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (!(Test-Path "backend/main.py")) {
    Write-Host "❌ Please run this script from the ExplainNet-ARUU root directory" -ForegroundColor Red
    exit 1
}

Write-Host "📝 Pre-Deployment Checklist:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. [ ] Created Supabase project and got DATABASE_URL"
Write-Host "2. [ ] Created Render account"
Write-Host "3. [ ] Created Vercel account"
Write-Host "4. [ ] Have all API keys (Google, NewsAPI, Guardian)"
Write-Host "5. [ ] Pushed code to GitHub"
Write-Host ""

$continue = Read-Host "Have you completed all the above steps? (y/n)"
if ($continue -ne "y") {
    Write-Host "❌ Please complete the checklist first. See DEPLOYMENT_GUIDE.md" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📊 Database Setup" -ForegroundColor Green
Write-Host "=================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Go to your Supabase project: https://supabase.com/dashboard"
Write-Host "2. Click 'SQL Editor' in the left menu"
Write-Host "3. Click 'New Query'"
Write-Host "4. Copy the contents of 'supabase_schema.sql' and paste it"
Write-Host "5. Click 'Run' to create all tables"
Write-Host ""
Read-Host "Press Enter when database setup is complete..."

Write-Host ""
Write-Host "🖥️  Backend Deployment (Render)" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Go to https://dashboard.render.com"
Write-Host "2. Click 'New +' → 'Web Service'"
Write-Host "3. Connect your GitHub repository"
Write-Host "4. Configure:"
Write-Host "   - Name: explainnet-backend"
Write-Host "   - Root Directory: backend"
Write-Host "   - Build Command: pip install -r requirements-deploy.txt"
Write-Host "   - Start Command: uvicorn main:app --host 0.0.0.0 --port `$PORT"
Write-Host ""
Write-Host "5. Add Environment Variables:"
Write-Host "   DATABASE_URL=<your-supabase-connection-string>"
Write-Host "   GOOGLE_API_KEY=<your-key>"
Write-Host "   NEWS_API_KEY=<your-key>"
Write-Host "   GUARDIAN_API_KEY=<your-key>"
Write-Host "   PYTHON_VERSION=3.11"
Write-Host ""
Read-Host "Press Enter when backend is deployed..."

Write-Host ""
$renderUrl = Read-Host "Enter your Render backend URL (e.g., https://explainnet-backend.onrender.com)"

Write-Host ""
Write-Host "🎨 Frontend Deployment (Vercel)" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""
Write-Host "Updating environment.prod.ts with your backend URL..."

# Update frontend environment
$envFile = "frontend/explainnet-ui/src/environments/environment.prod.ts"
$envContent = @"
export const environment = {
  production: true,
  apiBaseUrl: '$renderUrl/api'
};
"@
Set-Content -Path $envFile -Value $envContent
Write-Host "✅ Updated $envFile" -ForegroundColor Green

Write-Host ""
Write-Host "Committing changes..."
git add .
git commit -m "Update production API URL for deployment"
git push

Write-Host ""
Write-Host "Now deploy to Vercel:"
Write-Host "1. Go to https://vercel.com/dashboard"
Write-Host "2. Click 'Add New...' → 'Project'"
Write-Host "3. Import your GitHub repository"
Write-Host "4. Configure:"
Write-Host "   - Framework Preset: Angular"
Write-Host "   - Root Directory: frontend/explainnet-ui"
Write-Host "   - Build Command: npm run build"
Write-Host "   - Output Directory: dist/explainnet-ui/browser"
Write-Host "5. Click 'Deploy'"
Write-Host ""
Read-Host "Press Enter when frontend is deployed..."

Write-Host ""
$vercelUrl = Read-Host "Enter your Vercel frontend URL (e.g., https://explainnet.vercel.app)"

Write-Host ""
Write-Host "🔄 Updating Backend CORS" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Go back to Render dashboard"
Write-Host "2. Click on your 'explainnet-backend' service"
Write-Host "3. Go to 'Environment' tab"
Write-Host "4. Add/Update these variables:"
Write-Host "   FRONTEND_URL=$vercelUrl"
Write-Host "   ALLOW_ORIGINS=$vercelUrl,http://localhost:4200"
Write-Host "5. Click 'Save Changes'"
Write-Host ""
Read-Host "Press Enter when CORS is updated..."

Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your URLs:" -ForegroundColor Cyan
Write-Host "   Backend API: $renderUrl/docs"
Write-Host "   Frontend App: $vercelUrl"
Write-Host ""
Write-Host "🧪 Test your deployment:" -ForegroundColor Yellow
Write-Host "   1. Visit $vercelUrl"
Write-Host "   2. Create a new topic"
Write-Host "   3. Wait for analysis"
Write-Host "   4. Check visualizations"
Write-Host ""
Write-Host "📚 For local development:" -ForegroundColor Yellow
Write-Host "   Backend: cd backend && uvicorn main:app --reload"
Write-Host "   Frontend: cd frontend/explainnet-ui && npm start"
Write-Host ""
Write-Host "🎉 Happy analyzing!" -ForegroundColor Green
