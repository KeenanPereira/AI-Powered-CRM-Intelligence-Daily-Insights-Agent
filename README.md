# 🏠 AHA Smart Homes — AI-Powered CRM Intelligence Platform

> **"Extract everything. Store everything. Understand everything."**

A fully automated, production-grade CRM intelligence system that pulls **all data** from Zoho CRM across every module, stores it with zero data loss in a Supabase PostgreSQL cloud database using JSONB, performs deep SQL analytics across the entire conversion funnel, generates AI-driven executive insights with a private local LLM, delivers them via WhatsApp, and presents everything through a professional multi-tab Streamlit dashboard.

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        ZOHO CRM (Live API)                    │
│          Leads · Deals · Contacts · Accounts (ALL fields)     │
└────────────────────────────┬──────────────────────────────────┘
                             │  Incremental Sync (If-Modified-Since)
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                  Supabase Cloud (PostgreSQL)                   │
│  leads_raw · crm_deals · crm_contacts · crm_accounts          │
│  raw_data JSONB column → Zero data loss, infinite scalability │
└──────────┬────────────────────────────────┬───────────────────┘
           │  SQL Funnel Analytics           │  AI Payload
           ▼                                 ▼
┌──────────────────────┐       ┌────────────────────────────────┐
│   Streamlit Dashboard│       │   Mistral 7B (Local Ollama)    │
│   5 Tabs · 15+ Charts│       │   100% Private · $0 Cost       │
└──────────────────────┘       └────────────────┬───────────────┘
                                                 │ Executive Briefing
                                                 ▼
                                        ┌─────────────────┐
                                        │ WhatsApp (Twilio)│
                                        │ CEO Mobile Alert │
                                        └─────────────────┘
```

---

## 📁 Project Structure

```
AHA Smart Homes Project 2/
│
├── core/
│   ├── __init__.py
│   └── config.py                # Centralized env variable loader & validator
│
├── services/
│   ├── __init__.py
│   ├── zoho_client.py           # Zoho OAuth + dynamic multi-module extraction
│   ├── database_client.py       # 20+ Supabase query functions (JSONB upserts + analytics)
│   └── whatsapp_client.py       # Twilio WhatsApp dispatch
│
├── ai_agents/
│   ├── __init__.py
│   └── analyst_agent.py         # Dual-report Mistral prompt (Dashboard + WhatsApp)
│
├── jobs/
│   ├── __init__.py
│   └── run_daily_sync.py        # Main orchestrator: Omni-Sync → SQL → AI → WhatsApp
│
├── app.py                       # 5-tab Streamlit dashboard (15+ Plotly charts)
├── schema.sql                   # Supabase table definitions (4 tables + JSONB)
├── .env                         # Environment variables (NOT committed to git)
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) with `mistral` or `llama3.2` pulled locally
- A Zoho CRM account with API credentials (OAuth 2.0 Self-Client)
- A Supabase project
- A Twilio account with WhatsApp Sandbox enabled (optional)

### 1. Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install requests python-dotenv langchain-ollama supabase streamlit plotly pandas twilio
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Zoho CRM
ZOHO_CLIENT_ID=your_client_id
ZOHO_CLIENT_SECRET=your_client_secret
ZOHO_REFRESH_TOKEN=your_refresh_token
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_API_URL=https://www.zohoapis.in

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key

