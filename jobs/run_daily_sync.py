from datetime import datetime
from services.zoho_client import get_access_token, fetch_incremental_module
from ai_agents.analyst_agent import get_executive_summary
from services import database_client
from services.whatsapp_client import send_whatsapp_message
import json
import re

def build_ai_payload():
    """
    Builds the AI Payload using only the Advanced Analytics Database.
    We don't do maths here anymore; the Database handles the Funnel maths.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get True Analytics from Raw CRM Database
    analytics = database_client.get_advanced_analytics(today)
    period_stats = database_client.get_pipeline_period_stats()
    won_lost = database_client.get_won_vs_lost()
    
    final_payload = {
      "report_date": today,
      "daily_metrics": {
        "new_leads_yesterday": analytics['new_leads_today'],
        "seven_day_lead_average": analytics['seven_day_avg'],
        "percent_change_leads": analytics['percent_change_leads'],
        "total_open_pipeline_value": f"₹{analytics.get('pipeline_value', 0):,}",
        "pipeline_generated_today": f"₹{period_stats.get('pipeline_today', 0):,}",
        "closed_won_deals_total": won_lost.get('won_count', 0),
        "closed_won_value_total": f"₹{won_lost.get('won_value', 0):,}",
        "closed_lost_deals_total": won_lost.get('lost_count', 0),
        "closed_lost_value_total": f"₹{won_lost.get('lost_value', 0):,}"
      },
      "pipeline_funnel": analytics['pipeline_statuses'],
      "source_breakdown": analytics.get('source_breakdown', {}),
      "source_quality_matrix": analytics.get('source_quality_matrix', {}),
      "rep_pipeline_matrix": analytics.get('rep_pipeline_matrix', {}),
      "anomalies_detected_by_math": [
        "Historical database initialized. Incremental syncs logic tracking active."
      ]
    }
    
    # --- HARDCODED AI INSIGHT GENERATION (NO MATH REQUIRED BY LLM) ---
    rep_matrix = final_payload.get('rep_pipeline_matrix', {})
    for rep, data in rep_matrix.items():
        leads = data.get('active_leads', 0)
        pipe = data.get('total_pipeline_value', 0)
        # Identify overloaded reps (High lead volume, zero or very low pipeline value)
        if leads > 100 and pipe < 5000000:
            final_payload["anomalies_detected_by_math"].append(
                f"CRITICAL BOTTLENECK: {rep} is OVERLOADED. They have {leads} active leads but only ₹{pipe:,} in pipeline. "
                f"Recommendation: Immediately pause giving {rep} new leads and re-assign their existing pool."
            )
            
    source_matrix = final_payload.get('source_quality_matrix', {})
    for source, data in source_matrix.items():
        junk_pct_str = data.get('junk_pct', '0%')
        try:
            junk_pct = float(junk_pct_str.replace('%', ''))
        except (ValueError, AttributeError):
            junk_pct = 0
            
        if junk_pct >= 30 and data.get('total_leads', 0) > 5:
            final_payload["anomalies_detected_by_math"].append(
                f"TOXIC/UNDERPERFORMING CHANNEL: '{source}' generated {data.get('total_leads')} leads and {junk_pct_str} were JUNK. "
                "Recommendation: Review and heavily optimize this channel's targeting immediately."
            )

    return final_payload

def run_daily_pipeline():
    """Main Orchestrator: Incremental Fetch -> DB Upsert -> SQL Analytics -> AI Output"""
    print("========================================")
    print("🚀 STARTING: Production CRM Intelligence (Cloud)")
    print("========================================\n")
    
    # 1. Fetch live data incrementally
    token = get_access_token()
    if not token:
        print("❌ Pipeline failed at Authentication stage.")
        return
        
    last_sync = database_client.get_last_sync_time()
    
    modules_to_sync = ["Leads", "Deals", "Contacts", "Accounts"]
    total_records_synced = 0
    
    for module in modules_to_sync:
        records = fetch_incremental_module(token, module, last_sync)
        if records:
            print(f"\n⚙️  Upserting {len(records)} updated {module} into Supabase Cloud Pipeline Database...")
            database_client.upsert_module_data(module, records)
            total_records_synced += len(records)
        
    # Always log sync even if 0 new
    database_client.log_sync(total_records_synced)
    print("✅ Incremental Omni-Sync Logged in Cloud.")
    
    # 3. Pull SQL analytics and Hand to AI
    print("\n🧠 Generating AI Payload from Pipeline DB...")
    payload = build_ai_payload()
    print("Payload ready for AI:\n", json.dumps(payload, indent=2))
        
    print("\n🧠 Handing data to Llama 3.2 (Local Ollama)...")
    summary = get_executive_summary(payload)
        
    if summary:
        print("\n========================================")
        print("         📢 DAILY BRIEFING READY        ")
        print("========================================")
        print(summary)
        print("========================================\n")
        
        import re
        dashboard_match = re.search(r'<DASHBOARD_REPORT>\s*(.*?)\s*(?:</DASHBOARD_REPORT>|<WHATSAPP_REPORT>|$)', summary, re.DOTALL | re.IGNORECASE)
        whatsapp_match = re.search(r'<WHATSAPP_REPORT>\s*(.*?)\s*(?:</WHATSAPP_REPORT>|$)', summary, re.DOTALL | re.IGNORECASE)
        
        dashboard_report = dashboard_match.group(1).strip() if dashboard_match else summary.replace('<DASHBOARD_REPORT>', '').replace('</DASHBOARD_REPORT>', '').strip()
        
        # Priority: Exact match -> Extract anything after tag -> Fallback to dashboard
        if whatsapp_match:
            whatsapp_report = whatsapp_match.group(1).strip()
        elif "<WHATSAPP_REPORT>" in summary:
            whatsapp_report = summary.split("<WHATSAPP_REPORT>")[-1].replace("</WHATSAPP_REPORT>", "").strip()
        else:
            whatsapp_report = dashboard_report
            
        # Clean stray tags if Llama 3.2 malformed them
        whatsapp_report = re.sub(r'</?(DASHBOARD|WHATSAPP)_REPORT>', '', whatsapp_report).strip()
        
        # Save to Cloud DB instead of local text file using the dashboard format
        database_client.log_ai_briefing(dashboard_report)
        print("✅ Dashboard Briefing securely logged to Supabase ai_briefings_log table.")
        
        # Hard cap at 1500 chars — Twilio WhatsApp limit is 1600
        MAX_WA_CHARS = 1500
        if len(whatsapp_report) > MAX_WA_CHARS:
            # Truncate cleanly at the last newline before the limit
            truncated = whatsapp_report[:MAX_WA_CHARS]
            last_newline = truncated.rfind('\n')
            whatsapp_report = truncated[:last_newline] if last_newline > 0 else truncated
            whatsapp_report += "\n\n_(Report truncated to fit WhatsApp limit.)_"

        # Dispatch to CEO via WhatsApp using the mobile format
        print("\n📱 Dispatching AI Briefing to WhatsApp...")
        success = send_whatsapp_message(whatsapp_report)
        if success:
            print("✅ Successfully delivered to WhatsApp.")
        else:
            print("❌ WhatsApp delivery failed. Check logs.")
    else:
        print("❌ AI Agent failed to return a summary.")

if __name__ == "__main__":
    run_daily_pipeline()
