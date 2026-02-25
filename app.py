import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
from services import database_client

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AHA Smart Homes | CRM Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

pio.templates.default = "plotly_dark"

# ─── Premium CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── KPI Cards ── */
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px 22px;
    border-radius: 14px;
    backdrop-filter: blur(10px);
    transition: all 0.25s ease;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-4px);
    border-color: rgba(255,255,255,0.18);
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
div[data-testid="stMetricLabel"] { font-size: 13px; color: #9CA3AF; font-weight: 500; letter-spacing: 0.03em; }
div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #F3F4F6; margin-top: 4px; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(255,255,255,0.04);
    padding: 6px;
    border-radius: 12px;
}
[data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 9px 18px !important;
    color: #6B7280 !important;
    font-weight: 500 !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.2s ease;
    font-size: 14px !important;
}
[data-baseweb="tab"]:hover { color: #D1D5DB !important; background: rgba(255,255,255,0.06) !important; }
[data-baseweb="tab"][aria-selected="true"] {
    color: #fff !important;
    background: rgba(99,102,241,0.25) !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
}

/* ── Insight Callout Card ── */
.insight-card {
    background: rgba(99,102,241,0.1);
    border-left: 3px solid #6366F1;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0 20px 0;
    font-size: 14px;
    color: #C7D2FE;
    line-height: 1.6;
}
.warning-card {
    background: rgba(245,158,11,0.1);
    border-left: 3px solid #F59E0B;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0 20px 0;
    font-size: 14px;
    color: #FDE68A;
    line-height: 1.6;
}
.success-card {
    background: rgba(16,185,129,0.1);
    border-left: 3px solid #10B981;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0 20px 0;
    font-size: 14px;
    color: #A7F3D0;
    line-height: 1.6;
}
.section-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 12px;
}

