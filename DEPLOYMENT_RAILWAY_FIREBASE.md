# 🚂 Deployment Guide: Railway & Firebase Firestore

This guide explains how to deploy the **SIH26155 Multi-Vendor Network Compliance Auditor** to **Railway** with **Firebase Firestore** as the persistent cloud database.

---

## 🏗️ Architecture on Railway

- **Hosting Platform**: [Railway](https://railway.app) (Fast, flexible container deployment)
- **Database**: [Firebase Firestore](https://firebase.google.com) (NoSQL Document Store)
- **Build System**: Supported via both **Dockerfile** (via [`railway.json`](railway.json)) and **Nixpacks** (via [`nixpacks.toml`](nixpacks.toml))
- **Unified Service**: Single service running FastAPI that serves both the `/api/...` endpoints and the production React SPA!

---

## Step 1: Firebase Project & Private Key (3 minutes)

1. Go to [Firebase Console](https://console.firebase.google.com/).
2. Click **Add project** (e.g. `sih26155-auditor`) and click **Create Project**.
3. In the sidebar, navigate to **Build** ➔ **Firestore Database** ➔ Click **Create Database**.
   - Choose a location near you (e.g., `asia-south1` or `us-central1`).
   - Start in **Production mode** (or Test mode).
4. Download your Private Key:
   - Click the gear icon ⚙️ (top left) ➔ **Project settings**.
   - Go to the **Service accounts** tab.
   - Click **Generate new private key** ➔ **Generate key**.
   - Save the downloaded `.json` file on your computer.

---

## Step 2: Push Repository to GitHub

Make sure your latest code with `railway.json` and `nixpacks.toml` is committed and pushed to GitHub:

```bash
git add .
git commit -m "feat: Add Railway deployment configuration and Nixpacks builder"
git push -u origin main
```

---

## Step 3: Deploy on Railway (2 minutes)

1. Sign in to your [Railway Dashboard](https://railway.app/).
2. Click **+ New Project**.
3. Select **Deploy from GitHub repo**.
4. Choose your repository (e.g. `saifpathan9969/sih26155_agent`).
5. Click **Deploy Now**.
   - Railway will automatically detect the [`railway.json`](railway.json) / [`Dockerfile`](Dockerfile) and begin building the multi-stage image.

---

## Step 4: Add Firebase Credentials on Railway

1. In your Railway project dashboard, click on your deployed service card.
2. Go to the **Variables** tab.
3. Click **+ New Variable**:
   - **VARIABLE_NAME**: `FIREBASE_SERVICE_ACCOUNT_JSON`
   - **VALUE**: Open the downloaded Firebase `.json` file in Notepad, copy the **entire text**, and paste it here.
4. Click **Add**. Railway will automatically redeploy with Firebase Firestore connected!

---

## Step 5: Generate a Public Domain & Verify

1. In your service settings on Railway, go to the **Settings** tab.
2. Under **Networking** ➔ **Public Networking**, click **Generate Domain**.
3. You will get a URL like `https://sih26155-auditor-production.up.railway.app`.
4. Test the health endpoint:
   Visit `https://<your-railway-url>/api/health`:
   ```json
   {
     "status": "ok",
     "service": "SIH26155 Security Audit Agent",
     "database": "firebase_firestore",
     "firebase_connected": true
   }
   ```
5. Open your live app in your browser:
   - Log in with `saifullahpathan49@gmail.com` / `Sentry@779969`.
   - All uploaded configurations, user registrations, and blockchain provenance blocks will now be **permanently stored in Firebase Firestore**!
