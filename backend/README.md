# ⚙️ TrustTab Backend Installation & Setup

This directory houses the FastAPI threat engine and CROO agent infrastructure for TrustTab, powered by Python.

> **Naming note:** The underlying agent is registered on CROO as **Threat Detection Agent**. **TrustTab** is the product name shown in the extension/UI.

## 📋 Prerequisites

Before setting up the backend, ensure you have the following installed:

* **Python 3.11+**
* **pip** (Python package installer)

---

## 🚀 Getting Started

### 1. Navigate to the Backend Directory

If you are at the repository root, switch to the backend folder:

```bash
cd backend
```

### 2. Create and Activate a Virtual Environment

Isolate your project dependencies by spinning up a clean virtual environment:

**On Windows (Command Prompt/PowerShell):**

```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies

Install the engine packages specified in the requirements file:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a new file named `.env` inside this `backend/` directory to store your secret keys securely:

```
CROO_API_KEY=your_agent_sdk_key
CROO_BASE_URL=https://api.croo.network
CROO_WS_URL=wss://api.croo.network/ws
CROO_SERVICE_ID=your_registered_threat_detection_service_id
```

⚠️ **Security Warning:** Never commit your `.env` file or expose your API keys publicly. Ensure `.env` is listed inside your root `.gitignore`.

---

## 🏃 Running the Server

Start the local Uvicorn development server with hot-reloading enabled:

```bash
uvicorn app.main:app --reload
```

* **Local Base URL:** `http://127.0.0.1:8000`
* **Interactive Swagger UI Docs:** `http://127.0.0.1:8000/docs`

When the CROO environment variables are configured, the FastAPI app also starts `CrooProvider` in the background. This keeps the CROO EventStream connected from the same web process that serves `/api/audit`; the audit endpoint itself still runs the local deterministic pipeline directly and does not create CROO negotiations or orders.

---

## Render Free Web Service

Deploy the backend as a single Render **Web Service**:

* **Root directory:** `backend`
* **Build command:** `pip install -r requirements.txt`
* **Start command:** `sh start.sh`

Required Render environment variables:

```
CROO_API_KEY=your_service_owner_agent_key
CROO_BASE_URL=https://api.croo.network
CROO_WS_URL=wss://api.croo.network/ws
CROO_SERVICE_ID=your_registered_threat_detection_service_id
```

The service exposes `GET /health` for uptime checks. On Render free tier, add an external uptime ping every 10 minutes to keep the container awake during testing; when the web service sleeps, the CROO WebSocket connection sleeps too.

---

## 🔍 Verifying the API Setup

Once your server is running, navigate to `http://127.0.0.1:8000/docs` to test the backend routes:

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Health status check |
| `GET` | `/health` | Render/uptime health check with CROO provider status |
| `POST` | `/api/audit` | Synchronous URL metadata assessment endpoint |