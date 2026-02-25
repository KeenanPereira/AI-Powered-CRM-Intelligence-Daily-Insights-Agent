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
    Calculate granular Funnel Metrics by querying Supabase.
    """
    if not target_date_iso:
        target_date_iso = datetime.now().strftime("%Y-%m-%d")
        
    target_start = f"{target_date_iso}T00:00:00"
    target_end = f"{target_date_iso}T23:59:59"
    
    target_date_obj = datetime.strptime(target_date_iso, "%Y-%m-%d")
    seven_days_ago_start = (target_date_obj - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00")
    
    results = {}
    
    # 1. New Leads Generated Today vs 7-Day Average
    res_today = supabase.table("leads_raw").select("*", count="exact").gte("created_time", target_start).lte("created_time", target_end).execute()
    results['new_leads_today'] = res_today.count if res_today.count is not None else 0
    
    res_7d = supabase.table("leads_raw").select("*", count="exact").gte("created_time", seven_days_ago_start).lt("created_time", target_start).execute()
    seven_day_total = res_7d.count if res_7d.count is not None else 0
    results['seven_day_avg'] = round(seven_day_total / 7) if seven_day_total else 0
    
    if results['seven_day_avg'] == 0:
        results['percent_change_leads'] = "0%"
    else:
        change = ((results['new_leads_today'] - results['seven_day_avg']) / results['seven_day_avg']) * 100
        sign = "+" if change > 0 else ""
        results['percent_change_leads'] = f"{sign}{round(change)}%"

    # 2. Unified Conversion Funnel (Leads + Deals)
    # We query both tables to build a massive top-to-bottom pipeline.
    res_leads = supabase.table("leads_raw").select("lead_status").execute()
    res_deals = supabase.table("crm_deals").select("stage").execute()
    
    funnel = {}
    for row in res_leads.data:
        st = row['lead_status']
        funnel[st] = funnel.get(st, 0) + 1
        
    for row in res_deals.data:
        st = row['stage']
        funnel[st] = funnel.get(st, 0) + 1
        
    results['pipeline_statuses'] = funnel
    
    # 3. Source Breakdown for Today (Leads + Deals)
    res_src_leads = supabase.table("leads_raw").select("lead_source").gte("created_time", target_start).lte("created_time", target_end).execute()
    res_src_deals = supabase.table("crm_deals").select("source").gte("created_time", target_start).lte("created_time", target_end).execute()
    
    sources = {}
    for row in res_src_leads.data:
        src = row.get('lead_source', 'Unknown')
        sources[src] = sources.get(src, 0) + 1
    for row in res_src_deals.data:
        src = row.get('source', 'Unknown')
        sources[src] = sources.get(src, 0) + 1
        
    results['source_breakdown'] = sources
    
    # 4. Pipeline Value (Driven by Deals table for absolute accuracy)
    # We ignore leads for this because Deal tracking is strictly monetary.
    res_revenue = supabase.table("crm_deals").select("amount,stage").neq("stage", "Closed Lost").execute()
    total_val = sum([row['amount'] for row in res_revenue.data if row['amount']])
            
    results['pipeline_value'] = round(total_val)
    
    # 5. The "Source Quality Matrix" (Volume vs Pipeline Quality)
    res_quality = supabase.table("leads_raw").select("lead_source,lead_status").gte("created_time", target_start).lte("created_time", target_end).execute()
    quality_matrix = {}
    for row in res_quality.data:
        src = row['lead_source']
        status = row['lead_status']
        if src not in quality_matrix:
            quality_matrix[src] = {"total_leads": 0, "junk_or_unqualified": 0, "in_pipeline": 0}
            
        quality_matrix[src]["total_leads"] += 1
        if status in ["Junk Lead", "Not Qualified"]:
            quality_matrix[src]["junk_or_unqualified"] += 1
        else:
            quality_matrix[src]["in_pipeline"] += 1
    
    # Calculate % Junk for each source
    for src, metrics in quality_matrix.items():
        metrics["junk_percentage"] = f"{round((metrics['junk_or_unqualified'] / metrics['total_leads']) * 100)}%"
        
    results['source_quality_matrix'] = quality_matrix
    
    # 6. Sales Rep Pipeline Holdings (From Deals)
    res_reps = supabase.table("crm_deals").select("owner,amount,stage").neq("stage", "Closed Lost").execute()
    reps_matrix = {}
    for row in res_reps.data:
        rep = row['owner']
        rev = row['amount'] or 0
        if rep not in reps_matrix:
            reps_matrix[rep] = {"active_leads": 0, "total_pipeline_value": 0}
            
        reps_matrix[rep]["active_leads"] += 1
        reps_matrix[rep]["total_pipeline_value"] += rev
        
    # Merge lead counts so reps with no deals but many leads still show up
    res_reps_leads = supabase.table("leads_raw").select("owner").execute()
    for row in res_reps_leads.data:
        rep = row['owner']
        if rep not in reps_matrix:
            reps_matrix[rep] = {"active_leads": 0, "total_pipeline_value": 0}
        reps_matrix[rep]["active_leads"] += 1
        
    results['rep_pipeline_matrix'] = reps_matrix
    
    return results

# ─────────────────────────────────────────────────────────────
# PHASE 12: COMPREHENSIVE ANALYTICS — ALL TABLES
# ─────────────────────────────────────────────────────────────

def get_overview_kpis():
    """Returns high-level KPI counts for the Overview tab."""
    kpis = {}
    # Total leads
    r = supabase.table("leads_raw").select("*", count="exact").execute()
    kpis['total_leads'] = r.count or 0
    # Total deals
    r = supabase.table("crm_deals").select("*", count="exact").execute()
    kpis['total_deals'] = r.count or 0
    # Total contacts
    r = supabase.table("crm_contacts").select("*", count="exact").execute()
    kpis['total_contacts'] = r.count or 0
    # Total accounts
    r = supabase.table("crm_accounts").select("*", count="exact").execute()
    kpis['total_accounts'] = r.count or 0
    # Open pipeline value (not Closed Lost)
    r = supabase.table("crm_deals").select("amount,stage").neq("stage", "Closed Lost").execute()
    kpis['open_pipeline_value'] = round(sum(row['amount'] or 0 for row in r.data))
    # Closed Won value
    r = supabase.table("crm_deals").select("amount,stage").eq("stage", "Closed Won").execute()
    kpis['closed_won_value'] = round(sum(row['amount'] or 0 for row in r.data))
    # Closed Won deal count
    kpis['closed_won_deals'] = len(r.data)
    # Junk % from leads
    r_all = supabase.table("leads_raw").select("lead_status").execute()
    all_statuses = [row['lead_status'] for row in r_all.data]
    total = len(all_statuses)
    junk = sum(1 for s in all_statuses if s in ["Junk Lead", "Not Qualified", "Not Qualified Lead"])
    kpis['junk_pct'] = round((junk / total) * 100) if total > 0 else 0
    return kpis

def get_lead_volume_trend(days: int = 30):
    """Returns daily new lead counts over the last N days for a trend line chart."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")
    r = supabase.table("leads_raw").select("created_time").gte("created_time", since).execute()
    daily_counts = {}
    for row in r.data:
        ct = row.get('created_time', '')
        if ct:
            day = ct[:10]  # "YYYY-MM-DD"
            daily_counts[day] = daily_counts.get(day, 0) + 1
    return daily_counts

