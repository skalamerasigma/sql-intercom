# SQL Correlation Analysis Guide

This guide explains how to use the SQL scripts to analyze the correlation between MRR and chat volume in your database.

## Files Overview

1. **`setup_mrr_chat_tables.sql`** - Creates base tables and loads CSV data
2. **`mrr_chat_correlation_analysis.sql`** - PostgreSQL version (uses CORR() function)
3. **`mrr_chat_correlation_analysis_mysql.sql`** - MySQL version (manual correlation calculation)

## Quick Start

### Step 1: Load CSV Data into Database

#### Option A: PostgreSQL (Recommended)

```sql
-- 1. Create tables
\i setup_mrr_chat_tables.sql

-- 2. Load CSV files (adjust paths as needed)
\copy mrr_data FROM 'MONTHLY_RECURRING_REVENUE.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');
\copy conversations_data FROM 'Intercom Conversations - Master Table - Sheet1.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');
```

#### Option B: MySQL

```sql
-- 1. Create tables (modify setup script for MySQL syntax)
-- 2. Load CSV files
LOAD DATA LOCAL INFILE 'MONTHLY_RECURRING_REVENUE.csv'
INTO TABLE mrr_data
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'Intercom Conversations - Master Table - Sheet1.csv'
INTO TABLE conversations_data
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

#### Option C: Using Database GUI Tools

- **pgAdmin** (PostgreSQL): Right-click table → Import/Export
- **MySQL Workbench**: Table Data Import Wizard
- **DBeaver**: Right-click table → Import Data

### Step 2: Run Correlation Analysis

#### PostgreSQL:
```sql
\i mrr_chat_correlation_analysis.sql
```

#### MySQL:
```sql
SOURCE mrr_chat_correlation_analysis_mysql.sql;
```

## Output Tables Created

### 1. `mrr_chat_correlation_results`
**Main results table** containing:
- Correlation coefficients (MRR vs Conversations, MRR vs Daily Avg, Account Count vs Conversations)
- R-squared values
- Summary statistics (means, standard deviations, min/max)
- Correlation strength interpretations
- Analysis timestamp

**Query Example:**
```sql
SELECT 
    sample_size,
    start_month,
    end_month,
    mrr_vs_total_conversations_corr AS correlation,
    correlation_strength_mrr_total AS strength,
    mrr_vs_conversations_r_squared AS r_squared,
    mean_mrr,
    mean_conversations
FROM mrr_chat_correlation_results;
```

### 2. `monthly_mrr_chat_joined`
**Monthly aggregated data** with:
- Total MRR per month
- Total conversations per month
- Average daily conversations
- Account counts
- Calculated ratios (conversations per MRR, conversations per account)

**Query Example:**
```sql
SELECT 
    month,
    total_mrr,
    total_conversations,
    avg_daily_conversations,
    conversations_per_mrr,
    conversations_per_account
FROM monthly_mrr_chat_joined
ORDER BY month DESC
LIMIT 12;
```

### 3. `monthly_correlation_breakdown`
**Detailed monthly analysis** with:
- Z-scores for outlier detection
- Month-over-month percentage changes
- Rolling averages (3-month, 12-month)

**Query Example:**
```sql
-- Find outliers
SELECT 
    month,
    total_mrr,
    total_conversations,
    mrr_z_score,
    conversations_z_score
FROM monthly_correlation_breakdown
WHERE ABS(mrr_z_score) > 2 OR ABS(conversations_z_score) > 2
ORDER BY month;
```

### 4. `v_mrr_chat_correlation_summary` (PostgreSQL only)
**Summary view** showing all correlation types side-by-side.

**Query Example:**
```sql
SELECT * FROM v_mrr_chat_correlation_summary 
ORDER BY correlation_coefficient DESC;
```

## Common Queries

### View Correlation Results
```sql
SELECT * FROM mrr_chat_correlation_results;
```

### Get Monthly Trends
```sql
SELECT 
    month,
    total_mrr,
    total_conversations,
    ROUND(total_conversations / NULLIF(total_mrr, 0) * 1000000, 2) AS conversations_per_million_mrr
FROM monthly_mrr_chat_joined
ORDER BY month;
```

### Find Months with Largest Deviations
```sql
SELECT 
    month,
    total_mrr,
    total_conversations,
    mrr_month_over_month_pct_change,
    conversations_month_over_month_pct_change,
    ABS(mrr_month_over_month_pct_change - conversations_month_over_month_pct_change) AS deviation
