-- ============================================================================
-- MRR vs Chat Volume Correlation Analysis SQL
-- ============================================================================
-- This script analyzes the correlation between Monthly Recurring Revenue (MRR)
-- and Intercom chat/conversation volume, outputting results to a new table.
--
-- Assumes tables:
--   - mrr_data (from MONTHLY_RECURRING_REVENUE.csv)
--   - conversations_data (from Intercom Conversations CSV)
-- ============================================================================

-- Step 1: Create monthly MRR aggregation table
-- ============================================================================
CREATE TABLE IF NOT EXISTS monthly_mrr_aggregated AS
SELECT 
    DATE_TRUNC('month', TO_DATE("Revenue Calendar Month", 'YYYY-MM-DD')) AS month,
    SUM("Mrr") AS total_mrr,
    COUNT(DISTINCT "Account Guid") AS account_count,
    AVG("Mrr") AS avg_mrr_per_account,
    MIN("Mrr") AS min_mrr,
    MAX("Mrr") AS max_mrr,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "Mrr") AS median_mrr
FROM mrr_data
WHERE "Mrr" IS NOT NULL 
    AND "Mrr" > 0
    AND "Revenue Calendar Month" IS NOT NULL
GROUP BY DATE_TRUNC('month', TO_DATE("Revenue Calendar Month", 'YYYY-MM-DD'))
ORDER BY month;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_monthly_mrr_month ON monthly_mrr_aggregated(month);


-- Step 2: Create monthly conversations aggregation table
-- ============================================================================
CREATE TABLE IF NOT EXISTS monthly_conversations_aggregated AS
SELECT 
    DATE_TRUNC('month', TO_TIMESTAMP("Conversation Created PT", 'MM/DD/YYYY HH24:MI:SS')) AS month,
    COUNT(*) AS total_conversations,
    COUNT(CASE WHEN LOWER("Intercom Chat Status") = 'closed' THEN 1 END) AS closed_conversations,
    COUNT(CASE WHEN LOWER("Intercom Chat Status") = 'open' THEN 1 END) AS open_conversations,
    COUNT(DISTINCT DATE(TO_TIMESTAMP("Conversation Created PT", 'MM/DD/YYYY HH24:MI:SS'))) AS days_with_conversations,
    ROUND(COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT DATE(TO_TIMESTAMP("Conversation Created PT", 'MM/DD/YYYY HH24:MI:SS'))), 0), 2) AS avg_daily_conversations,
    AVG("IR (s)") AS avg_initial_response_seconds,
    AVG("Waiting Time (s)") AS avg_waiting_time_seconds,
    COUNT(DISTINCT "User Org") AS unique_orgs,
    COUNT(DISTINCT "TSE Assigned to") AS unique_tse_count
FROM conversations_data
WHERE "Conversation Created PT" IS NOT NULL
GROUP BY DATE_TRUNC('month', TO_TIMESTAMP("Conversation Created PT", 'MM/DD/YYYY HH24:MI:SS'))
ORDER BY month;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_monthly_conv_month ON monthly_conversations_aggregated(month);


-- Step 3: Create joined monthly data table
-- ============================================================================
CREATE TABLE IF NOT EXISTS monthly_mrr_chat_joined AS
SELECT 
    COALESCE(m.month, c.month) AS month,
    COALESCE(m.total_mrr, 0) AS total_mrr,
    COALESCE(m.account_count, 0) AS account_count,
    COALESCE(m.avg_mrr_per_account, 0) AS avg_mrr_per_account,
    COALESCE(c.total_conversations, 0) AS total_conversations,
    COALESCE(c.closed_conversations, 0) AS closed_conversations,
    COALESCE(c.open_conversations, 0) AS open_conversations,
    COALESCE(c.avg_daily_conversations, 0) AS avg_daily_conversations,
    COALESCE(c.days_with_conversations, 0) AS days_with_conversations,
    CASE 
        WHEN COALESCE(m.total_mrr, 0) > 0 
        THEN COALESCE(c.total_conversations, 0) / m.total_mrr 
        ELSE 0 
    END AS conversations_per_mrr,
    CASE 
        WHEN COALESCE(m.account_count, 0) > 0 
        THEN COALESCE(c.total_conversations, 0)::NUMERIC / m.account_count 
        ELSE 0 
    END AS conversations_per_account
FROM monthly_mrr_aggregated m
FULL OUTER JOIN monthly_conversations_aggregated c ON m.month = c.month
WHERE COALESCE(m.total_mrr, 0) > 0 
    AND COALESCE(c.total_conversations, 0) > 0
ORDER BY month;

-- Add index
CREATE INDEX IF NOT EXISTS idx_mrr_chat_month ON monthly_mrr_chat_joined(month);


