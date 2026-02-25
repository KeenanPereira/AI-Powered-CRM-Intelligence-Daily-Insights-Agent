from supabase import create_client, Client
from datetime import datetime, timedelta
from core.config import Config
import socket
import urllib.request
import json
import logging

def _bypass_isp_dns_block():
    """
    Reliance Jio often blocks .co domains by hijacking system DNS.
    This dynamically asks Google's DNS for the real Cloudflare/AWS IP
    and patches Python's core socket to force connection, bypassing Jio.
    """
    try:
        host = "elrbabblikqjovunqlar.supabase.co"
        url = f"https://dns.google/resolve?name={host}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            ips = [a['data'] for a in data.get('Answer', []) if a['type'] == 1]
            if ips:
                real_ip = ips[0]
                _orig_getaddrinfo = socket.getaddrinfo
                def _custom_getaddrinfo(h, port, family=0, type=0, proto=0, flags=0):
                    if h == host:
                        return _orig_getaddrinfo(real_ip, port, family, type, proto, flags)
                    return _orig_getaddrinfo(h, port, family, type, proto, flags)
                socket.getaddrinfo = _custom_getaddrinfo
                logging.info(f"🛡️ DNS Patch Active: Bypassing ISP Block for Supabase ({real_ip})")
    except Exception as e:
        logging.warning(f"Failed to apply DNS patch: {e}")

_bypass_isp_dns_block()

supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def upsert_module_data(module_name: str, records: list):
    """
    Inserts or updates raw CRM records in Supabase (Cloud PostgreSQL).
    Safely stores the entire unfiltered exact payload in the `raw_data` JSONB column.
    """
    if not records: return
    formatted_data = []
    table = None
    
    for rec in records:
        rec_id = rec.get('id')
        if not rec_id: continue
        
        owner_obj = rec.get('Owner')
        owner = owner_obj.get('name', 'Unassigned') if isinstance(owner_obj, dict) else 'Unassigned'
        
        row = {
            "id": rec_id,
            "owner": owner,
            "created_time": rec.get('Created_Time'),
            "modified_time": rec.get('Modified_Time'),
            "raw_data": rec  # JSONB insertion
        }
        
        if module_name == "Leads":
            row["full_name"] = rec.get('Full_Name', 'Unknown')
            row["lead_source"] = rec.get('Lead_Source', 'Unknown')
            row["lead_status"] = rec.get('Lead_Status', 'New Lead')
            row["annual_revenue"] = float(rec.get('Annual_Revenue', 0) or 0)
            table = "leads_raw"
        elif module_name == "Deals":
            row["deal_name"] = rec.get('Deal_Name', 'Unknown')
            row["stage"] = rec.get('Stage', 'Unknown')
            row["source"] = rec.get('Lead_Source', 'Unknown')
            row["amount"] = float(rec.get('Amount', 0) or 0)
            row["closed_time"] = rec.get('Closing_Date')
            table = "crm_deals"
        elif module_name == "Contacts":
            row["full_name"] = rec.get('Full_Name', 'Unknown')
            row["email"] = rec.get('Email', 'Unknown')
            table = "crm_contacts"
        elif module_name == "Accounts":
            row["account_name"] = rec.get('Account_Name', 'Unknown')
            row["industry"] = rec.get('Industry', 'Unknown')
            table = "crm_accounts"
            
        formatted_data.append(row)
        
    if formatted_data and table:
        supabase.table(table).upsert(formatted_data).execute()

def log_sync(records_fetched: int):
    supabase.table("sync_logs").insert({
        "sync_time": datetime.now().isoformat(),
        "records_fetched": records_fetched,
        "status": "SUCCESS"
    }).execute()

def get_last_sync_time():
    """Returns the ISO timestamp of the last successful sync, or None."""
    response = supabase.table("sync_logs").select("sync_time").eq("status", "SUCCESS").order("id", desc=True).limit(1).execute()
    data = response.data
    return data[0]['sync_time'] if data else None

def get_advanced_analytics(target_date_iso=None):
    """
    Calculate granular Funnel Metrics by querying Supabase RPC.
    """
    if not target_date_iso:
        target_date_iso = datetime.now().strftime("%Y-%m-%d")
    
    r = supabase.rpc("get_advanced_analytics", {"target_date_iso": target_date_iso}).execute()
    return r.data if r.data else {}

# ─────────────────────────────────────────────────────────────
# PHASE 12: COMPREHENSIVE ANALYTICS — ALL TABLES 
# (NOW POWERED BY POSTGRESQL NATIVE COMPUTATION)
# ─────────────────────────────────────────────────────────────

def get_overview_kpis():
    r = supabase.rpc("get_overview_kpis").execute()
    return r.data if r.data else {}

def get_pipeline_period_stats():
    r = supabase.rpc("get_pipeline_period_stats").execute()
    return r.data if r.data else {}

def get_lead_volume_trend(days: int = 30):
    r = supabase.rpc("get_lead_volume_trend", {"days": days}).execute()
    return r.data if r.data else {}

def get_lead_status_breakdown():
    r = supabase.rpc("get_lead_status_breakdown").execute()
    return r.data if r.data else {}

def get_owner_lead_distribution():
    r = supabase.rpc("get_owner_lead_distribution").execute()
    return r.data if r.data else {}

def get_deal_stage_breakdown():
    r = supabase.rpc("get_deal_stage_breakdown").execute()
    return r.data if r.data else {}

def get_deal_value_by_owner():
    r = supabase.rpc("get_deal_value_by_owner").execute()
    return r.data if r.data else {}

def get_deals_closing_soon(days: int = 30):
    r = supabase.rpc("get_deals_closing_soon", {"days": days}).execute()
    return r.data if r.data else []

def get_won_vs_lost():
    r = supabase.rpc("get_won_vs_lost").execute()
    return r.data if r.data else {}

def get_contact_owner_distribution():
    r = supabase.rpc("get_contact_and_account_breakdown").execute()
    return r.data.get("contact_owners", {}) if r.data else {}

def get_account_industry_breakdown():
    r = supabase.rpc("get_contact_and_account_breakdown").execute()
    return r.data.get("industries", {}) if r.data else {}

def get_source_quality_all_time():
    r = supabase.rpc("get_source_quality_all_time").execute()
    return r.data if r.data else {}

def get_sync_history(limit: int = 10):
    """Returns last N sync log records for the System Health tab."""
    r = supabase.table("sync_logs").select("*").order("id", desc=True).limit(limit).execute()
    return r.data

def log_ai_briefing(markdown_content: str):
    """Saves the AI Briefing to the cloud database."""
    today = datetime.now().strftime("%Y-%m-%d")
    supabase.table("ai_briefings_log").upsert({
        "report_date": today,
        "markdown_content": markdown_content
    }, on_conflict="report_date").execute()

def get_latest_ai_briefing():
    """Fetches the latest AI briefing from Supabase."""
    res = supabase.table("ai_briefings_log").select("markdown_content").order("id", desc=True).limit(1).execute()
    if res.data:
        return res.data[0]['markdown_content']
    return None

def get_all_briefing_dates():
    """Returns a list of all dates that have AI briefings, newest first."""
    res = supabase.table("ai_briefings_log").select("report_date").order("report_date", desc=True).execute()
    if res.data:
        return [row['report_date'] for row in res.data]
    return []

def get_briefing_by_date(report_date: str):
    """Fetches the AI briefing for a specific date."""
    res = supabase.table("ai_briefings_log").select("markdown_content").eq("report_date", report_date).execute()
    if res.data:
        return res.data[0]['markdown_content']
    return None
