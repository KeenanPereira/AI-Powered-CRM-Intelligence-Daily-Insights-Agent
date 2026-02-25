-- ────────────────────────────────────────────────────────────────────────
-- AHA SMART HOMES: POSTGRESQL AGGREGATION RPC BACKEND
-- This file pushes all heavy data aggregations from Python down to the 
-- Supabase Postgres layer. Run this entire script in the SQL Editor.
-- ────────────────────────────────────────────────────────────────────────

-- 1. Get Overview KPIs
CREATE OR REPLACE FUNCTION get_overview_kpis()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result json;
    t_leads int;
    t_deals int;
    t_contacts int;
    t_accounts int;
    open_pipe float;
    won_rev float;
    won_deals int;
    junk_total int;
    junk_pct int;
BEGIN
    SELECT count(*) INTO t_leads FROM leads_raw;
    SELECT count(*) INTO t_deals FROM crm_deals;
    SELECT count(*) INTO t_contacts FROM crm_contacts;
    SELECT count(*) INTO t_accounts FROM crm_accounts;
    
    SELECT coalesce(sum(amount), 0) INTO open_pipe FROM crm_deals WHERE stage != 'Closed Lost' AND stage != 'Closed Won';
    SELECT coalesce(sum(amount), 0), count(*) INTO won_rev, won_deals FROM crm_deals WHERE stage = 'Closed Won';
    
    SELECT count(*) INTO junk_total FROM leads_raw WHERE lead_status IN ('Junk Lead', 'Not Qualified', 'Not Qualified Lead');
    IF t_leads > 0 THEN
        junk_pct := round((junk_total::float / t_leads::float) * 100);
    ELSE
        junk_pct := 0;
    END IF;

    SELECT json_build_object(
        'total_leads', t_leads,
        'total_deals', t_deals,
        'total_contacts', t_contacts,
        'total_accounts', t_accounts,
        'open_pipeline_value', open_pipe,
        'closed_won_value', won_rev,
        'closed_won_deals', won_deals,
        'junk_pct', junk_pct
    ) INTO result;
    
    RETURN result;
END;
$$;

-- 2. Get Pipeline Period Stats (Today/Week/Month)
CREATE OR REPLACE FUNCTION get_pipeline_period_stats()
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH periods AS (
        SELECT 
            to_char(CURRENT_DATE, 'YYYY-MM-DD"T"00:00:00') AS today_start,
            to_char(date_trunc('week', CURRENT_DATE), 'YYYY-MM-DD"T"00:00:00') AS week_start,
            to_char(date_trunc('month', CURRENT_DATE), 'YYYY-MM-DD"T"00:00:00') AS month_start
    )
    SELECT json_build_object(
        'leads_today', (SELECT count(*) FROM leads_raw, periods WHERE created_time >= today_start),
        'leads_week', (SELECT count(*) FROM leads_raw, periods WHERE created_time >= week_start),
        'leads_month', (SELECT count(*) FROM leads_raw, periods WHERE created_time >= month_start),
        'pipeline_today', (SELECT coalesce(sum(amount), 0) FROM crm_deals, periods WHERE created_time >= today_start AND stage != 'Closed Lost'),
        'pipeline_week', (SELECT coalesce(sum(amount), 0) FROM crm_deals, periods WHERE created_time >= week_start AND stage != 'Closed Lost'),
        'pipeline_month', (SELECT coalesce(sum(amount), 0) FROM crm_deals, periods WHERE created_time >= month_start AND stage != 'Closed Lost')
    );
$$;

-- 3. Get Lead Volume Trend 
-- (Accepts days integer dynamically from Python)
CREATE OR REPLACE FUNCTION get_lead_volume_trend(days int DEFAULT 30)
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH daily_counts AS (
        SELECT substring(created_time from 1 for 10) AS day, count(*) AS cnt
        FROM leads_raw
        WHERE created_time >= to_char(CURRENT_DATE - (days || ' days')::interval, 'YYYY-MM-DD"T"00:00:00')
        GROUP BY 1
    )
    SELECT json_object_agg(day, cnt)
    FROM daily_counts;
$$;

-- 4. Get Lead Status Breakdown
CREATE OR REPLACE FUNCTION get_lead_status_breakdown()
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH status_counts AS (
        SELECT coalesce(lead_status, 'Unknown') AS status, count(*) AS cnt 
        FROM leads_raw GROUP BY 1
    )
    SELECT json_object_agg(status, cnt) FROM status_counts;
$$;

-- 5. Get Owner Lead Distribution
CREATE OR REPLACE FUNCTION get_owner_lead_distribution()
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH owner_counts AS (
        SELECT coalesce(owner, 'Unassigned') AS rep, count(*) AS cnt 
        FROM leads_raw GROUP BY 1
    )
    SELECT json_object_agg(rep, cnt) FROM owner_counts;
