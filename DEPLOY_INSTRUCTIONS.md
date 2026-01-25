# 🚀 Deployment Instructions (Forever Free Stack)

These steps are manual because they require authentication with external providers (Neon, Render, Vercel).

## 1. Database (Neon) - The Persistence Layer
1.  Go to [Neon Console](https://console.neon.tech).
2.  Create a new project: **sliceinsights**.
3.  **IMPORTANT**: Copy the Connection String (Postgres URL).
    *   It looks like: `postgres://user:pass@ep-xyz.aws.neon.tech/neondb`
4.  **Save this URL**, you will need it for Render.

## 2. Backend (Render) - The Compute Layer
1.  Go to [Render Dashboard](https://dashboard.render.com).
2.  Click **New +** -> **Blueprint**.
3.  Connect your GitHub repository.
4.  Render will auto-detect `render.yaml`.
5.  **Environment Variables**:
    *   Render will ask for `DATABASE_URL`. Paste the Neon URL.
    *   **CRITICAL**: Append `?sslmode=require` if missing.
    *   For `DATABASE_URL_SYNC`, paste the same URL but remove `+asyncpg` if present (or use the main one, the app handles conversion).
6.  Click **Apply**. Wait for build (~5 mins).
7.  **Copy the Backend URL**: e.g., `https://sliceinsights-backend.onrender.com`.

## 3. Frontend (Vercel) - The Presentation Layer
1.  Go to [Vercel Dashboard](https://vercel.com).
2.  Click **Add New** -> **Project**.
3.  Import `sliceinsights` repo.
4.  **Framework Preset**: Next.js (Auto-detected).
5.  **Root Directory**: Click "Edit" and select `frontend`.
6.  **Environment Variables**:
    *   `NEXT_PUBLIC_API_URL`: Paste the **Render Backend URL** + `/api/v1`.
    *   Example: `https://sliceinsights-backend.onrender.com/api/v1`
7.  Click **Deploy**.

## 4. Final Security Handshake
1.  Once Frontend is live, copy its domain (e.g., `https://sliceinsights.vercel.app`).
2.  Go back to **Render Dashboard** -> Environment.
3.  Update `ALLOWED_ORIGINS` to: `["https://sliceinsights.vercel.app"]`.
4.  Render will redeploy. **Done!**
