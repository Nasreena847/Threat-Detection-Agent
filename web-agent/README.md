# 🖥️ TrustTab Frontend Installation & Setup

This directory contains the Chrome Extension frontend for TrustTab, built using React, TypeScript, Tailwind CSS, and TanStack Query.

> **Naming note:** The underlying agent is registered on CROO as **Threat Detection Agent** (used for the repo name and CAP listing). **TrustTab** is the product/extension name shown in Chrome and the UI. Same project, two labels depending on context.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

* **Node.js** (v18 or higher)
* **npm** (or `pnpm` / `yarn`)
* **Google Chrome** browser

---

## 🚀 Getting Started

### 1. Clone the Repository & Navigate to Frontend

If you haven't already, clone the main repository and change to the frontend directory:

```bash
git clone https://github.com/<your-username>/Threat-Detection-Agent.git
cd Threat-Detection-Agent/frontend
```

### 2. Install Dependencies

Install the required node modules using npm:

```bash
npm install
```

### 3. Configure the Backend URL

Open `src/services/api.ts` and ensure the API endpoint points to your active backend environment.

**For local development:**

```typescript
const API_URL = "http://localhost:8000/api/audit";
```

**For production / cloud deployment:**

```typescript
const API_URL = "https://your-backend-url/api/audit";
```

### 4. Build the Extension

Compile the application and bundle the assets into a production-ready package:

```bash
npm run build
```

This will generate a static production build folder named `dist` inside your frontend directory.

---

## 🌐 Loading the Extension into Google Chrome

To install and run your newly compiled extension locally, use Chrome's Developer Mode:

1. Open a new tab in Google Chrome and navigate to `chrome://extensions/`
2. In the top-right corner, toggle the **Developer Mode** switch to **ON**
3. In the top-left corner, click the **Load unpacked** button
4. From the file browser dialog, navigate into your project folder and select the newly generated `dist` folder

🎉 The TrustTab extension is now loaded and ready to use!

---

## 🛠️ Development Workflow Note

Whenever you make structural changes to your frontend source files, make sure to run:

```bash
npm run build
```

Then, go back to `chrome://extensions/` and click the **Reload** (circular arrow) icon on the **TrustTab** card to apply your latest changes.