-- Step 4: Calculate correlation statistics and create results table
-- ============================================================================
CREATE TABLE IF NOT EXISTS mrr_chat_correlation_results AS
WITH stats AS (
    SELECT 
        COUNT(*) AS sample_size,
        AVG(total_mrr) AS mean_mrr,
        AVG(total_conversations) AS mean_conversations,
        AVG(avg_daily_conversations) AS mean_daily_conversations,
        AVG(account_count) AS mean_account_count,
        STDDEV(total_mrr) AS stddev_mrr,
        STDDEV(total_conversations) AS stddev_conversations,
        STDDEV(avg_daily_conversations) AS stddev_daily_conversations,
        STDDEV(account_count) AS stddev_account_count,
        MIN(total_mrr) AS min_mrr,
        MAX(total_mrr) AS max_mrr,
        MIN(total_conversations) AS min_conversations,
        MAX(total_conversations) AS max_conversations,
        MIN(avg_daily_conversations) AS min_daily_conversations,
        MAX(avg_daily_conversations) AS max_daily_conversations,
        MIN(month) AS start_month,
        MAX(month) AS end_month
    FROM monthly_mrr_chat_joined
),
correlation_calc AS (
    SELECT 
        -- Pearson correlation: MRR vs Total Conversations
        CASE 
            WHEN STDDEV(total_mrr) > 0 AND STDDEV(total_conversations) > 0
            THEN CORR(total_mrr, total_conversations)
            ELSE 0
        END AS mrr_vs_total_conversations_corr,
        
        -- Pearson correlation: MRR vs Daily Average
        CASE 
            WHEN STDDEV(total_mrr) > 0 AND STDDEV(avg_daily_conversations) > 0
            THEN CORR(total_mrr, avg_daily_conversations)
            ELSE 0
        END AS mrr_vs_daily_avg_corr,
        
        -- Pearson correlation: Account Count vs Conversations
        CASE 
            WHEN STDDEV(account_count) > 0 AND STDDEV(total_conversations) > 0
            THEN CORR(account_count, total_conversations)
            ELSE 0
        END AS account_count_vs_conversations_corr,
        
        -- R-squared values
        POWER(CASE 
            WHEN STDDEV(total_mrr) > 0 AND STDDEV(total_conversations) > 0
            THEN CORR(total_mrr, total_conversations)
            ELSE 0
        END, 2) AS mrr_vs_conversations_r_squared,
        
        POWER(CASE 
            WHEN STDDEV(total_mrr) > 0 AND STDDEV(avg_daily_conversations) > 0
            THEN CORR(total_mrr, avg_daily_conversations)
            ELSE 0
        END, 2) AS mrr_vs_daily_avg_r_squared
    FROM monthly_mrr_chat_joined
)
SELECT 
    s.sample_size,
    s.start_month,
    s.end_month,
    s.mean_mrr,
    s.mean_conversations,
    s.mean_daily_conversations,
    s.mean_account_count,
    s.stddev_mrr,
    s.stddev_conversations,
    s.stddev_daily_conversations,
    s.min_mrr,
    s.max_mrr,
    s.min_conversations,
    s.max_conversations,
    s.min_daily_conversations,
    s.max_daily_conversations,
    c.mrr_vs_total_conversations_corr,
    c.mrr_vs_daily_avg_corr,
    c.account_count_vs_conversations_corr,
    c.mrr_vs_conversations_r_squared,
    c.mrr_vs_daily_avg_r_squared,
    CASE 
        WHEN ABS(c.mrr_vs_total_conversations_corr) >= 0.9 THEN 'Very Strong'
        WHEN ABS(c.mrr_vs_total_conversations_corr) >= 0.7 THEN 'Strong'
        WHEN ABS(c.mrr_vs_total_conversations_corr) >= 0.5 THEN 'Moderate'
        WHEN ABS(c.mrr_vs_total_conversations_corr) >= 0.3 THEN 'Weak'
        ELSE 'Very Weak'
    END AS correlation_strength_mrr_total,
    CASE 
        WHEN ABS(c.mrr_vs_daily_avg_corr) >= 0.9 THEN 'Very Strong'
        WHEN ABS(c.mrr_vs_daily_avg_corr) >= 0.7 THEN 'Strong'
        WHEN ABS(c.mrr_vs_daily_avg_corr) >= 0.5 THEN 'Moderate'
        WHEN ABS(c.mrr_vs_daily_avg_corr) >= 0.3 THEN 'Weak'
        ELSE 'Very Weak'
    END AS correlation_strength_mrr_daily,
    -- Calculate ratios
    CASE 
        WHEN s.mean_mrr > 0 
        THEN s.mean_conversations / s.mean_mrr 
        ELSE 0 
    END AS conversations_per_mrr_ratio,
    CASE 
        WHEN s.mean_account_count > 0 
        THEN s.mean_conversations / s.mean_account_count 
        ELSE 0 
    END AS conversations_per_account_ratio,
    CURRENT_TIMESTAMP AS analysis_timestamp
