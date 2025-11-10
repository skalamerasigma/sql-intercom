-- ============================================================================
-- MRR vs Chat Volume Correlation Analysis SQL (MySQL Version)
-- ============================================================================
-- MySQL-compatible version of the correlation analysis
-- ============================================================================

-- Step 1: Create monthly MRR aggregation table
-- ============================================================================
DROP TABLE IF EXISTS monthly_mrr_aggregated;
CREATE TABLE monthly_mrr_aggregated AS
SELECT 
    DATE_FORMAT(STR_TO_DATE(`Revenue Calendar Month`, '%Y-%m-%d'), '%Y-%m-01') AS month,
    SUM(`Mrr`) AS total_mrr,
    COUNT(DISTINCT `Account Guid`) AS account_count,
    AVG(`Mrr`) AS avg_mrr_per_account,
    MIN(`Mrr`) AS min_mrr,
    MAX(`Mrr`) AS max_mrr
FROM mrr_data
WHERE `Mrr` IS NOT NULL 
    AND `Mrr` > 0
    AND `Revenue Calendar Month` IS NOT NULL
GROUP BY DATE_FORMAT(STR_TO_DATE(`Revenue Calendar Month`, '%Y-%m-%d'), '%Y-%m-01')
ORDER BY month;

ALTER TABLE monthly_mrr_aggregated ADD INDEX idx_month (month);


-- Step 2: Create monthly conversations aggregation table
-- ============================================================================
DROP TABLE IF EXISTS monthly_conversations_aggregated;
CREATE TABLE monthly_conversations_aggregated AS
SELECT 
    DATE_FORMAT(STR_TO_DATE(`Conversation Created PT`, '%m/%d/%Y %H:%i:%s'), '%Y-%m-01') AS month,
    COUNT(*) AS total_conversations,
    SUM(CASE WHEN LOWER(`Intercom Chat Status`) = 'closed' THEN 1 ELSE 0 END) AS closed_conversations,
    SUM(CASE WHEN LOWER(`Intercom Chat Status`) = 'open' THEN 1 ELSE 0 END) AS open_conversations,
    COUNT(DISTINCT DATE(STR_TO_DATE(`Conversation Created PT`, '%m/%d/%Y %H:%i:%s'))) AS days_with_conversations,
    ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT DATE(STR_TO_DATE(`Conversation Created PT`, '%m/%d/%Y %H:%i:%s'))), 0), 2) AS avg_daily_conversations,
    AVG(`IR (s)`) AS avg_initial_response_seconds,
    AVG(`Waiting Time (s)`) AS avg_waiting_time_seconds,
    COUNT(DISTINCT `User Org`) AS unique_orgs,
    COUNT(DISTINCT `TSE Assigned to`) AS unique_tse_count
FROM conversations_data
WHERE `Conversation Created PT` IS NOT NULL
GROUP BY DATE_FORMAT(STR_TO_DATE(`Conversation Created PT`, '%m/%d/%Y %H:%i:%s'), '%Y-%m-01')
ORDER BY month;

ALTER TABLE monthly_conversations_aggregated ADD INDEX idx_month (month);


-- Step 3: Create joined monthly data table
-- ============================================================================
DROP TABLE IF EXISTS monthly_mrr_chat_joined;
CREATE TABLE monthly_mrr_chat_joined AS
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
        THEN COALESCE(c.total_conversations, 0) / m.account_count 
        ELSE 0 
    END AS conversations_per_account
FROM monthly_mrr_aggregated m
LEFT JOIN monthly_conversations_aggregated c ON m.month = c.month
WHERE COALESCE(m.total_mrr, 0) > 0 
    AND COALESCE(c.total_conversations, 0) > 0

UNION

SELECT 
    c.month,
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
        THEN COALESCE(c.total_conversations, 0) / m.account_count 
        ELSE 0 
    END AS conversations_per_account
FROM monthly_conversations_aggregated c
LEFT JOIN monthly_mrr_aggregated m ON c.month = m.month
WHERE COALESCE(m.total_mrr, 0) > 0 
    AND COALESCE(c.total_conversations, 0) > 0
    AND c.month NOT IN (SELECT month FROM monthly_mrr_aggregated)
ORDER BY month;

ALTER TABLE monthly_mrr_chat_joined ADD INDEX idx_month (month);


-- Step 4: Calculate correlation statistics and create results table
-- ============================================================================
DROP TABLE IF EXISTS mrr_chat_correlation_results;
CREATE TABLE mrr_chat_correlation_results AS
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
            THEN (
                (COUNT(*) * SUM(total_mrr * total_conversations) - SUM(total_mrr) * SUM(total_conversations)) /
                (SQRT((COUNT(*) * SUM(total_mrr * total_mrr) - SUM(total_mrr) * SUM(total_mrr)) * 
                      (COUNT(*) * SUM(total_conversations * total_conversations) - SUM(total_conversations) * SUM(total_conversations))))
            ELSE 0
        END AS mrr_vs_total_conversations_corr,
        
        -- Pearson correlation: MRR vs Daily Average
        CASE 
            WHEN STDDEV(total_mrr) > 0 AND STDDEV(avg_daily_conversations) > 0
            THEN (
                (COUNT(*) * SUM(total_mrr * avg_daily_conversations) - SUM(total_mrr) * SUM(avg_daily_conversations)) /
                (SQRT((COUNT(*) * SUM(total_mrr * total_mrr) - SUM(total_mrr) * SUM(total_mrr)) * 
                      (COUNT(*) * SUM(avg_daily_conversations * avg_daily_conversations) - SUM(avg_daily_conversations) * SUM(avg_daily_conversations)))))
            ELSE 0
        END AS mrr_vs_daily_avg_corr,
        
        -- Pearson correlation: Account Count vs Conversations
        CASE 
            WHEN STDDEV(account_count) > 0 AND STDDEV(total_conversations) > 0
            THEN (
                (COUNT(*) * SUM(account_count * total_conversations) - SUM(account_count) * SUM(total_conversations)) /
                (SQRT((COUNT(*) * SUM(account_count * account_count) - SUM(account_count) * SUM(account_count)) * 
                      (COUNT(*) * SUM(total_conversations * total_conversations) - SUM(total_conversations) * SUM(total_conversations)))))
            ELSE 0
        END AS account_count_vs_conversations_corr
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
    POWER(c.mrr_vs_total_conversations_corr, 2) AS mrr_vs_conversations_r_squared,
    POWER(c.mrr_vs_daily_avg_corr, 2) AS mrr_vs_daily_avg_r_squared,
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
    NOW() AS analysis_timestamp
FROM stats s
CROSS JOIN correlation_calc c;


-- Step 5: Create detailed monthly correlation breakdown table
-- ============================================================================
DROP TABLE IF EXISTS monthly_correlation_breakdown;
CREATE TABLE monthly_correlation_breakdown AS
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
    (total_mrr - (SELECT AVG(total_mrr) FROM monthly_mrr_chat_joined)) / 
        NULLIF((SELECT STDDEV(total_mrr) FROM monthly_mrr_chat_joined), 0) AS mrr_z_score,
    (total_conversations - (SELECT AVG(total_conversations) FROM monthly_mrr_chat_joined)) / 
        NULLIF((SELECT STDDEV(total_conversations) FROM monthly_mrr_chat_joined), 0) AS conversations_z_score,
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
    END AS conversations_month_over_month_pct_change
FROM monthly_mrr_chat_joined
ORDER BY month;

