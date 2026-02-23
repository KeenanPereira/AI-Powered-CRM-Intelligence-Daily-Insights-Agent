import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from services import database_client

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AHA Smart Homes | CRM Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Sidebar: Date Filters & Info ────────────────────────────────────────────
with st.sidebar:
    st.title("🏠 AHA Smart Homes")
    st.caption("CRM Intelligence Platform")
    st.divider()
    st.markdown("**Last Refreshed:**")
    st.markdown(f"`{datetime.now().strftime('%d %b %Y, %H:%M')}`")
    st.divider()
    st.markdown("**Data Sources**")
    st.markdown("- `leads_raw` — Zoho Leads\n- `crm_deals` — Zoho Deals\n- `crm_contacts` — Zoho Contacts\n- `crm_accounts` — Zoho Accounts")
    st.divider()
    if st.button("🔄 Clear Cache & Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─── Cached Data Loaders ─────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def load_all_data():
    return {
        "kpis":           database_client.get_overview_kpis(),
        "trend":          database_client.get_lead_volume_trend(days=30),
        "lead_statuses":  database_client.get_lead_status_breakdown(),
        "source_quality": database_client.get_source_quality_all_time(),
        "owner_leads":    database_client.get_owner_lead_distribution(),
        "deal_stages":    database_client.get_deal_stage_breakdown(),
        "deal_by_owner":  database_client.get_deal_value_by_owner(),
        "closing_soon":   database_client.get_deals_closing_soon(days=30),
        "won_vs_lost":    database_client.get_won_vs_lost(),
        "contact_owners": database_client.get_contact_owner_distribution(),
        "industries":     database_client.get_account_industry_breakdown(),
        "sync_history":   database_client.get_sync_history(limit=10),
        "pipeline":       database_client.get_advanced_analytics(),
        "ai_dates":       database_client.get_all_briefing_dates(),
        "ai_report":      database_client.get_latest_ai_briefing(),
        "period_stats":   database_client.get_pipeline_period_stats(),
    }

d = load_all_data()
kpis = d["kpis"]

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🤖 AHA Smart Homes — CRM Intelligence")
st.caption(f"Live data from Supabase Cloud · {datetime.now().strftime('%A, %d %B %Y')}")
st.divider()

# ─── Top-Level KPI Row ───────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
c1.metric("Total Leads",    f"{kpis.get('total_leads', 0):,}")
c2.metric("Total Deals",    f"{kpis.get('total_deals', 0):,}")
c3.metric("Contacts",       f"{kpis.get('total_contacts', 0):,}")
c4.metric("Accounts",       f"{kpis.get('total_accounts', 0):,}")
c5.metric("Open Pipeline",  f"₹{kpis.get('open_pipeline_value', 0):,}")
c6.metric("Won Revenue",    f"₹{kpis.get('closed_won_value', 0):,}")
c7.metric("Lead Junk %",    f"{kpis.get('junk_pct', 0)}%", delta="Lower is better", delta_color="inverse")

st.divider()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🎯 Lead Intelligence",
    "💰 Deal Pipeline",
    "🤝 Contacts & Accounts",
    "🧠 AI Briefing & System Health"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Pipeline Overview")

    # ── Daily / Weekly / Monthly Pipeline Strip ──────────────────────────────
    ps = d["period_stats"]
    st.markdown("##### 📅 Period Performance")
    pc1, pc2, pc3, pc4, pc5, pc6 = st.columns(6)
    pc1.metric("Leads Today",        f"{ps.get('leads_today', 0):,}")
    pc2.metric("Leads This Week",    f"{ps.get('leads_week', 0):,}")
    pc3.metric("Leads This Month",   f"{ps.get('leads_month', 0):,}")
    pc4.metric("Pipeline Today",     f"₹{ps.get('pipeline_today', 0):,}")
    pc5.metric("Pipeline This Week", f"₹{ps.get('pipeline_week', 0):,}")
    pc6.metric("Pipeline This Month",f"₹{ps.get('pipeline_month', 0):,}")

    st.divider()

    # ── Row 1: Trend line + Deal Stage Bar ───────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        trend = d["trend"]
        if trend:
            df_trend = pd.DataFrame(
                sorted(trend.items()), columns=["Date", "New Leads"]
            )
            df_trend["Date"] = pd.to_datetime(df_trend["Date"])
            fig = px.line(
                df_trend, x="Date", y="New Leads",
                title="📈 New Lead Volume — Last 30 Days",
                markers=True, line_shape="spline"
            )
            fig.update_traces(line_color="#636EFA", fill="tozeroy", fillcolor="rgba(99,110,250,0.08)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lead trend data available yet.")

    with col_b:
        pipeline_statuses = d["pipeline"].get("pipeline_statuses", {})
        if pipeline_statuses:
            df_stages = (
                pd.DataFrame(list(pipeline_statuses.items()), columns=["Stage", "Count"])
                  .sort_values("Count", ascending=True)
            )
            fig = px.bar(
                df_stages, x="Count", y="Stage", orientation="h",
                title="📊 Unified Pipeline — Stage Breakdown (Leads + Deals)",
                color="Count", color_continuous_scale="Blues"
            )
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pipeline data available.")

    # ── Row 2: Source pie + Won vs Lost ──────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        src = d["pipeline"].get("source_breakdown", {})
        if src:
            df_src = pd.DataFrame(list(src.items()), columns=["Source", "Count"])
            fig = px.pie(
                df_src, values="Count", names="Source",
                title="🥧 All-Time Lead Source Distribution",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data.")

    with col_d:
        wl = d["won_vs_lost"]
        if wl["won_count"] or wl["lost_count"]:
            df_wl = pd.DataFrame([
                {"Outcome": "Closed Won",  "Count": wl["won_count"],  "Value (₹)": wl["won_value"]},
                {"Outcome": "Closed Lost", "Count": wl["lost_count"], "Value (₹)": wl["lost_value"]},
            ])
            fig = px.bar(
                df_wl, x="Outcome", y="Count", color="Outcome", text="Count",
                title="🏆 Won vs Lost Deals",
                color_discrete_map={"Closed Won": "#00CC96", "Closed Lost": "#EF553B"}
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            val_c1, val_c2 = st.columns(2)
            val_c1.metric("Total Won Value",  f"₹{wl['won_value']:,}")
            val_c2.metric("Total Lost Value", f"₹{wl['lost_value']:,}")
        else:
            st.info("No closed deals yet.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — LEAD INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Lead Intelligence — All Time")

    # Row 1: Status breakdown + Owner workload
    col_a, col_b = st.columns(2)

    with col_a:
        statuses = d["lead_statuses"]
        if statuses:
            df_st = (
                pd.DataFrame(list(statuses.items()), columns=["Status", "Count"])
                  .sort_values("Count", ascending=True)
            )
            fig = px.bar(
                df_st, x="Count", y="Status", orientation="h",
                title="📋 Lead Status Breakdown (All Time)",
                color="Count", color_continuous_scale="Blues"
            )
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lead data.")

    with col_b:
        owner_leads = d["owner_leads"]
        if owner_leads:
            df_ow = (
                pd.DataFrame(list(owner_leads.items()), columns=["Sales Rep", "Leads Assigned"])
                  .sort_values("Leads Assigned", ascending=True)
            )
            fig = px.bar(
                df_ow, x="Leads Assigned", y="Sales Rep", orientation="h",
                title="👤 Lead Ownership — Rep Workload",
                color="Leads Assigned", color_continuous_scale="Teal"
            )
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rep data.")

    st.divider()

    # Row 2: Source quality matrix (all time)
    st.markdown("#### Marketing Channel Quality Analysis")
    sq = d["source_quality"]
    if sq:
        q_rows = []
        for src, m in sq.items():
            q_rows.append({
                "Source": src,
                "Status": "In Pipeline",
                "Count": m["in_pipeline"]
            })
            q_rows.append({
                "Source": src,
                "Status": "Junk / Unqualified",
                "Count": m["junk_or_unqualified"]
            })
        df_q = pd.DataFrame(q_rows)
        fig = px.bar(
            df_q, x="Source", y="Count", color="Status", barmode="stack",
            title="📢 Source Quality Matrix — All Time (Junk vs Pipeline per Channel)",
            color_discrete_map={"In Pipeline": "#00CC96", "Junk / Unqualified": "#EF553B"}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Bubble chart: Source vs Junk % vs Lead Volume
        df_bubble = pd.DataFrame([
            {"Source": src, "Total Leads": m["total_leads"], "Junk %": m["junk_pct"], "In Pipeline": m["in_pipeline"]}
            for src, m in sq.items()
        ])
        fig2 = px.scatter(
            df_bubble, x="Source", y="Junk %", size="Total Leads",
            color="Junk %", color_continuous_scale=["#00CC96", "#FFA15A", "#EF553B"],
            hover_data=["Total Leads", "In Pipeline"],
            title="🫧 Lead Volume Bubble Chart — Source vs Junk %",
            size_max=60
        )
        fig2.update_layout(xaxis_title="Source", yaxis_title="Junk %")
        st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📄 View Raw Source Quality Table"):
            display_rows = [
                {
                    "Source": src,
                    "Total Leads": m["total_leads"],
                    "In Pipeline": m["in_pipeline"],
                    "Junk / Unqualified": m["junk_or_unqualified"],
                    "Junk %": f"{m['junk_pct']}%"
                }
                for src, m in sq.items()
            ]
            st.dataframe(pd.DataFrame(display_rows).sort_values("Total Leads", ascending=False), use_container_width=True)
    else:
        st.info("No source quality data available.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — DEAL PIPELINE
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Deal Pipeline Analytics")

    deal_stages = d["deal_stages"]

    # Row 1: Stage count + Stage value
    col_a, col_b = st.columns(2)

    with col_a:
        if deal_stages:
            df_stages = pd.DataFrame([
                {"Stage": s, "Deals": m["count"], "Value (₹)": round(m["value"])}
                for s, m in deal_stages.items()
            ]).sort_values("Deals", ascending=True)
            fig = px.bar(
                df_stages, x="Deals", y="Stage", orientation="h",
                title="📦 Deal Count by Stage",
                color="Deals", color_continuous_scale="Purples"
            )
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No deal stage data.")

    with col_b:
        if deal_stages:
            df_val = pd.DataFrame([
                {"Stage": s, "Value (₹)": round(m["value"])}
                for s, m in deal_stages.items()
            ]).sort_values("Value (₹)", ascending=True)
            fig = px.bar(
                df_val, x="Value (₹)", y="Stage", orientation="h",
                title="💹 Pipeline ₹ Value by Stage",
                color="Value (₹)", color_continuous_scale="Greens"
            )
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No deal value data.")

    st.divider()

    # Row 2: Deal value by owner (grouped bar)
    deal_owners = d["deal_by_owner"]
    if deal_owners:
        st.markdown("#### Sales Rep — Deal Performance")
        df_owner = pd.DataFrame([
            {
                "Sales Rep": o,
                "Open Pipeline (₹)": round(m["open_value"]),
                "Won Revenue (₹)": round(m["won_value"]),
                "Total Deals": m["deal_count"]
            }
            for o, m in deal_owners.items()
        ]).sort_values("Open Pipeline (₹)", ascending=False)

        fig = px.bar(
            df_owner.melt(id_vars="Sales Rep", value_vars=["Open Pipeline (₹)", "Won Revenue (₹)"],
                          var_name="Category", value_name="Value (₹)"),
            x="Sales Rep", y="Value (₹)", color="Category", barmode="group",
            title="👔 Deal Value by Sales Rep (Open vs Won)",
            color_discrete_map={"Open Pipeline (₹)": "#636EFA", "Won Revenue (₹)": "#00CC96"}
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📄 View Raw Rep Deal Table"):
            st.dataframe(df_owner, use_container_width=True)

    st.divider()

    # Row 3: Deals closing soon
    st.markdown("#### ⏰ Deals Closing in the Next 30 Days")
    closing = d["closing_soon"]
    if closing:
        df_close = pd.DataFrame(closing)
        df_close.rename(columns={
            "deal_name": "Deal", "stage": "Stage",
            "amount": "Amount (₹)", "owner": "Owner", "closed_time": "Close Date"
        }, inplace=True)
        df_close["Amount (₹)"] = df_close["Amount (₹)"].apply(lambda x: f"₹{x:,.0f}" if x else "₹0")
        st.dataframe(df_close, use_container_width=True)
    else:
        st.success("✅ No open deals with a deadline in the next 30 days.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — CONTACTS & ACCOUNTS
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Contacts & Accounts")

    col_a, col_b = st.columns(2)

    with col_a:
        contact_owners = d["contact_owners"]
        if contact_owners:
            df_co = (
                pd.DataFrame(list(contact_owners.items()), columns=["Owner", "Contacts"])
                  .sort_values("Contacts", ascending=True)
            )
            fig = px.bar(
                df_co, x="Contacts", y="Owner", orientation="h",
                title="👥 Contact Distribution by Owner",
                color="Contacts", color_continuous_scale="Teal"
            )
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📄 View Raw Contact Data"):
                r = database_client.supabase.table("crm_contacts").select("full_name,email,owner,created_time").order("created_time", desc=True).limit(100).execute()
                if r.data:
                    df_raw = pd.DataFrame(r.data)
                    df_raw.rename(columns={"full_name": "Name", "email": "Email", "owner": "Owner", "created_time": "Created"}, inplace=True)
                    st.dataframe(df_raw, use_container_width=True)
        else:
            st.info("No contact data synced yet.")

    with col_b:
        industries = d["industries"]
        if industries:
            df_ind = (
                pd.DataFrame(list(industries.items()), columns=["Industry", "Accounts"])
                  .sort_values("Accounts", ascending=False)
            )
            fig = px.pie(
                df_ind, values="Accounts", names="Industry",
                title="🏢 Accounts by Industry",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📄 View Raw Account Data"):
                r = database_client.supabase.table("crm_accounts").select("account_name,industry,owner,created_time").order("created_time", desc=True).limit(100).execute()
                if r.data:
                    df_raw = pd.DataFrame(r.data)
                    df_raw.rename(columns={"account_name": "Account", "industry": "Industry", "owner": "Owner", "created_time": "Created"}, inplace=True)
                    st.dataframe(df_raw, use_container_width=True)
        else:
            st.info("No account data synced yet.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — AI BRIEFING & SYSTEM HEALTH
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    col_a, col_b = st.columns([1.5, 1])

    with col_a:
        st.subheader("🧠 AI Executive Briefing")
        ai_dates = d["ai_dates"]
        if ai_dates:
            selected_date = st.selectbox("Select Report Date", ai_dates, index=0)
            briefing = database_client.get_briefing_by_date(selected_date)
            if briefing:
                st.info("Generated by local Llama 3.2 — grounded strictly in Supabase SQL data.")
                st.markdown(briefing)
            else:
                st.warning("No briefing found for this date.")
        else:
            st.info("No AI briefings logged yet. Run `run_daily_sync.py` to generate one.")

    with col_b:
        st.subheader("⚙️ System Health")

        sync_history = d["sync_history"]
        if sync_history:
            last_sync = sync_history[0]
            last_sync_time = last_sync.get("sync_time", "Unknown")[:19].replace("T", " ")
            total_records = last_sync.get("records_fetched", 0)

            st.metric("Last Sync Time", last_sync_time)
            st.metric("Records in Last Sync", f"{total_records:,}")
            st.divider()

            df_sync = pd.DataFrame(sync_history)
            df_sync["sync_time"] = df_sync["sync_time"].str[:16].str.replace("T", " ")
            df_sync.rename(columns={
                "sync_time": "Timestamp",
                "records_fetched": "Records",
                "status": "Status"
            }, inplace=True)
            st.markdown("**Last 10 Sync Logs**")
            st.dataframe(df_sync[["Timestamp", "Records", "Status"]], use_container_width=True)

            # Sync volume bar chart
            df_chart = df_sync[["Timestamp", "Records"]].copy()
            fig = px.bar(
                df_chart, x="Timestamp", y="Records",
                title="📡 Records Synced Per Run",
                color="Records", color_continuous_scale="Blues"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sync logs found.")

st.divider()
st.caption("Powered by Zoho CRM · Supabase Cloud PostgreSQL · Streamlit · Llama 3.2 (Local)")
