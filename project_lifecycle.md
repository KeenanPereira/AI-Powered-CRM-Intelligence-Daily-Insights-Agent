# 📖 AHA Smart Homes: Project Lifecycle & Study Guide

This document serves as your personal study guide. It breaks down exactly how we moved from a blank folder to a production-grade AI CRM Intelligence platform. You can use this to learn the architecture, prepare for your presentation, and understand the "why" behind every line of code.

---

## Part 1: The Initial Problem & Requirements
**The Goal:** The assignment was to build an AI-driven system that transforms raw Zoho CRM data into actionable, daily business intelligence for the CEO.

**The "Toy Project" Trap:** Many candidates would solve this by writing a single Python script that downloads data into a CSV, feeds the messy CSV into OpenAI, and prints a paragraph. 

**Our Goal:** We wanted to build a "Production-Grade" architecture. That means:
1. It runs automatically on a server.
2. It uses a real cloud database (PostgreSQL), not a local file.
3. It guarantees the AI doesn't hallucinate math (by using SQL for calculations).
4. It keeps company data 100% private (by running open-source models locally instead of using ChatGPT).

---

## Part 2: Architectural Breakdown & Decisions

We split the project into strict "Domains" instead of throwing everything into one file.

### 1. Data Ingestion ([services/zoho_client.py](file:///g:/AHA%20Smart%20Homes%20Project%202/services/zoho_client.py))
*   **The Challenge:** The Zoho API uses OAuth 2.0. Access tokens expire every hour.
*   **Our Solution:** We manually exchanged an Auth Code for a permanent "Refresh Token." The [zoho_client.py](file:///g:/AHA%20Smart%20Homes%20Project%202/services/zoho_client.py) script now automatically asks Zoho for a fresh 1-hour token every time it runs.
*   **Key Decision (Incremental Sync):** Instead of downloading 10,000 leads every day, our script looks at our database for the [last_sync_time](file:///g:/AHA%20Smart%20Homes%20Project%202/services/database_client.py#41-46), and only asks Zoho for leads modified *after* that exact millisecond. This makes the script run in 1 second instead of 1 minute.

### 2. The Cloud Database ([services/database_client.py](file:///g:/AHA%20Smart%20Homes%20Project%202/services/database_client.py))
*   **The Challenge:** We needed a place to store data that a web dashboard could read instantly.
*   **Our Solution:** We used **Supabase**, a cloud-hosted PostgreSQL database.
*   **Key Decision (Raw vs. Aggregate):** A bad architecture would just save a new row every day saying `{"date": "Feb 22", "total_leads": 15}`. We chose to store the **raw individual leads** in a `leads_raw` table using UPSERTs. This allowed us to run powerful SQL queries (`SELECT count(*) WHERE lead_source = 'Google Ads' AND lead_status = 'Junk Lead'`) to calculate dynamic matrices on the fly. 

### 3. The Analytics Engine (SQL vs LLM)
*   **The Challenge:** LLMs are incredibly bad at math. If you give Llama 3.2 200 leads, it might miscount the conversion rate. 
*   **Our Solution:** We offloaded *all* mathematics to our SQL queries in [database_client.py](file:///g:/AHA%20Smart%20Homes%20Project%202/services/database_client.py). We wrote Python logic to create a `source_quality_matrix` and a `rep_pipeline_matrix`.
*   **The Result:** By the time the data reaches the AI, the math (e.g., "Kushal has 191 leads and ₹0 pipeline") is already a hard fact. 

### 4. The Intelligence Layer ([ai_agents/analyst_agent.py](file:///g:/AHA%20Smart%20Homes%20Project%202/ai_agents/analyst_agent.py))
*   **The Challenge:** We wanted to use AI, but we didn't want to expose sensitive CRM data to external servers (like OpenAI), and we didn't want the AI to write generic fluffy text.
*   **Our Solution:** We used **Ollama** to run `Llama 3.2` locally. This costs $0 and ensures zero data leakage.
*   **Key Decision (Prompt Engineering):** We engineered a "Zero-Shot, Strict Persona" prompt. We explicitly banned the AI from using emojis in the Whatsapp report, banned it from using jargon, and forced it to output two specific formats via XML tags (`<DASHBOARD_REPORT>` and `<WHATSAPP_REPORT>`).

### 5. The Presentation Layer ([app.py](file:///g:/AHA%20Smart%20Homes%20Project%202/app.py))
*   **The Challenge:** We needed a clean way to visualize the daily data without building a complex React frontend from scratch.
*   **Our Solution:** We used **Streamlit** mixed with **Plotly**. 
*   **Key Design:** We pulled the SQL metrics directly into metric cards and dynamic charts (like the bubble chart for Sales Reps). We placed the AI's Markdown analysis directly above the charts to provide the "narrative" for the numbers.

### 6. The Automation ([jobs/run_daily_sync.py](file:///g:/AHA%20Smart%20Homes%20Project%202/jobs/run_daily_sync.py) & Twilio)
*   **The Challenge:** The CEO shouldn't have to log into a dashboard to know if something is wrong. They need proactive alerts.
*   **Our Solution:** We wired up the **Twilio WhatsApp API** ([whatsapp_client.py](file:///g:/AHA%20Smart%20Homes%20Project%202/services/whatsapp_client.py)).
*   **The Result:** The [run_daily_sync.py](file:///g:/AHA%20Smart%20Homes%20Project%202/jobs/run_daily_sync.py) file acts as the primary "Orchestrator." When it runs, it fetches Zoho data -> Upserts to Supabase -> Calculates SQL Analytics -> Prompts Llama 3.2 -> Parses the XML -> Updates the Dashboard DB -> and posts the `WHATSAPP_REPORT` string directly to the CEO's phone.

---

## Part 3: Identifying and Solving Challenges

Throughout development, we hit several real-world roadblocks that you should highlight in your presentation, as they show you know how to debug like a Senior Engineer:

**Challenge 1: The "Hallucination" Problem**
*   *Issue:* Initially, the AI was making up numbers or writing generic advice like "You should try to get more leads."
*   *Fix:* We stopped feeding the AI raw text, and instead fed it a strictly structured JSON payload filled with mathematically-perfect SQL calculations. We rewrote the prompt to say "Give 1 to 2 sharp, realistic actions the CEO can take today based ONLY on the data."

**Challenge 2: The "Twilio 20003 Error"**
*   *Issue:* During the WhatsApp integration, the Twilio API successfully connected but rejected the message, throwing an `Error 20003`.
*   *Fix:* We discovered two issues. First, Twilio requires strict E.164 formatting (`+9181...`), so we stripped spaces from the [.env](file:///g:/AHA%20Smart%20Homes%20Project%202/.env) file. Second, we debugged that the Account SID and Auth Token had been accidentally swapped. We fixed the credentials and the message fired perfectly.

**Challenge 3: Formatting for Different Mediums**
*   *Issue:* The Dashboard required a deep, multi-paragraph analysis, but that exact same text looked terrible and overly long when blasted to a mobile WhatsApp screen.
*   *Fix:* We implemented dual-prompting. We told Llama 3.2 to write two reports at once, separated by XML tags (`<DASHBOARD_REPORT>` and `<WHATSAPP_REPORT>`). We then used Python Regex (`re.search()`) to rip the outputs apart and route them to their respective destinations.

---

## Part 4: Final Output & Business Value

You didn't just write a script; you built a scalable "product."

**The Final Flow:**
1. A cron job executes [run_daily_sync.py](file:///g:/AHA%20Smart%20Homes%20Project%202/jobs/run_daily_sync.py) at 8:00 AM.
2. It talks to Zoho, grabs exactly what changed in the last 24 hours.
3. It pushes those changes to Supabase PostgreSQL.
4. It calculates that "Google Ads has 0% junk but Walk-ins are dropping."
5. It hands that math to Llama 3.2 running locally on your hardware.
6. Llama 3.2 writes an executive summary.
7. The CEO's phone buzzes with a 5-bullet summary on WhatsApp.
8. The CEO opens their laptop, navigates to the Streamlit Dashboard, and sees dynamic Bubble Charts and Stacked Bar charts proving exactly why Llama 3.2 said what it said.

**If you explain this lifecycle—from data privacy choices to SQL math structuring—you will absolutely dominate your evaluation.**