def get_lead_status_breakdown():
    """Returns count of leads per status (all-time)."""
    r = supabase.table("leads_raw").select("lead_status").execute()
    counts = {}
    for row in r.data:
        s = row['lead_status'] or 'Unknown'
        counts[s] = counts.get(s, 0) + 1
    return counts

def get_source_quality_all_time():
    """Returns source quality matrix (junk vs pipeline) for ALL TIME, not just today."""
    r = supabase.table("leads_raw").select("lead_source,lead_status").execute()
    matrix = {}
    for row in r.data:
        src = row['lead_source'] or 'Unknown'
        status = row['lead_status'] or 'Unknown'
        if src not in matrix:
            matrix[src] = {"total_leads": 0, "junk_or_unqualified": 0, "in_pipeline": 0}
        matrix[src]["total_leads"] += 1
        if status in ["Junk Lead", "Not Qualified", "Not Qualified Lead"]:
            matrix[src]["junk_or_unqualified"] += 1
        else:
            matrix[src]["in_pipeline"] += 1
    for src, m in matrix.items():
        m["junk_pct"] = round((m['junk_or_unqualified'] / m['total_leads']) * 100) if m['total_leads'] > 0 else 0
    return matrix

def get_owner_lead_distribution():
    """Returns lead count per owner/sales rep (all-time)."""
    r = supabase.table("leads_raw").select("owner").execute()
    counts = {}
    for row in r.data:
        o = row['owner'] or 'Unassigned'
        counts[o] = counts.get(o, 0) + 1
    return counts

