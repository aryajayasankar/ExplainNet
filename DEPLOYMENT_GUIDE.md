# ExplainNet Deployment Guide

This guide will help you deploy ExplainNet with:
- **Backend**: Render (Python/FastAPI)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: Vercel (Angular)

## 📋 Prerequisites

1. GitHub account (to connect repos)
2. Render account (free): https://render.com
3. Supabase account (free): https://supabase.com
4. Vercel account (free): https://vercel.com
5. API Keys:
   - Google API Key (YouTube Data API v3 + Gemini AI)
   - News API Key: https://newsapi.org
   - Guardian API Key: https://open-platform.theguardian.com

---

## 🗄️ STEP 1: Deploy Database on Supabase

### 1.1 Create Supabase Project

1. Go to https://supabase.com
2. Click "New Project"
3. Fill in:
   - **Name**: explainnet-db
   - **Database Password**: Create a strong password (SAVE THIS!)
   - **Region**: Choose closest to your users
4. Click "Create new project" (takes ~2 minutes)

### 1.2 Get Database Connection String

1. In your Supabase dashboard, go to **Settings** → **Database**
2. Scroll to "Connection string" → **URI**
3. Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with your actual password
5. **SAVE THIS STRING** - you'll need it for Render

### 1.3 Run Database Migrations

Once backend is deployed, run these migrations in Supabase SQL Editor:

1. Go to **SQL Editor** in Supabase
2. Run the schema creation (copy from `backend/models.py` structure)

---

## 🚀 STEP 2: Deploy Backend on Render

### 2.1 Push Code to GitHub

```bash
cd Z:\ExplainNet-ARUU
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2.2 Create Render Web Service

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub account
4. Select your "ExplainNet" repository
5. Configure:
   - **Name**: `explainnet-backend`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements-deploy.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

### 2.3 Set Environment Variables

In Render dashboard, go to **Environment** and add:

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
FRONTEND_URL=https://your-app.vercel.app
GOOGLE_API_KEY=your_google_api_key
NEWS_API_KEY=your_news_api_key
GUARDIAN_API_KEY=your_guardian_api_key
PYTHON_VERSION=3.11
ALLOW_ORIGINS=https://your-app.vercel.app,http://localhost:4200
```

**Important**:
- Replace `[YOUR-PASSWORD]` in DATABASE_URL with your Supabase password
- Replace `your-app.vercel.app` with your actual Vercel URL (add after Step 3)
- Add all your API keys

### 2.4 Deploy

1. Click "Create Web Service"
2. Wait for deployment (~5-10 minutes)
3. Your backend will be at: `https://explainnet-backend.onrender.com`
4. Test it: `https://explainnet-backend.onrender.com/docs`

### 2.5 Run Database Migrations

After first deployment:

1. Go to Render dashboard → **Shell**
2. Run:
   ```bash
   python add_video_emotions_migration.py
   python backfill_emotions.py
   ```

---

## 🎨 STEP 3: Deploy Frontend on Vercel

### 3.1 Update Backend URL

1. Edit `frontend/explainnet-ui/src/environments/environment.prod.ts`:
   ```typescript
   export const environment = {
     production: true,
     apiBaseUrl: 'https://explainnet-backend.onrender.com/api'
   };
   ```
2. Commit changes:
   ```bash
   git add .
   git commit -m "Update production API URL"
   git push
   ```

### 3.2 Deploy to Vercel

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Angular
   - **Root Directory**: `frontend/explainnet-ui`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist/explainnet-ui/browser`
5. Click "Deploy"
6. Wait for deployment (~3-5 minutes)

### 3.3 Get Your Vercel URL

1. After deployment, Vercel gives you a URL like: `https://explainnet-xxxxx.vercel.app`
2. **COPY THIS URL**

### 3.4 Update Backend CORS