/* ── App Header ── */
.app-header { margin-bottom: 6px; }
.app-header h1 { font-size: 28px; font-weight: 700; color: #F9FAFB; letter-spacing: -0.5px; }
.app-header p  { color: #6B7280; font-size: 13px; margin-top: 2px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: rgba(17,17,23,0.9); border-right: 1px solid rgba(255,255,255,0.06); }

/* ── Remove Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
div.block-container { padding-top: 1.8rem; }

/* ── Dividers ── */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 28px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏠 AHA Smart Homes")
    st.caption("CRM Intelligence Platform")
    st.divider()
    st.markdown("<div class='section-label'>Last Refreshed</div>", unsafe_allow_html=True)
    st.markdown(f"`{datetime.now().strftime('%d %b %Y, %H:%M')}`")
    st.divider()
    st.markdown("<div class='section-label'>Data Sources</div>", unsafe_allow_html=True)
    st.markdown("- `leads_raw` — Zoho Leads\n- `crm_deals` — Zoho Deals\n- `crm_contacts` — Zoho Contacts\n- `crm_accounts` — Zoho Accounts")
    st.divider()
    if st.button("🔄 Clear Cache & Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─── Data Loader ─────────────────────────────────────────────────────────────
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
k = d["kpis"]
ps = d["period_stats"]

# ─── Page Header ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='app-header'>
    <h1>AHA Smart Homes — CRM Intelligence</h1>
    <p>Live data from Supabase Cloud &nbsp;·&nbsp; {datetime.now().strftime('%A, %d %B %Y')}</p>
</div>
""", unsafe_allow_html=True)

# ─── Top KPI Strip ───────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
c1.metric("Total Leads",   f"{k.get('total_leads', 0):,}")
c2.metric("Total Deals",   f"{k.get('total_deals', 0):,}")
c3.metric("Contacts",      f"{k.get('total_contacts', 0):,}")
c4.metric("Accounts",      f"{k.get('total_accounts', 0):,}")
c5.metric("Open Pipeline", f"₹{k.get('open_pipeline_value', 0):,}")
c6.metric("Won Revenue",   f"₹{k.get('closed_won_value', 0):,}")
junk_pct = k.get('junk_pct', 0)
c7.metric("Lead Junk %",   f"{junk_pct}%",
          delta="Lower is better", delta_color="inverse")

st.divider()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Summary",
    "🎯 Lead Intelligence",
    "💰 Deal Pipeline",
    "⚙️ System Health",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Key Findings Strip ────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Key Findings — Today at a Glance</div>", unsafe_allow_html=True)

    _findings = []
    # Finding 1: Daily lead pacing
    _leads_today = ps.get('leads_today', 0)
    _weekly_avg  = round(ps.get('leads_week', 0) / 7, 1) if ps.get('leads_week', 0) else 0
    if _weekly_avg:
        _lead_dir = "ahead of" if _leads_today >= _weekly_avg else "behind"
        _findings.append(
            f"📈 **Lead Pacing:** {_leads_today} leads captured today vs. a 7-day daily average of {_weekly_avg:.0f}. "
            f"Inbound volume is {_lead_dir} the weekly run-rate."
        )
    # Finding 2: Junk rate signal
    _junk = k.get('junk_pct', 0)
    if _junk:
        _junk_cls = "🟢" if _junk < 20 else ("🟡" if _junk < 35 else "🔴")
        _findings.append(
            f"{_junk_cls} **Lead Quality:** {_junk}% of all-time leads are junk/unqualified. "
            f"{'This is within a healthy range — marketing spend is well targeted.' if _junk < 20 else 'Quality is degrading — review lead qualification criteria and source targeting immediately.'}"
        )
    # Finding 3: rep overload check
    _owner_dict = d.get('owner_leads', {})
    if _owner_dict:
        _rep_avg = sum(_owner_dict.values()) / len(_owner_dict)
        _overloaded_reps = [r for r, cnt in _owner_dict.items() if cnt > _rep_avg * 2]
        if _overloaded_reps:
            _findings.append(
                f"🔴 **Rep Overload Risk:** {', '.join(_overloaded_reps)} {'is' if len(_overloaded_reps)==1 else 'are'} "
                f"holding more than 2× the team average of {_rep_avg:.0f} leads. "
                f"Overloaded reps are at risk of slow follow-up and lead decay."
            )
    # Finding 4: Open pipeline context
    _pipeline_val = k.get('open_pipeline_value', 0)
    _won_val      = k.get('closed_won_value', 0)
    if _pipeline_val:
        _conversion_insight = round((_won_val / (_won_val + _pipeline_val)) * 100) if (_won_val + _pipeline_val) else 0
        _findings.append(
            f"💰 **Pipeline Health:** ₹{_pipeline_val:,} in open pipeline with ₹{_won_val:,} already won. "
            f"Current conversion-to-won rate stands at {_conversion_insight}%."
        )

    if _findings:
        with st.container(border=True):
            for i, finding in enumerate(_findings, 1):
                st.markdown(f"{i}. {finding}")
    
    st.divider()

    # ── Period KPIs ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Period Performance</div>", unsafe_allow_html=True)
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Leads Today",         f"{ps.get('leads_today', 0):,}")
    p2.metric("Leads This Week",     f"{ps.get('leads_week', 0):,}")
    p3.metric("Leads This Month",    f"{ps.get('leads_month', 0):,}")
    p4.metric("Pipeline Today",      f"₹{ps.get('pipeline_today', 0):,}")
    p5.metric("Pipeline This Week",  f"₹{ps.get('pipeline_week', 0):,}")
    p6.metric("Pipeline This Month", f"₹{ps.get('pipeline_month', 0):,}")

    st.divider()

    # ── AI Executive Briefing ─────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Today's AI Executive Briefing</div>", unsafe_allow_html=True)
    ai_dates = d["ai_dates"]
    if ai_dates:
        col_date, _ = st.columns([1, 3])
        with col_date:
            selected_date = st.selectbox("Report Date", ai_dates, index=0, label_visibility="collapsed")
        briefing = database_client.get_briefing_by_date(selected_date)
        if briefing:
            with st.container(border=True):
                st.markdown(briefing)
        else:
            st.warning("No briefing found for this date.")
    else:
        st.markdown("<div class='insight-card'>No AI briefings logged yet. Run <code>run_daily_sync.py</code> to generate one.</div>", unsafe_allow_html=True)

    st.divider()

    # ── Charts Row: Lead Trend + Pipeline Stages ──────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        trend = d["trend"]
        if trend:
            df_trend = pd.DataFrame(sorted(trend.items()), columns=["Date", "New Leads"])
            df_trend["Date"] = pd.to_datetime(df_trend["Date"])
            avg_leads = df_trend["New Leads"].mean()
            fig = px.area(
                df_trend, x="Date", y="New Leads",
                title="New Lead Volume — Last 30 Days",
                line_shape="spline",
            )
            fig.update_traces(line_color="#6366F1", fillcolor="rgba(99,102,241,0.12)")
            fig.add_hline(y=avg_leads, line_dash="dot", line_color="#9CA3AF",
                          annotation_text=f"30-day avg: {avg_leads:.0f}")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            # Insight
            recent_days = df_trend.tail(3)["New Leads"].mean()
            prev_3_days = df_trend.iloc[-6:-3]["New Leads"].mean() if len(df_trend) >= 6 else avg_leads
            momentum = "improving" if recent_days > prev_3_days else "declining"
            trend_dir = "above" if recent_days > avg_leads else "below"
            color_class = "success-card" if trend_dir == "above" else "warning-card"
            st.markdown(
                f"<div class='{color_class}'>The last 3 days averaged <b>{recent_days:.0f} leads/day</b> — "
                f"<b>{abs(recent_days - avg_leads):.0f} {'more' if trend_dir=='above' else 'fewer'}</b> than the 30-day average of <b>{avg_leads:.0f}</b>. "
                f"Momentum is <b>{momentum}</b> compared to the prior 3-day window ({prev_3_days:.0f} avg). "
                f"{'No action needed — pipeline intake is healthy.' if trend_dir=='above' else 'Run a quick audit of active ad campaigns to identify what changed.'}"
                f"</div>", unsafe_allow_html=True)
        else:
            st.info("No lead trend data available yet.")

    with col_b:
        pipeline_statuses = d["pipeline"].get("pipeline_statuses", {})
        if pipeline_statuses:
            junk_statuses = {"Junk Lead", "Not Qualified", "Not Qualified Lead"}
            df_stages = (
                pd.DataFrame(list(pipeline_statuses.items()), columns=["Stage", "Count"])
                  .sort_values("Count", ascending=True)
            )
            df_stages["Color"] = df_stages["Stage"].apply(
                lambda s: "#EF553B" if s in junk_statuses else
                          "#00CC96" if "Won" in s else "#6366F1"
            )
            fig = px.bar(
                df_stages, x="Count", y="Stage", orientation="h",
                title="Pipeline Stage Breakdown",
                color="Color", color_discrete_map="identity",
            )
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            # Insight
            top_stage = max(pipeline_statuses, key=pipeline_statuses.get)
            junk_total = sum(v for k_, v in pipeline_statuses.items() if k_ in junk_statuses)
            total_all  = sum(pipeline_statuses.values())
            junk_share = round((junk_total / total_all) * 100) if total_all else 0
            in_pipeline = total_all - junk_total
            st.markdown(
                f"<div class='insight-card'><b>{top_stage}</b> has the most records at <b>{pipeline_statuses[top_stage]:,}</b>. "
                f"Across the entire funnel, <b>{in_pipeline:,}</b> leads are actively progressing "
                f"while <b>{junk_total:,} ({junk_share}%) are junk/unqualified</b> — "
                f"{'quality is healthy; marketing spend is translating well into qualified pipeline.' if junk_share < 20 else 'this level of junk is eroding pipeline efficiency. A source-level targeting review is recommended.'}"
                f"</div>", unsafe_allow_html=True)
        else:
            st.info("No pipeline data available.")

    st.divider()

    # ── Row 2: Source Donut + Won vs Lost ─────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        src = d["pipeline"].get("source_breakdown", {})
        if src:
            df_src = pd.DataFrame(list(src.items()), columns=["Source", "Count"])
            top_src = df_src.sort_values("Count", ascending=False).iloc[0]
            fig = px.pie(df_src, values="Count", names="Source",
                         title="Lead Source Distribution (Today)", hole=0.45)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            total_sources = len(src)
            second_src = df_src.sort_values("Count", ascending=False).iloc[1] if total_sources > 1 else None
            top_share = round((top_src['Count'] / df_src['Count'].sum()) * 100)
            st.markdown(
                f"<div class='insight-card'><b>{top_src['Source']}</b> dominates today's inbound with "
                f"<b>{top_src['Count']} leads ({top_share}% of total)</b>. "
                f"{f'Second-place is <b>{second_src["Source"]}</b> with <b>{second_src["Count"]}</b> leads.' if second_src is not None else ''} "
                f"Heavy reliance on a single channel creates risk — if this source underperforms tomorrow, overall volume drops sharply.</div>",
                unsafe_allow_html=True)
        else:
            st.info("No source data for today.")

    with col_d:
        wl = d["won_vs_lost"]
        if wl["won_count"] or wl["lost_count"]:
            total = wl["won_count"] + wl["lost_count"]
            win_rate = round((wl["won_count"] / total) * 100) if total else 0
            df_wl = pd.DataFrame([
                {"Outcome": "Closed Won",  "Count": wl["won_count"],  "Value (₹)": wl["won_value"]},
                {"Outcome": "Closed Lost", "Count": wl["lost_count"], "Value (₹)": wl["lost_value"]},
            ])
            fig = px.bar(df_wl, x="Outcome", y="Count", color="Outcome", text="Count",
                         title="Won vs Lost Deals",
                         color_discrete_map={"Closed Won": "#10B981", "Closed Lost": "#EF553B"})
            fig.update_traces(textposition="outside")
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            color_class = "success-card" if win_rate >= 50 else "warning-card"
            revenue_at_risk = wl['lost_value']
            st.markdown(
                f"<div class='{color_class}'>Win rate stands at <b>{win_rate}%</b> across {total} closed deals. "
                f"The team has converted <b>₹{wl['won_value']:,}</b> in revenue, but left <b>₹{revenue_at_risk:,} on the table</b> through lost deals. "
                f"{'Conversion is strong — focus on increasing deal volume to scale revenue.' if win_rate >= 50 else 'Win rate is below 50%. Strategy review on objection handling and deal qualification is recommended.'}"
                f"</div>", unsafe_allow_html=True)
        else:
            st.info("No closed deals yet.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LEAD INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-label'>Lead Status & Quality Analysis</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        statuses = d["lead_statuses"]
        if statuses:
            df_st = (pd.DataFrame(list(statuses.items()), columns=["Status", "Count"])
                       .sort_values("Count", ascending=True))
            fig = px.bar(df_st, x="Count", y="Status", orientation="h",
                         title="Lead Status Breakdown (All Time)",
                         color="Count", color_continuous_scale="Blues")
            fig.update_coloraxes(showscale=False)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            # Insight
            junk_keys = ["Junk Lead", "Not Qualified", "Not Qualified Lead"]
            junk_count = sum(statuses.get(k_, 0) for k_ in junk_keys)
            total_leads = sum(statuses.values())
            top_status = max(statuses, key=statuses.get)
            st.markdown(
                f"<div class='insight-card'><b>{top_status}</b> is the most common lead status with "
                f"<b>{statuses[top_status]:,}</b> leads. "
                f"<b>{junk_count:,}</b> leads ({round(junk_count/total_leads*100) if total_leads else 0}%) "
                f"are classified as junk or unqualified — these are not converting into pipeline value.</div>",
                unsafe_allow_html=True)

    with col_b:
        owner_leads = d["owner_leads"]
        if owner_leads:
            df_ow = (pd.DataFrame(list(owner_leads.items()), columns=["Sales Rep", "Leads Assigned"])
                       .sort_values("Leads Assigned", ascending=True))
            avg_load = df_ow["Leads Assigned"].mean()
            df_ow["Color"] = df_ow["Leads Assigned"].apply(
                lambda x: "#EF553B" if x > avg_load * 2 else "#6366F1"
            )
            fig = px.bar(df_ow, x="Leads Assigned", y="Sales Rep", orientation="h",
                         title="Sales Rep Lead Workload",
                         color="Color", color_discrete_map="identity")
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            overloaded = df_ow[df_ow["Leads Assigned"] > avg_load * 2]["Sales Rep"].tolist()
            if overloaded:
                st.markdown(
                    f"<div class='warning-card'>⚠️ <b>{', '.join(overloaded)}</b> "
                    f"{'is' if len(overloaded) == 1 else 'are'} carrying more than 2× the average lead load "
                    f"({avg_load:.0f} avg). This risks slow follow-up and deal decay. Consider redistributing leads.</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div class='success-card'>Lead distribution is balanced across reps. Average load is <b>{avg_load:.0f} leads/rep</b>.</div>",
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='section-label'>Marketing Channel Quality</div>", unsafe_allow_html=True)

    sq = d["source_quality"]
    if sq:
        # Stacked bar
        q_rows = []
        for src, m in sq.items():
            q_rows.append({"Source": src, "Status": "In Pipeline", "Count": m["in_pipeline"]})
            q_rows.append({"Source": src, "Status": "Junk / Unqualified", "Count": m["junk_or_unqualified"]})
        df_q = pd.DataFrame(q_rows)
        fig = px.bar(df_q, x="Source", y="Count", color="Status", barmode="stack",
                     title="Channel Quality — Junk vs Pipeline per Source",
                     color_discrete_map={"In Pipeline": "#10B981", "Junk / Unqualified": "#EF553B"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Auto-generate insight from the source matrix
        best_src  = max(sq, key=lambda s: sq[s].get("in_pipeline", 0))
        worst_src = max(sq, key=lambda s: sq[s].get("junk_or_unqualified", 0))
        st.markdown(
            f"<div class='insight-card'><b>{best_src}</b> is the top-performing channel with "
            f"<b>{sq[best_src]['in_pipeline']}</b> leads in pipeline. "
            f"<b>{worst_src}</b> produces the most junk ({sq[worst_src]['junk_or_unqualified']} unqualified leads) "
            f"— review this channel's targeting criteria.</div>", unsafe_allow_html=True)

        # Bubble
        for src in sq:
            total = sq[src].get("total_leads", 0)
            junk  = sq[src].get("junk_or_unqualified", 0)
            sq[src]["junk_pct"] = round((junk / total) * 100) if total else 0

        df_bubble = pd.DataFrame([
            {"Source": src, "Total Leads": m["total_leads"], "Junk %": m["junk_pct"], "In Pipeline": m["in_pipeline"]}
            for src, m in sq.items()
        ])
        fig2 = px.scatter(
            df_bubble, x="Source", y="Junk %", size="Total Leads",
            color="Junk %", color_continuous_scale=["#10B981", "#F59E0B", "#EF553B"],
            hover_data=["Total Leads", "In Pipeline"],
            title="Lead Volume vs Junk % — Bubble View",
            size_max=60,
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📄 Raw Source Quality Table"):
            display_rows = [
                {"Source": src, "Total Leads": m["total_leads"], "In Pipeline": m["in_pipeline"],
                 "Junk / Unqualified": m["junk_or_unqualified"], "Junk %": f"{m['junk_pct']}%"}
                for src, m in sq.items()
            ]
            st.dataframe(pd.DataFrame(display_rows).sort_values("Total Leads", ascending=False),
                         use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DEAL PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-label'>Deal Stage Breakdown</div>", unsafe_allow_html=True)

    deal_stages = d["deal_stages"]
    col_a, col_b = st.columns(2)

    with col_a:
        if deal_stages:
            df_stages = pd.DataFrame([
                {"Stage": s, "Deals": m["count"], "Value (₹)": round(m["value"])}
                for s, m in deal_stages.items()
            ]).sort_values("Deals", ascending=True)
            fig = px.bar(df_stages, x="Deals", y="Stage", orientation="h",
                         title="Deal Count by Stage",
                         color="Deals", color_continuous_scale="Purples")
            fig.update_coloraxes(showscale=False)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            top_stage = max(deal_stages, key=lambda s: deal_stages[s]["count"])
            st.markdown(
                f"<div class='insight-card'><b>{top_stage}</b> has the highest deal concentration "
                f"({deal_stages[top_stage]['count']} deals). If this is an early stage, it indicates strong top-of-funnel pipeline.</div>",
                unsafe_allow_html=True)

    with col_b:
        if deal_stages:
            df_val = pd.DataFrame([
                {"Stage": s, "Value (₹)": round(m["value"])}
                for s, m in deal_stages.items()
            ]).sort_values("Value (₹)", ascending=True)
            fig = px.bar(df_val, x="Value (₹)", y="Stage", orientation="h",
                         title="Pipeline ₹ Value by Stage",
                         color="Value (₹)", color_continuous_scale="Greens")
            fig.update_coloraxes(showscale=False)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            top_val_stage = max(deal_stages, key=lambda s: deal_stages[s]["value"])
            st.markdown(
                f"<div class='insight-card'>The highest ₹ concentration is at <b>{top_val_stage}</b> "
                f"(₹{deal_stages[top_val_stage]['value']:,.0f}). Prioritise closing deals in this stage first.</div>",
                unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='section-label'>Sales Rep Performance</div>", unsafe_allow_html=True)

    deal_owners = d["deal_by_owner"]
    if deal_owners:
        df_owner = pd.DataFrame([
            {"Sales Rep": o, "Open Pipeline (₹)": round(m["open_value"]),
             "Won Revenue (₹)": round(m["won_value"]), "Total Deals": m["deal_count"]}
            for o, m in deal_owners.items()
        ]).sort_values("Open Pipeline (₹)", ascending=False)

        fig = px.bar(
            df_owner.melt(id_vars="Sales Rep", value_vars=["Open Pipeline (₹)", "Won Revenue (₹)"],
                          var_name="Category", value_name="Value (₹)"),
            x="Sales Rep", y="Value (₹)", color="Category", barmode="group",
            title="Deal Value by Rep — Open Pipeline vs Won Revenue",
            color_discrete_map={"Open Pipeline (₹)": "#6366F1", "Won Revenue (₹)": "#10B981"}
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        top_rep = df_owner.iloc[0]
        st.markdown(
            f"<div class='insight-card'><b>{top_rep['Sales Rep']}</b> holds the largest open pipeline "
            f"(₹{top_rep['Open Pipeline (₹)']:,}). Reps with high open pipeline but low won revenue may need "
            f"coaching on closing techniques.</div>", unsafe_allow_html=True)

        with st.expander("📄 Raw Rep Performance Table"):
            st.dataframe(df_owner, use_container_width=True)

    st.divider()
    st.markdown("<div class='section-label'>Deals Closing in the Next 30 Days</div>", unsafe_allow_html=True)

    closing = d["closing_soon"]
    if closing:
        df_close = pd.DataFrame(closing)
        df_close.rename(columns={
            "deal_name": "Deal", "stage": "Stage",
            "amount": "Amount (₹)", "owner": "Owner", "closed_time": "Close Date"
        }, inplace=True)
        df_close["Amount (₹)"] = df_close["Amount (₹)"].apply(lambda x: f"₹{x:,.0f}" if x else "₹0")
        st.markdown(
            f"<div class='warning-card'>⏰ <b>{len(closing)} deal(s)</b> are closing within 30 days. "
            f"These require immediate attention from the assigned reps.</div>", unsafe_allow_html=True)
        st.dataframe(df_close, use_container_width=True)
    else:
        st.markdown("<div class='success-card'>✅ No open deals with a deadline in the next 30 days.</div>",
                    unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SYSTEM HEALTH
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-label'>Data Sync Health</div>", unsafe_allow_html=True)

    sync_history = d["sync_history"]
    if sync_history:
        col_a, col_b = st.columns([1, 2])

        with col_a:
            last = sync_history[0]
            last_time    = last.get("sync_time", "Unknown")[:19].replace("T", " ")
            last_records = last.get("records_fetched", 0)
            st.metric("Last Sync", last_time)
            st.metric("Records in Last Sync", f"{last_records:,}")

            total_syncs = len(sync_history)
            st.metric("Sync Runs (Logged)", total_syncs)

            st.markdown(
                f"<div class='success-card'>System is syncing regularly. Last run ingested "
                f"<b>{last_records:,}</b> records from Zoho CRM.</div>", unsafe_allow_html=True)

        with col_b:
            df_sync = pd.DataFrame(sync_history)
            df_sync["sync_time"] = df_sync["sync_time"].str[:16].str.replace("T", " ")
            df_sync.rename(columns={"sync_time": "Timestamp", "records_fetched": "Records", "status": "Status"}, inplace=True)
            fig = px.bar(df_sync, x="Timestamp", y="Records",
                         title="Records Synced Per Run",
                         color="Records", color_continuous_scale="Blues")
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(tickangle=45)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("<div class='section-label'>Last 10 Sync Logs</div>", unsafe_allow_html=True)
        st.dataframe(df_sync[["Timestamp", "Records", "Status"]], use_container_width=True)
    else:
        st.info("No sync logs found. Run `run_daily_sync.py` to generate logs.")

    st.divider()
    st.markdown("<div class='section-label'>Connected Data Sources</div>", unsafe_allow_html=True)
    src_col1, src_col2, src_col3, src_col4 = st.columns(4)
    src_col1.success("✅ leads_raw")
    src_col2.success("✅ crm_deals")
    src_col3.success("✅ crm_contacts")
    src_col4.success("✅ crm_accounts")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.caption("Powered by Zoho CRM · Supabase Cloud PostgreSQL · Streamlit · Llama 3.2 (Local AI)")
