# Deploying Frontend on Vercel + Backend on Railway

This architecture provides the optimal split for hackathon presentation and global reliability:
- **Frontend on Vercel**: Global high-speed Edge CDN, automatic SSL certificates, unlimited free `.vercel.app` domains, zero DNS quota restrictions.
- **Backend on Railway**: Python FastAPI backend with Firebase Firestore cloud database integration.

---

## Step 1: Obtain your Railway Public Domain

1. Go to your **[Railway Dashboard](https://railway.com/dashboard)**.
2. Click on your deployed project (`sih26155_agent`).
3. Click on your active service container.
4. Go to **Settings** (tab at the top) -> scroll down to **Networking**.
5. Under **Public Networking**, click **"Generate Domain"**.
   - Railway will instantly assign you an official domain such as:
     `https://sih26155-agent-production-xxxx.up.railway.app`
6. Test this URL in your browser:
   `https://sih26155-agent-production-xxxx.up.railway.app/api/health`
   *(It should return `{"status":"ok","service":"SIH26155 Security Audit Agent",...}`)*.

---

## Step 2: Deploy Frontend on Vercel (1-Click Setup)

1. Open **[vercel.com/new](https://vercel.com/new)** and sign in with your GitHub account.
2. Under **Import Git Repository**, select **`saifpathan9969/sih26155_agent`**.
3. In the project configuration screen:
   - **Framework Preset**: Vite (automatically detected).
   - **Root Directory**: Click *Edit* and select **`frontend`**.
     *(Note: If you keep it as root `./`, it will also build automatically thanks to the root `vercel.json`!)*
4. Expand **Environment Variables** and add:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://sih26155-agent-production-xxxx.up.railway.app` *(your Railway domain from Step 1)* |
5. Click **"Deploy"**.
6. Within 30 to 45 seconds, your frontend is live at:
   `https://sih26155-agent.vercel.app`

---

## Step 3: Dynamic In-App Railway Backend Switcher

We added a failsafe in the frontend:
- If `VITE_API_BASE_URL` was not set or if you ever spin up a new Railway instance, click the **"Railway Live / Backend Offline"** status pill in the top header.
- A dialog opens where you can paste your Railway URL and click **"Save & Connect"**.
- You can also append `?backend=https://your-railway-app.up.railway.app` to any Vercel link when sharing with judges, and the app will auto-bind to the backend!

---

## Summary of Configured Files

- [`frontend/vercel.json`](file:///c:/Users/saifu/Downloads/sih26155_agent/frontend/vercel.json): Vercel routing configuration for Vite SPA.
- [`vercel.json`](file:///c:/Users/saifu/Downloads/sih26155_agent/vercel.json): Root monorepo fallback build script.
- [`frontend/src/api.js`](file:///c:/Users/saifu/Downloads/sih26155_agent/frontend/src/api.js): Dynamic URL resolver supporting Vercel env var, query param, and localStorage.
- [`frontend/src/App.jsx`](file:///c:/Users/saifu/Downloads/sih26155_agent/frontend/src/App.jsx): Interactive backend connection switcher and offline reconnection bar.