$$;

-- 6. Get Deal Stage Breakdown
CREATE OR REPLACE FUNCTION get_deal_stage_breakdown()
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH stage_aggs AS (
        SELECT coalesce(stage, 'Unknown') AS stg, count(*) AS cnt, coalesce(sum(amount), 0) AS val
        FROM crm_deals GROUP BY 1
    )
    SELECT json_object_agg(stg, json_build_object('count', cnt, 'value', val)) FROM stage_aggs;
$$;

-- 7. Get Deal Value By Owner (Open vs Won)
CREATE OR REPLACE FUNCTION get_deal_value_by_owner()
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH owner_aggs AS (
        SELECT 
            coalesce(owner, 'Unassigned') AS rep,
            count(*) AS deal_count,
            coalesce(sum(amount) FILTER (WHERE stage = 'Closed Won'), 0) AS won_value,
            coalesce(sum(amount) FILTER (WHERE stage != 'Closed Lost' AND stage != 'Closed Won'), 0) AS open_value
        FROM crm_deals
        GROUP BY 1
    )
    SELECT json_object_agg(rep, json_build_object('deal_count', deal_count, 'won_value', won_value, 'open_value', open_value)) FROM owner_aggs;
$$;

-- 8. Get Deals Closing Soon
CREATE OR REPLACE FUNCTION get_deals_closing_soon(days int DEFAULT 30)
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT coalesce(json_agg(row_to_json(t)), '[]'::json)
    FROM (
        SELECT deal_name, stage, amount, owner, closed_time
        FROM crm_deals 
        WHERE closed_time >= to_char(CURRENT_DATE, 'YYYY-MM-DD')
          AND closed_time <= to_char(CURRENT_DATE + (days || ' days')::interval, 'YYYY-MM-DD')
          AND stage != 'Closed Lost' 
          AND stage != 'Closed Won'
        ORDER BY closed_time
    ) t;
$$;

-- 9. Get Won vs Lost
CREATE OR REPLACE FUNCTION get_won_vs_lost()
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH aggs AS (
        SELECT 
            count(*) FILTER (WHERE stage = 'Closed Won') AS won_count,
            count(*) FILTER (WHERE stage = 'Closed Lost') AS lost_count,
            coalesce(sum(amount) FILTER (WHERE stage = 'Closed Won'), 0) AS won_value,
            coalesce(sum(amount) FILTER (WHERE stage = 'Closed Lost'), 0) AS lost_value
        FROM crm_deals
    )
    SELECT json_build_object('won_count', won_count, 'lost_count', lost_count, 'won_value', won_value, 'lost_value', lost_value) FROM aggs;
$$;

-- 10. Get Contact & Account Breakdown (Combined)
CREATE OR REPLACE FUNCTION get_contact_and_account_breakdown()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    contact_owners json;
    industries json;
BEGIN
    SELECT json_object_agg(rep, cnt) INTO contact_owners FROM (
        SELECT coalesce(owner, 'Unassigned') AS rep, count(*) AS cnt FROM crm_contacts GROUP BY 1
    ) t;
    
    SELECT json_object_agg(ind, cnt) INTO industries FROM (
        SELECT coalesce(industry, 'Unknown') AS ind, count(*) AS cnt FROM crm_accounts GROUP BY 1
    ) t2;
    
    RETURN json_build_object('contact_owners', coalesce(contact_owners, '{}'::json), 'industries', coalesce(industries, '{}'::json));
END;
$$;

-- 11. Source Quality Matrix (All Time)
CREATE OR REPLACE FUNCTION get_source_quality_all_time()
RETURNS json
LANGUAGE sql
SECURITY DEFINER
AS $$
    WITH src_aggs AS (
        SELECT 
            coalesce(lead_source, 'Unknown') AS src,
            count(*) AS total_leads,
            count(*) FILTER (WHERE lead_status IN ('Junk Lead', 'Not Qualified', 'Not Qualified Lead')) AS junk_or_unqualified,
            count(*) FILTER (WHERE lead_status NOT IN ('Junk Lead', 'Not Qualified', 'Not Qualified Lead')) AS in_pipeline
        FROM leads_raw
        GROUP BY 1
    )
    SELECT json_object_agg(src, json_build_object(
        'total_leads', total_leads, 
        'junk_or_unqualified', junk_or_unqualified, 
        'in_pipeline', in_pipeline,
        'junk_pct', CASE WHEN total_leads > 0 THEN round((junk_or_unqualified::float / total_leads::float) * 100) ELSE 0 END
    )) FROM src_aggs;
$$;

