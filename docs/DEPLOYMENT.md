# Deployment Status

**Last Updated:** 2026-01-25  
**Environment:** Production (Free Tier)

## 🌐 Live URLs

| Service | URL | Status |
|---------|-----|--------|
| Frontend | https://sliceinsights.vercel.app | ✅ Online |
| Backend API | `https://sliceinsights-xxx.onrender.com` | 🔄 Deploying |
| Database | Neon (US East 1) | ✅ Online |

## 🏗️ Infrastructure

### Frontend (Vercel)
- **Framework:** Next.js
- **Build:** Automatic on push to `main`
- **CDN:** Global Edge Network
- **Cost:** $0/month (Hobby tier)

### Backend (Render)
- **Runtime:** Docker (Python 3.11)
- **Instance:** 512 MB RAM, 0.1 CPU
- **Deploy:** Auto-rebuild on GitHub push
- **Sleep:** After 15 min inactivity (first request ~30s)
- **Cost:** $0/month (Free tier)

### Database (Neon)
- **Type:** Postgres 17 (Serverless)
- **Storage:** 0.5 GB
- **Region:** AWS US East 1 (N. Virginia)
- **Connection:** TLS required
- **Cost:** $0/month (Free tier)

## 🔐 Security

- **HTTPS:** Enforced on all services
- **CORS:** Restricted to Vercel domain only
- **Secrets:** Managed via environment variables
- **Rate Limiting:** SlowAPI configured
- **Monitoring:** Sentry integration ready (DSN pending)

## 📋 Environment Variables

### Backend (Render)
```
DATABASE_URL=postgresql://neondb_owner:***@ep-***.neon.tech/neondb?sslmode=require
ALLOWED_ORIGINS=["https://sliceinsights.vercel.app"]
DEBUG=false
LOG_LEVEL=INFO
```

### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL=https://sliceinsights-xxx.onrender.com/api/v1
```

## 🚀 Deployment Process

1. **Code Push:** Developer pushes to `main` branch
2. **Frontend:** Vercel auto-deploys (~2 min)
3. **Backend:** Render auto-rebuilds (~5-10 min)
4. **Database:** Always available (serverless)

## ⚠️ Known Limitations (Free Tier)

- Backend cold starts after 15 min (~30s first request)
- Database computes: 191 hours/month
- No custom domains without upgrade
- Limited concurrent connections

## 📈 Next Steps

- [ ] Monitor backend performance after launch
- [ ] Set up Sentry for error tracking
- [ ] Configure custom domain (requires upgrade)
- [ ] Implement CDN caching strategy