def get_deal_stage_breakdown():
    """Returns deal count and total value per stage."""
    r = supabase.table("crm_deals").select("stage,amount").execute()
    stages = {}
    for row in r.data:
        s = row['stage'] or 'Unknown'
        if s not in stages:
            stages[s] = {"count": 0, "value": 0}
        stages[s]["count"] += 1
        stages[s]["value"] += row['amount'] or 0
    return stages

def get_deal_value_by_owner():
    """Returns total deal value (open + won) per owner."""
    r = supabase.table("crm_deals").select("owner,amount,stage").execute()
    by_owner = {}
    for row in r.data:
        o = row['owner'] or 'Unassigned'
        if o not in by_owner:
            by_owner[o] = {"open_value": 0, "won_value": 0, "deal_count": 0}
        by_owner[o]["deal_count"] += 1
        if row['stage'] == "Closed Won":
            by_owner[o]["won_value"] += row['amount'] or 0
        elif row['stage'] != "Closed Lost":
            by_owner[o]["open_value"] += row['amount'] or 0
    return by_owner

def get_deals_closing_soon(days: int = 30):
    """Returns deals whose closing date is within the next N days."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    future_str = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    r = supabase.table("crm_deals").select("deal_name,stage,amount,owner,closed_time").gte("closed_time", today_str).lte("closed_time", future_str).neq("stage", "Closed Lost").neq("stage", "Closed Won").order("closed_time").execute()
    return r.data

def get_won_vs_lost():
    """Returns count and total ₹ for Closed Won vs Closed Lost deals."""
    r = supabase.table("crm_deals").select("stage,amount").execute()
    won_count, lost_count, won_val, lost_val = 0, 0, 0, 0
    for row in r.data:
        if row['stage'] == "Closed Won":
            won_count += 1
            won_val += row['amount'] or 0
        elif row['stage'] == "Closed Lost":
            lost_count += 1
            lost_val += row['amount'] or 0
    return {"won_count": won_count, "lost_count": lost_count, "won_value": round(won_val), "lost_value": round(lost_val)}

def get_contact_owner_distribution():
    """Returns contact count per owner."""
    r = supabase.table("crm_contacts").select("owner").execute()
    counts = {}
    for row in r.data:
        o = row['owner'] or 'Unassigned'
        counts[o] = counts.get(o, 0) + 1
    return counts

def get_account_industry_breakdown():
    """Returns account count per industry."""
    r = supabase.table("crm_accounts").select("industry").execute()
    counts = {}
    for row in r.data:
        ind = row['industry'] or 'Unknown'
        counts[ind] = counts.get(ind, 0) + 1
    return counts

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

def get_pipeline_period_stats():
    """
    Returns lead and pipeline value totals for today, this week, and this month.
    Used to power the daily/weekly/monthly metrics strip on the Overview tab.
    """
    now = datetime.now()
    today_start     = now.strftime("%Y-%m-%dT00:00:00")
    week_start      = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%dT00:00:00")
    month_start     = now.strftime("%Y-%m-01T00:00:00")

    stats = {}

    # --- Lead counts ---
    for label, since in [("today", today_start), ("week", week_start), ("month", month_start)]:
        r = supabase.table("leads_raw").select("*", count="exact").gte("created_time", since).execute()
        stats[f"leads_{label}"] = r.count or 0

    # --- Pipeline value (open deals) created in each period ---
    for label, since in [("today", today_start), ("week", week_start), ("month", month_start)]:
        r = supabase.table("crm_deals").select("amount,stage").gte("created_time", since).neq("stage", "Closed Lost").execute()
        stats[f"pipeline_{label}"] = round(sum(row["amount"] or 0 for row in r.data))

    return stats