# Twilio WhatsApp (optional)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=+14155238886
TARGET_WHATSAPP_NUMBER=+91XXXXXXXXXX
```

### 3. Apply the Database Schema
Open your Supabase project → **SQL Editor** → paste the full contents of `schema.sql` → click **Run**.

This creates 6 tables:

| Table | Contents |
|---|---|
| `leads_raw` | All Zoho Leads with `raw_data JSONB` |
| `crm_deals` | All Zoho Deals (Potentials) with `raw_data JSONB` |
| `crm_contacts` | All Zoho Contacts with `raw_data JSONB` |
| `crm_accounts` | All Zoho Accounts with `raw_data JSONB` |
| `sync_logs` | Incremental sync history |
| `ai_briefings_log` | Historical AI reports |

### 4. Pull the AI Model
```bash
ollama pull mistral
```

---

## 🚀 Running the System

### Command 1 — Daily Sync Pipeline *(run once a day)*
Fetches all CRM data from Zoho, upserts to Supabase, runs AI analysis, and dispatches the WhatsApp briefing:
```powershell
$env:PYTHONPATH='.'; .\venv\Scripts\python.exe .\jobs\run_daily_sync.py
```

### Command 2 — Live Dashboard *(keep running continuously)*
```powershell
.\venv\Scripts\streamlit.exe run app.py
```
Then open **http://localhost:8501** in your browser.

> ⚠️ Make sure Ollama is running in the background before running the sync pipeline.

---

## 📊 Dashboard — 5 Tabs, 15+ Charts

| Tab | Contents |
|---|---|
| **📊 Overview** | 7 KPI cards, 30-day lead volume trend, unified conversion funnel, source pie chart, Won vs Lost bar |
| **🎯 Lead Intelligence** | All-time status breakdown, Rep workload, Source quality stacked bar, Lead volume treemap (colored by junk %) |
| **💰 Deal Pipeline** | Deal count by stage, Pipeline ₹ value by stage, Rep performance grouped bar (Open vs Won), Deals closing in 30 days table |
| **🤝 Contacts & Accounts** | Contacts per owner, Accounts by industry, raw data expanders |
| **🧠 AI & System Health** | Historical AI briefing reader with date picker, Sync log table, Sync volume chart |

---

## 🧠 AI Insight Engine

The LLM receives a mathematically pre-calculated payload (never raw data) and generates two distinct reports:

| Report | Delivered Via |
|---|---|
| **Deep-Dive Dashboard Report** | Streamlit UI Markdown |
| **Punchy Executive Summary** | WhatsApp message to CEO's phone |

### Data fed to the AI:

| Metric | Source |
|---|---|
| New leads today vs. 7-day average | `leads_raw` SQL count |
| Unified funnel (Leads + Deals stages) | `leads_raw` + `crm_deals` |
| Source Quality Matrix (Junk % per channel) | `leads_raw` SQL groupby |
| Rep Pipeline Matrix (Leads + Deal value per rep) | `leads_raw` + `crm_deals` |
| Open pipeline value | `crm_deals` amount sum |

---

## � Data Architecture — JSONB ELT Pattern

Instead of rigid column schemas that break whenever Zoho adds a new field, we use an **ELT (Extract, Load, Transform)** pattern:

- Every record from Zoho is fetched with **zero field filtering** — the entire JSON payload is returned.
- Core indexed columns (`id`, `owner`, `status`, `amount`, `dates`) are typed SQL columns for fast querying.
- The full, unfiltered JSON is stored in a `raw_data JSONB` column — meaning **no CRM data is ever lost**, even custom fields added after deployment.

---

## 🔧 Tech Stack

| Component | Technology |
|---|---|
| CRM Source | Zoho CRM API v2 (OAuth 2.0) |
| Database | Supabase (PostgreSQL + JSONB) |
| AI / LLM | Mistral 7B via Ollama (LangChain) — 100% local |
| Dashboard | Streamlit + Plotly Express |
| Notifications | Twilio WhatsApp API |
| Language | Python 3.10+ |
| Config | python-dotenv |

---

## ⚖️ Key Technical Decisions

### 1. JSONB ELT vs. Rigid Schema
Using `raw_data JSONB` means the database is future-proof. If a manager adds 50 new custom fields to Zoho tomorrow, they sync automatically with zero schema changes required.

### 2. SQL Math vs. LLM Math
All funnel calculations (conversion rates, junk %, pipeline value) are done in PostgreSQL before touching the LLM — eliminating all risk of AI hallucination on numbers.

### 3. Local LLM vs. Cloud API
Mistral 7B runs on-device via Ollama — ensuring **zero data leaves the building** and generating reports at **₹0 cost per run**.

### 4. Incremental Sync vs. Full Refresh
Using the `If-Modified-Since` HTTP header means only records **changed since the last sync** are downloaded, keeping the daily job fast regardless of CRM size.

### 5. Modular Architecture
Domain-driven modules (`core/`, `services/`, `ai_agents/`, `jobs/`) mean swapping a CRM, database, or LLM provider requires changes in exactly one file.

---


