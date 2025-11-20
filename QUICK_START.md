# 🚀 ExplainNet - Quick Start Guide

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend runs on: http://localhost:8000

### Frontend
```bash
cd frontend/explainnet-ui
npm install
npm start
```
Frontend runs on: http://localhost:4200

---

## Production Deployment

### Hosted Services
- **Backend**: Render (https://render.com)
- **Database**: Supabase (https://supabase.com)  
- **Frontend**: Vercel (https://vercel.com)

### Quick Deploy Steps

1. **Database** (5 minutes)
   - Create Supabase project
   - Run `supabase_schema.sql` in SQL Editor
   - Copy DATABASE_URL

2. **Backend** (10 minutes)
   - Push code to GitHub
   - Create Render Web Service
   - Set environment variables
   - Deploy

3. **Frontend** (5 minutes)
   - Update `environment.prod.ts` with backend URL
   - Deploy to Vercel
   - Update backend CORS with frontend URL

### Automated Helper
```powershell
.\deploy.ps1
```

---

## 📚 Documentation

- **Full Deployment Guide**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **API Documentation**: `/docs` endpoint on backend
- **Environment Template**: `backend/.env.template`

---

## 🔑 Required API Keys

- Google API Key (YouTube + Gemini AI)
- News API Key
- Guardian API Key

---

## 🌐 Environment Switching

### Local (SQLite)
```env
DATABASE_URL=sqlite:///./explainnet.db
ALLOW_ORIGINS=http://localhost:4200
```

### Production (PostgreSQL)
```env
DATABASE_URL=postgresql://postgres:pass@db.supabase.co:5432/postgres
ALLOW_ORIGINS=https://your-app.vercel.app
```

**The app automatically detects the environment!**

---

## ✅ Verify Deployment

1. **Backend**: Visit `https://your-backend.onrender.com/docs`
2. **Frontend**: Visit `https://your-app.vercel.app`
3. **Integration**: Create a topic and check visualizations

---

## 🐛 Common Issues

**CORS Errors**: Update `ALLOW_ORIGINS` in Render to include Vercel URL

**Database Errors**: Verify `DATABASE_URL` format and credentials

**Build Fails**: Check `requirements-deploy.txt` for missing dependencies

---

## 💰 Cost

All free tier:
- Render: 750 hours/month (sleeps after 15min inactivity)
- Supabase: 500MB database
- Vercel: 100GB bandwidth

**Total: $0/month**

---

## 📞 Support

- Issues: GitHub Issues
- Docs: See DEPLOYMENT_GUIDE.md
- API: Visit `/docs` endpoint

---

Made with ❤️ by ExplainNet Team
