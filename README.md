# TrustTab 🛡️

### **AI-Powered Browser Security Agent built with CROO**

TrustTab is an intelligent, real-time browser security agent that proactively identifies phishing and malicious websites. Operating both as an interactive Chrome Extension and a decentralized, machine-to-machine service via the CROO framework, TrustTab brings autonomous threat intelligence directly to users and AI agents alike.

---

## 📌 Overview

TrustTab is an AI-powered browser security agent that helps users identify phishing and malicious websites in real time. When a webpage is opened, TrustTab analyzes multiple security signals—including HTTPS usage, suspicious URL patterns, page metadata, and other environmental indicators—to generate an easy-to-understand security assessment.

Beyond functioning as a browser extension, TrustTab exposes its threat-analysis capability as a CROO service, enabling other autonomous AI agents to request website trust evaluations through decentralized agent commerce.

---

## ⚠️ The Problem

* **Zero-Day Phishing:** Millions of users unknowingly visit phishing websites daily. Traditional browser warnings rely heavily on static blacklists, leaving newly created, short-lived phishing sites undetected.
* **Lack of Context:** Existing security tools give binary "safe/unsafe" blocks without explaining *why* a website is flagged, leaving users disconnected from the decision-making process.
* **Isolated Web Intelligence:** Security infrastructure is traditionally built for humans, lacking standardized interfaces for autonomous AI agents to evaluate link safety before interacting with them.

---

## 💡 The Solution

TrustTab operates as a real-time AI-powered browser security agent executing on-the-fly website risk analysis. 

The agent proactively:
* **Analyzes** the active webpage's structural and structural components.
* **Computes** an algorithmic, multi-weighted risk score.
* **Explains** detected security anomalies in plain, natural language.
* **Recommends** contextual safety protocols and protective actions.
* **Exposes** this deep security analysis layer as a CROO Agent Service, enabling standard agent-to-agent security handshakes.

---

## ✨ Features

* **🔍 Real-Time Analysis:** Instant, on-demand evaluation of active browser tabs.
* **🛡️ AI-Powered Security Agent:** Deep heuristics and semantic parsing to classify web-based threats.
* **📊 Granular Risk Scoring:** Returns a transparent threat index scaled from `0` (Safe) to `100` (Critical).
* **🚨 Threat Classification:** Pinpoints exact threat types (e.g., typosquatting, credential harvesting, credential counterfeiting).
* **📋 Human-Readable Explanations:** Explainable AI breakdowns explaining why a specific page triggered anomalies.
* **💡 Actionable Safety Guardrails:** Clear recommendations on whether to proceed, exit, or isolate inputs.
* **🌐 Cross-Environment Utility:** Accessible natively via a Chrome Extension UI or programmatically via a FastAPI backend.
* **🤖 CROO Agent Native:** Service discoverability, streaming mechanics, and monetization options baked directly into the CROO ecosystem.

---

## 🏗️ Architecture

```
       Chrome Extension
              │
              ▼
        React Frontend
              │
              ▼
       FastAPI Backend
              │
       ┌──────┴────────┐
       │               │
       ▼               ▼
 Threat Engine   CROO Provider
       │               │
       ▼               ▼
  Risk Report    Agent Service
```

### **Component Breakdown**
1. **Frontend (Chrome Extension):** A lightweight React interface that hooks into browser tab events to capture document metadata and display security reports.
2. **Backend (FastAPI Engine):** Orchestrates the core threat analysis pipeline, aggregates security metrics, and manages agent routing.
3. **CROO Layer:** Registers TrustTab into the decentralized agent web, opening a bi-directional event stream for external integrations.

---

## 🛠️ Tech Stack

### **Frontend (Extension)**
* **Core:** React, TypeScript, Vite
* **Styling:** Tailwind CSS, Framer Motion (smooth transition status flags)
* **Data Fetching:** TanStack Query (`@tanstack/react-query`)

### **Backend & AI Architecture**
* **Framework:** FastAPI (Python), Pydantic (strict data validation)
* **Threat Engine:** Custom URL heuristics engine, NLP metadata analysis pipeline

### **Agent Infrastructure**
* **Network Integration:** CROO SDK
* **Communication Protocol:** CROO EventStream
* **Client Handshake:** CROO AgentClient

---

## ⚙️ How It Works

```
[ User Navigates to Site ]
           │
           ▼
[ Extension Extracts Metadata (URL, DOM structure, SSL) ]
           │
           ▼
[ Secure Payload Streamed to FastAPI Backend ]
           │
           ▼
┌─────────────────── Mixed-Pipeline Security Evaluation ───────────────────┐
│  1. Structural Heuristics  2. Semantics & Metadata  3. Network Profiles  │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
                      [ Composite Risk Report Generated ]
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
        [ Displayed inside UI ]               [ Exposed as CROO Service ]
   (Visual Signals & Human Advice)        (JSON Payloads for Fellow AI Agents)
```

1. **Capture:** The user loads a website, and the background security agent securely grabs essential metadata.
2. **Compute:** The backend threat pipeline processes the structure, domain health, and semantics of the target location.
3. **Report:** A full cryptographic threat profile is rendered inside the extension popup.
4. **Expose:** Concurrently, the identical capability is exposed downstream to the CROO network for independent agent invocation.

---

## 🤖 CROO Integration

TrustTab is structurally registered as an autonomous, discoverable **CROO Agent**. 

* **Seamless Connection:** Uses the native `CROO SDK` to bridge web infrastructure with distributed networks.
* **Online Status:** Establishes a persistent, highly responsive network provider node.
* **Agent-to-Agent Commerce:** Exposes a clean, structured schema allowing external autonomous agents (e.g., shopping agents, AI researchers) to pass a URL payload and receive a machine-readable security clearance report before interacting with unknown endpoints.

---

## 🚀 Roadmap & Future Improvements

- [ ] **Advanced ML Threat Vectors:** Fine-tuned deep learning models for sequence classification on zero-day URLs.
- [ ] **Vision-Based Threat Analysis:** OCR-based visual scanning of layout templates to catch fake mimicry/login portals.
- [ ] **Enriched OSINT Graphing:** Direct integrations with WHOIS records, passive DNS timelines, and VirusTotal APIs.
- [ ] **Advanced Cloud Sandbox:** Screenshot-based structural similarities indexing.
- [ ] **Reputation Memory:** Historical tracking and machine-attested confidence intervals over long horizons.
- [ ] **Multi-Agent Defense Swarms:** Cross-collaboration channels via CROO to orchestrate dynamic defenses with other firewalls.

---

## 📦 Deployment & Hosting Notes

* **Backend Matrix:** Designed for rapid orchestration across **Render** or **Railway** environments.
* **State Alert:** The public demonstration instances utilize a free cloud hosting tier. If the instance undergoes cold starts or is temporarily sleeping due to hosting limits, the extension will handle the exception gracefully with an optimized informational panel. Running the backend environment locally bypasses external latency.