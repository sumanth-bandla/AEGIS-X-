# AEGIS X 3.0 — Open AI Data Investigation Agent

> **Calculate with code. Explain with AI. Verify with evidence.**  
> *From Raw Data to Trusted Insights.*

---

## Overview

**AEGIS X 3.0** is an enterprise-grade, AI-assisted data investigation and forensic platform. Upload any structured dataset (CSV or web endpoint) to instantly profile schemas, uncover mathematical and statistical anomalies, inspect evidence chains, and query your data through an AI Copilot grounded strictly in verified dataset context.

---

## Key Features

- **Automated Data Quality & Forensics**:
  - Null value detection & completeness auditing
  - Exact row duplicate identification
  - Business logic validation (e.g., `Quantity × Unit Price = Total`)
  - Statistical anomaly detection via Interquartile Range (IQR) & extreme outlier fences
  - Data Hygiene Health Score (0–100 scale)
- **AI Investigation Copilot**:
  - Live Server-Sent Events (SSE) streaming answers
  - Multi-provider support: **Google Gemini** (`gemini-2.5-flash`), **OpenAI**, **NVIDIA NIM**, and **Nebius AI Studio**
  - Context grounding: answers cite exact finding IDs (e.g., `F003`) and row indices
  - Zero client-side API key leakage (all requests proxied server-side via Node.js)
  - Seamless automatic fallback to a local deterministic rule-based engine when no key is set
- **Web & Remote Dataset Ingestion**:
  - Drag-and-drop or file upload for local `.csv` files (up to 25MB)
  - Direct import from any public web URL, GitHub raw link, or REST API endpoint
  - Real-time directory watching (`./data/`) with auto-broadcast to all open browser sessions
- **Cloud Database & Firestore Sync**:
  - Out-of-the-box support for Firebase Authentication and Google Cloud Firestore (`aegis-x-59031`)
  - Automated persistence of investigation snapshots and audit findings
- **Evidence Dossier & Exports**:
  - Forensic evidence chain linking each finding to rule thresholds and offending rows
  - Instant automated SQL remediation script generation
  - Exportable audit findings (CSV) and executive Markdown audit reports

---

## Architecture & Tech Stack

| Layer | Technology |
|---|---|
| **Runtime & Backend** | Node.js (v18+), Express.js |
| **Frontend UI** | Modern Vanilla JavaScript, Glassmorphic CSS Design System, Lucide Icons |
| **AI LLM Engine** | Google Gemini (`gemini-2.5-flash`), OpenAI (`gpt-4o-mini`), NVIDIA NIM, Nebius AI |
| **Database & Cloud** | Google Cloud Firestore, Firebase Authentication |
| **Realtime Stream** | Server-Sent Events (SSE) for both live chat streaming and directory-watching sync |

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/sumanth-bandla/AEGIS-X-.git
cd AEGIS-X-
npm install
```

### 2. Configure Environment

Create your `.env` file from the provided example:

```bash
cp .env.example .env
```

Add your preferred AI provider key:

```env
PORT=3000

# Google Gemini AI (Recommended)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Firebase Project Configuration (Optional)
FIREBASE_PROJECT_ID=aegis-x-59031
FIREBASE_AUTH_DOMAIN=aegis-x-59031.firebaseapp.com
FIREBASE_STORAGE_BUCKET=aegis-x-59031.firebasestorage.app
```

> **Note:** If no AI key is configured, AEGIS X automatically operates using its built-in local deterministic intelligence engine with zero setup required.

### 3. Launch the Application

```bash
npm start
```

Open your browser at **[http://localhost:3000](http://localhost:3000)**.

---

## Project Structure

```text
AEGIS-X/
├── server.js               # Express API: /api/chat (SSE), /api/status, /api/events
├── package.json            # Node project dependencies and start scripts
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules (protects credentials)
├── public/
│   ├── index.html          # Unified dashboard, copilot interface & forensic engine
│   └── assets/             # Branding emblems and icons
├── data/                   # Watched folder for live instant dataset ingestion
├── sample/                 # Sample datasets (e.g. Sales_Analysis_Dataset.csv)
├── services/               # Modular forensic & analytical services
└── docs/                   # Architecture and technical documentation
```

---

## Core Principles

1. **Calculate with Code**: Statistical boundaries, variances, and duplicate states are calculated deterministically.
2. **Explain with AI**: Large Language Models translate complex findings into executive summaries and action steps.
3. **Verify with Evidence**: Every finding references specific offending rows, original values, and verification queries.

---

## License

This project is licensed under the [MIT License](LICENSE).