1. Go back to Render dashboard
2. Update `FRONTEND_URL` environment variable with your Vercel URL
3. Update `ALLOW_ORIGINS` to include your Vercel URL
4. Click "Save Changes" (backend will redeploy)

---

## ✅ STEP 4: Verify Deployment

### 4.1 Test Backend

1. Visit: `https://explainnet-backend.onrender.com/docs`
2. Try the `/api/topics` endpoint
3. Should return an empty array `[]` initially

### 4.2 Test Frontend

1. Visit: `https://your-app.vercel.app`
2. Create a new topic
3. Wait for analysis to complete
4. Check all visualizations load

### 4.3 Test Full Integration

1. Create a topic on production
2. Verify backend processes it
3. Check data appears in Supabase
4. Confirm frontend displays results

---

## 🔧 Local Development Setup

### Backend (Local)

```bash
cd backend

# Use local SQLite
DATABASE_URL=sqlite:///./explainnet.db

# Start server
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### Frontend (Local)

```bash
cd frontend/explainnet-ui

# Install dependencies
npm install

# Start dev server
npm start
# Runs on http://localhost:4200
```

### Environment Switching

The app automatically detects:
- **Local**: Uses `environment.ts` → `http://localhost:8000/api`
- **Production**: Uses `environment.prod.ts` → `https://explainnet-backend.onrender.com/api`

No code changes needed!

---

## 📊 Database Migrations

### For Production (Supabase)

1. Go to Render Shell
2. Run migration:
   ```bash
   python your_migration_script.py
   ```

### For Local (SQLite)

```bash
cd backend
python add_video_emotions_migration.py
python backfill_emotions.py
```

---

## 🐛 Troubleshooting

### Backend Errors

**Issue**: `CORS policy` errors
**Fix**: Make sure `ALLOW_ORIGINS` in Render includes your Vercel URL

**Issue**: Database connection fails
**Fix**: Verify `DATABASE_URL` in Render matches Supabase connection string

### Frontend Errors

**Issue**: API calls failing
**Fix**: Check `environment.prod.ts` has correct Render URL

**Issue**: Build fails on Vercel
**Fix**: Ensure `vercel.json` output directory matches Angular config

### Database Issues

**Issue**: Tables don't exist
**Fix**: Run migrations in Render Shell after first deployment

---

## 💰 Cost Breakdown

| Service | Free Tier | Limits |
|---------|-----------|--------|
| Render | ✅ Yes | 750 hours/month, sleeps after 15 min inactivity |
| Supabase | ✅ Yes | 500MB database, 2GB bandwidth |
| Vercel | ✅ Yes | 100GB bandwidth, unlimited deployments |

**Total Monthly Cost**: $0 (on free tier)

**Note**: Render free tier sleeps after inactivity. First request after sleep takes ~30s to wake up.

---

## 🔐 Security Checklist

- [ ] Never commit `.env` files
- [ ] API keys stored only in Render/Vercel environment variables
- [ ] Database password is strong and saved securely
- [ ] CORS properly configured for your domains
- [ ] Supabase RLS (Row Level Security) configured if needed

---

## 🚀 Quick Deploy Checklist

1. [ ] Create Supabase project and get DATABASE_URL
2. [ ] Push code to GitHub
3. [ ] Deploy backend to Render with environment variables
4. [ ] Run database migrations in Render Shell
5. [ ] Update frontend with backend URL
6. [ ] Deploy frontend to Vercel
7. [ ] Update Render CORS with Vercel URL
8. [ ] Test end-to-end functionality

---

## 📞 Support URLs

- **Backend API Docs**: https://explainnet-backend.onrender.com/docs
- **Frontend App**: https://your-app.vercel.app
- **Supabase Dashboard**: https://supabase.com/dashboard
- **Render Dashboard**: https://dashboard.render.com
- **Vercel Dashboard**: https://vercel.com/dashboard

---

**Deployment Complete!** 🎉

Your ExplainNet app is now live and accessible worldwide!