-- 12. Advanced Analytics (The giant dictionary function)
CREATE OR REPLACE FUNCTION get_advanced_analytics(target_date_iso text DEFAULT NULL)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    target_date date;
    target_start text;
    target_end text;
    seven_days_ago text;
    new_leads_today int;
    seven_day_avg int;
    pct_change float;
    pct_change_str text;
    pipe_status json;
    src_brk json;
    pipe_val float;
    qual_mat json;
    rep_mat json;
    result json;
BEGIN
    IF target_date_iso IS NULL THEN
        target_date := CURRENT_DATE;
    ELSE
        target_date := target_date_iso::date;
    END IF;
    
    target_start := to_char(target_date, 'YYYY-MM-DD"T"00:00:00');
    target_end := to_char(target_date, 'YYYY-MM-DD"T"23:59:59');
    seven_days_ago := to_char(target_date - interval '7 days', 'YYYY-MM-DD"T"00:00:00');
    
    -- 1. Leads
    SELECT count(*) INTO new_leads_today FROM leads_raw WHERE created_time >= target_start AND created_time <= target_end;
    SELECT round(count(*) / 7.0) INTO seven_day_avg FROM leads_raw WHERE created_time >= seven_days_ago AND created_time < target_start;
    
    IF coalesce(seven_day_avg, 0) = 0 THEN
        pct_change_str := '0%';
    ELSE
        pct_change := ((new_leads_today - seven_day_avg)::float / seven_day_avg::float) * 100;
        IF pct_change > 0 THEN pct_change_str := '+' || round(pct_change)::text || '%';
        ELSE pct_change_str := round(pct_change)::text || '%'; END IF;
    END IF;
    
    -- 2. Pipeline Statuses
    SELECT json_object_agg(st, cnt) INTO pipe_status FROM (
        SELECT st, sum(cnt) as cnt FROM (
            SELECT lead_status AS st, count(*) AS cnt FROM leads_raw GROUP BY 1
            UNION ALL
            SELECT stage AS st, count(*) AS cnt FROM crm_deals GROUP BY 1
        ) combined GROUP BY 1
    ) t;

    -- 3. Source Breakdown Today
    SELECT json_object_agg(src, cnt) INTO src_brk FROM (
        SELECT src, sum(cnt) as cnt FROM (
            SELECT coalesce(lead_source, 'Unknown') AS src, count(*) AS cnt FROM leads_raw WHERE created_time >= target_start AND created_time <= target_end GROUP BY 1
            UNION ALL
            SELECT coalesce(source, 'Unknown') AS src, count(*) AS cnt FROM crm_deals WHERE created_time >= target_start AND created_time <= target_end GROUP BY 1
        ) combined GROUP BY 1
    ) t;
    
    -- 4. Pipeline Value
    SELECT coalesce(sum(amount), 0) INTO pipe_val FROM crm_deals WHERE stage != 'Closed Lost';
    
    -- 5. Quality Matrix
    SELECT json_object_agg(src, json_build_object('total_leads', t, 'junk_or_unqualified', j, 'in_pipeline', p, 'junk_pct', CASE WHEN t>0 THEN round((j::float/t::float)*100)::text||'%' ELSE '0%' END)) INTO qual_mat FROM (
        SELECT coalesce(lead_source, 'Unknown') AS src, count(*) AS t, count(*) FILTER(WHERE lead_status IN ('Junk Lead', 'Not Qualified')) AS j, count(*) FILTER(WHERE lead_status NOT IN ('Junk Lead', 'Not Qualified')) AS p
        FROM leads_raw WHERE created_time >= target_start AND created_time <= target_end GROUP BY 1
    ) t_q;
    
    -- 6. Rep Matrix
    SELECT json_object_agg(owner, json_build_object('active_leads', leads, 'total_pipeline_value', rev)) INTO rep_mat FROM (
        SELECT coalesce(d.owner, l.owner, 'Unassigned') AS owner,
               coalesce(l.cnt, 0) + coalesce(d.cnt, 0) AS leads,
               coalesce(d.rev, 0) as rev
        FROM 
            (SELECT owner, count(*) as cnt, sum(amount) as rev FROM crm_deals WHERE stage != 'Closed Lost' GROUP BY 1) d
        FULL OUTER JOIN 
            (SELECT owner, count(*) as cnt FROM leads_raw GROUP BY 1) l
        ON d.owner = l.owner
    ) t_r;
    
    SELECT json_build_object(
        'new_leads_today', new_leads_today,
        'seven_day_avg', coalesce(seven_day_avg, 0),
        'percent_change_leads', pct_change_str,
        'pipeline_statuses', coalesce(pipe_status, '{}'::json),
        'source_breakdown', coalesce(src_brk, '{}'::json),
        'pipeline_value', coalesce(pipe_val, 0),
        'source_quality_matrix', coalesce(qual_mat, '{}'::json),
        'rep_pipeline_matrix', coalesce(rep_mat, '{}'::json)
    ) INTO result;
    
    RETURN result;
END;
$$;
