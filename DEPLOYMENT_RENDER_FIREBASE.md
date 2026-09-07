# 🚀 Deployment Guide: Render & Firebase Firestore

This guide provides end-to-end instructions for deploying the **SIH26155 Multi-Vendor Network Security Compliance Auditor** to **Render** with **Firebase Firestore** as the persistent cloud database.

---

## 🏗️ Architecture Overview

- **Cloud Platform**: [Render](https://render.com) (Free Tier compatible)
- **Database**: [Firebase Firestore](https://firebase.google.com) (NoSQL Document Store)
- **Runtime**: Python 3.11 + Vite React SPA (Unified Full-Stack Deployment via `build.sh` and FastAPI Static Mounting)
- **Zero-Failure Fallback**: If Firebase credentials are not provided or Firebase is unreachable, the system **automatically falls back to in-memory/local mode** without crashing.

---

## Part 1: Firebase Project Setup (5 minutes)

1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Click **Add project** (e.g. name it `sih26155-auditor`). Disable Google Analytics if not needed, then click **Create Project**.
3. In the left navigation menu, go to **Build** ➔ **Firestore Database**.
4. Click **Create Database**:
   - Choose a location near your target users (e.g. `asia-south1` for Mumbai, or `us-central1`).
   - Start in **Production mode** (or Test mode).
5. Generate your Service Account Private Key:
   - Click the gear icon ⚙️ next to **Project Overview** (top left) ➔ **Project settings**.
   - Navigate to the **Service accounts** tab.
   - Under **Firebase Admin SDK**, ensure **Python** is selected.
   - Click **Generate new private key**, then confirm **Generate key**.
   - A `.json` file (e.g. `sih26155-auditor-firebase-adminsdk-xxxxx.json`) will be downloaded to your computer.

---

## Part 2: Deploy to Render (5 minutes)

### Option A: 1-Click Render Blueprint (Recommended)

1. Push this repository to your **GitHub** account.
2. Sign in to your [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** ➔ **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically detect [`render.yaml`](render.yaml) and configure:
   - **Service Name**: `sih26155-network-compliance-auditor`
   - **Build Command**: `./build.sh`
   - **Start Command**: `cd sih26155_agent && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Health Check**: `/api/health`
6. Under **Environment Variables**, configure:
   - **`FIREBASE_SERVICE_ACCOUNT_JSON`**:
     Open the `.json` file downloaded in Part 1 in any text editor, copy its **entire JSON content**, and paste it into this field.
7. Click **Apply**. Render will automatically build the React frontend, install backend dependencies, connect to Firebase, and provide you with a live `https://<your-app>.onrender.com` URL!

---

### Option B: Manual Web Service Setup on Render

If you prefer to configure the Web Service manually:
1. Click **New +** ➔ **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name**: `sih26155-auditor`
   - **Region**: Oregon or Frankfurt
   - **Branch**: `main`
   - **Language / Runtime**: `Python`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `cd sih26155_agent && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. Expand **Advanced** ➔ **Environment Variables**:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.11.9` | Recommended Python version |
   | `FIREBASE_SERVICE_ACCOUNT_JSON` | `{"type": "service_account", ...}` | Paste entire contents of downloaded service account JSON |
5. Click **Create Web Service**.

---

## Part 3: Verification & Health Check

Once deployment is complete:
1. Open your live Render URL (e.g. `https://sih26155-auditor.onrender.com`).
2. Test the health endpoint by visiting `/api/health`:
   ```json
   {
     "status": "ok",
     "service": "SIH26155 Security Audit Agent",
     "database": "firebase_firestore",
     "firebase_connected": true
   }
   ```
3. Log in with the pre-seeded admin credentials:
   - **Email / Username**: `saifullahpathan49@gmail.com`
   - **Password**: `Sentry@779969`
4. Register a new user account:
   - Verify that the new user document appears in your Firebase Firestore console under the `users` collection!
5. Upload a configuration file or run an audit mission:
   - Verify that configuration metadata and blockchain provenance blocks are sealed and recorded into the `blockchain_ledger` Firestore collection!

---

## 🔒 Security & Best Practices

- **Never commit serviceAccountKey.json to git**: It contains private keys. Keep it only in Render environment variables or a local `.env` file added to `.gitignore`.
- **Render Free Tier Spin-Down**: On Render's free tier, the web service spins down after 15 minutes of inactivity. The first request after spin-down may take ~30-50 seconds to initialize. With Firebase Firestore, all your uploaded configurations, user accounts, and blockchain blocks **remain permanently saved** across restarts!