FROM monthly_correlation_breakdown
WHERE mrr_month_over_month_pct_change IS NOT NULL
ORDER BY deviation DESC
LIMIT 10;
```

### Forecast Future Conversations Based on MRR
```sql
-- Assuming you have a future_mrr table with projected MRR
SELECT 
    f.month,
    f.projected_mrr,
    -- Use the correlation ratio from results
    f.projected_mrr * (SELECT conversations_per_mrr_ratio FROM mrr_chat_correlation_results) AS projected_conversations,
    -- Use daily average correlation
    f.projected_mrr * (SELECT conversations_per_mrr_ratio FROM mrr_chat_correlation_results) / 30 AS projected_daily_avg
FROM future_mrr f;
```

## Database-Specific Notes

### PostgreSQL
- Uses built-in `CORR()` function for correlation
- Supports `PERCENTILE_CONT` for median calculation
- Full outer joins supported
- Window functions fully supported

### MySQL
- Manual correlation calculation (no built-in CORR function)
- Uses `STDDEV()` for standard deviation
- May need to adjust FULL OUTER JOIN to LEFT/RIGHT JOIN UNION
- Window functions available in MySQL 8.0+

### SQL Server
- Similar to PostgreSQL syntax
- Use `CORRELATION()` or manual calculation
- `STDEV()` instead of `STDDEV()`
- `PERCENTILE_CONT` available

### SQLite
- No built-in correlation function
- Manual calculation required
- Limited window function support
- Use Python script instead for SQLite

## Troubleshooting

### Issue: Date Format Errors
**Solution:** Adjust date parsing functions based on your CSV format:
- PostgreSQL: `TO_DATE()` or `TO_TIMESTAMP()`
- MySQL: `STR_TO_DATE()`
- SQL Server: `CONVERT()` or `PARSE()`

### Issue: Column Names with Spaces
**Solution:** Use quoted identifiers:
- PostgreSQL/MySQL: Use double quotes or backticks
- SQL Server: Use square brackets `[Column Name]`

### Issue: CSV Loading Errors
**Solution:**
1. Check CSV encoding (UTF-8 recommended)
2. Verify delimiter matches CSV format
3. Handle NULL values appropriately
4. Check for special characters in data

### Issue: Correlation Returns NULL
**Solution:**
- Ensure sufficient data points (minimum 2, preferably 10+)
- Check for NULL values in MRR or conversation columns
- Verify standard deviation is not zero

## Performance Optimization

1. **Create Indexes:**
```sql
CREATE INDEX idx_mrr_month ON mrr_data("Revenue Calendar Month");
CREATE INDEX idx_conv_month ON conversations_data("Conversation Created PT");
```

2. **Partition Large Tables:**
```sql
-- Partition by month for very large datasets
CREATE TABLE monthly_mrr_aggregated (
    ...
) PARTITION BY RANGE (month);
```

3. **Materialize Views:**
```sql
-- Refresh periodically instead of calculating on-the-fly
CREATE MATERIALIZED VIEW monthly_mrr_chat_joined_mv AS
SELECT ... FROM monthly_mrr_chat_joined;
```

## Integration with Existing Systems

### Update Existing Forecast Tables
```sql
UPDATE forecast_table f
SET projected_conversations = 
    f.projected_mrr * (SELECT conversations_per_mrr_ratio FROM mrr_chat_correlation_results)
WHERE f.projected_conversations IS NULL;
```

### Create Scheduled Refresh
```sql
-- PostgreSQL: Create a function and schedule with pg_cron
CREATE OR REPLACE FUNCTION refresh_correlation_analysis()
RETURNS void AS $$
BEGIN
    TRUNCATE TABLE mrr_chat_correlation_results;
    INSERT INTO mrr_chat_correlation_results SELECT ...;
END;
$$ LANGUAGE plpgsql;
```

## Next Steps

1. **Automate:** Set up scheduled refresh of correlation tables
2. **Visualize:** Connect to BI tools (Tableau, Power BI, Metabase)
3. **Alert:** Set up alerts when correlation drops below threshold
4. **Segment:** Analyze correlations by customer segment, region, or product
5. **Forecast:** Integrate correlation ratios into forecasting models

