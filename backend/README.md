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

---

## 🔍 Verifying the API Setup

Once your server is running, navigate to `http://127.0.0.1:8000/docs` to test the internal and CROO-facing routes:

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Health status check |
| `POST` | `/api/audit` | Synchronous URL metadata assessment endpoint |
| `GET` | `/api/croo/agents` | Fetches current active network agent parameters |
| `POST` | `/api/croo/invoke` | Simulates execution call chains via the agent infrastructure |