FROM stats s
CROSS JOIN correlation_calc c;


-- Step 5: Create detailed monthly correlation breakdown table
-- ============================================================================
CREATE TABLE IF NOT EXISTS monthly_correlation_breakdown AS
SELECT 
    month,
    total_mrr,
    total_conversations,
    avg_daily_conversations,
    account_count,
    avg_mrr_per_account,
    conversations_per_mrr,
    conversations_per_account,
    -- Calculate z-scores for outlier detection
    (total_mrr - AVG(total_mrr) OVER()) / NULLIF(STDDEV(total_mrr) OVER(), 0) AS mrr_z_score,
    (total_conversations - AVG(total_conversations) OVER()) / NULLIF(STDDEV(total_conversations) OVER(), 0) AS conversations_z_score,
    -- Calculate month-over-month changes
    LAG(total_mrr) OVER (ORDER BY month) AS prev_month_mrr,
    LAG(total_conversations) OVER (ORDER BY month) AS prev_month_conversations,
    CASE 
        WHEN LAG(total_mrr) OVER (ORDER BY month) > 0
        THEN ((total_mrr - LAG(total_mrr) OVER (ORDER BY month)) / LAG(total_mrr) OVER (ORDER BY month)) * 100
        ELSE NULL
    END AS mrr_month_over_month_pct_change,
    CASE 
        WHEN LAG(total_conversations) OVER (ORDER BY month) > 0
        THEN ((total_conversations - LAG(total_conversations) OVER (ORDER BY month)) / LAG(total_conversations) OVER (ORDER BY month)) * 100
        ELSE NULL
    END AS conversations_month_over_month_pct_change,
    -- Rolling averages
    AVG(total_mrr) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS mrr_3_month_avg,
    AVG(total_conversations) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS conversations_3_month_avg,
    AVG(total_mrr) OVER (ORDER BY month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS mrr_12_month_avg,
    AVG(total_conversations) OVER (ORDER BY month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS conversations_12_month_avg
FROM monthly_mrr_chat_joined
ORDER BY month;


-- Step 6: Create summary view for easy querying
-- ============================================================================
CREATE OR REPLACE VIEW v_mrr_chat_correlation_summary AS
SELECT 
    'MRR vs Total Conversations' AS correlation_type,
    mrr_vs_total_conversations_corr AS correlation_coefficient,
    mrr_vs_conversations_r_squared AS r_squared,
    correlation_strength_mrr_total AS strength,
    sample_size,
    start_month,
    end_month
FROM mrr_chat_correlation_results
UNION ALL
SELECT 
    'MRR vs Daily Average' AS correlation_type,
    mrr_vs_daily_avg_corr AS correlation_coefficient,
    mrr_vs_daily_avg_r_squared AS r_squared,
    correlation_strength_mrr_daily AS strength,
    sample_size,
    start_month,
    end_month
FROM mrr_chat_correlation_results
UNION ALL
SELECT 
    'Account Count vs Conversations' AS correlation_type,
    account_count_vs_conversations_corr AS correlation_coefficient,
    NULL AS r_squared,
    CASE 
        WHEN ABS(account_count_vs_conversations_corr) >= 0.9 THEN 'Very Strong'
        WHEN ABS(account_count_vs_conversations_corr) >= 0.7 THEN 'Strong'
        WHEN ABS(account_count_vs_conversations_corr) >= 0.5 THEN 'Moderate'
        WHEN ABS(account_count_vs_conversations_corr) >= 0.3 THEN 'Weak'
        ELSE 'Very Weak'
    END AS strength,
    sample_size,
    start_month,
    end_month
FROM mrr_chat_correlation_results;


-- ============================================================================
-- QUERY EXAMPLES
-- ============================================================================

-- View correlation results summary
-- SELECT * FROM mrr_chat_correlation_results;

-- View correlation summary by type
-- SELECT * FROM v_mrr_chat_correlation_summary ORDER BY correlation_coefficient DESC;

-- View monthly breakdown with outliers
-- SELECT 
--     month,
--     total_mrr,
--     total_conversations,
--     mrr_z_score,
--     conversations_z_score,
--     CASE 
--         WHEN ABS(mrr_z_score) > 2 OR ABS(conversations_z_score) > 2 THEN 'Outlier'
--         ELSE 'Normal'
--     END AS outlier_flag
-- FROM monthly_correlation_breakdown
-- ORDER BY month;

-- View months with largest deviations
-- SELECT 
--     month,
--     total_mrr,
--     total_conversations,
--     mrr_month_over_month_pct_change,
--     conversations_month_over_month_pct_change,
--     ABS(mrr_month_over_month_pct_change - conversations_month_over_month_pct_change) AS deviation
-- FROM monthly_correlation_breakdown
-- WHERE mrr_month_over_month_pct_change IS NOT NULL
-- ORDER BY deviation DESC
-- LIMIT 10;

