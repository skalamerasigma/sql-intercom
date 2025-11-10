# MRR vs Chat Volume Correlation Analysis

## Executive Summary

**Analysis Date:** Generated from CSV data analysis  
**Analysis Period:** February 2020 to November 2025 (70 months)  
**Key Finding:** **Strong positive correlation** between Monthly Recurring Revenue (MRR) and chat volume

---

## Key Findings

### Correlation Results

1. **MRR vs Total Monthly Conversations**
   - **Correlation Coefficient:** 0.805 (Strong Positive Correlation)
   - **Interpretation:** As MRR increases, chat volume increases proportionally
   - **Sample Size:** 70 months of overlapping data

2. **MRR vs Average Daily Conversations**
   - **Correlation Coefficient:** 0.868 (Very Strong Positive Correlation)
   - **Interpretation:** Daily chat volume shows an even stronger relationship with MRR
   - **Sample Size:** 70 months

3. **Account Count vs Total Conversations**
   - **Correlation Coefficient:** 0.784 (Strong Positive Correlation)
   - **Interpretation:** Number of accounts also strongly correlates with chat volume
   - **Sample Size:** 70 months

### Summary Statistics

- **Average Monthly MRR:** $3,347,149
- **Average Monthly Conversations:** 182 conversations
- **Average Daily Conversations:** 7.87 conversations/day
- **Conversations per $1 MRR:** 0.0000545 (approximately 1 conversation per $18,300 MRR)
- **Conversations per Account:** 0.30 conversations/account/month

### Data Range

- **MRR Range:** $71,843 - $12,150,438
- **Conversations Range:** 20 - 849 conversations/month
- **Date Range:** February 2020 to November 2025

---

## Interpretation

### What This Means

1. **Strong Positive Relationship:** The correlation coefficient of 0.805 indicates a strong positive linear relationship between MRR and chat volume. This means:
   - When MRR increases, chat volume tends to increase
   - When MRR decreases, chat volume tends to decrease
   - The relationship is consistent and predictable

2. **Predictive Value:** With an r-value of 0.805, approximately **64.8% of the variance** in chat volume can be explained by MRR changes (r² = 0.648).

3. **Business Implications:**
   - **Capacity Planning:** MRR growth can be used to forecast support chat volume
   - **Resource Allocation:** As revenue grows, support resources should scale proportionally
   - **Customer Success:** Higher MRR customers generate more support interactions (likely due to more users, more complex usage, or higher engagement)

### Correlation Strength Guide

- **0.9 - 1.0:** Very Strong
- **0.7 - 0.9:** Strong ← **Your Results**
- **0.5 - 0.7:** Moderate
- **0.3 - 0.5:** Weak
- **0.0 - 0.3:** Very Weak

---

## Monthly Trends

### Early Period (2020-2021)
- Low MRR ($71K - $230K) corresponded with low chat volume (20-64 conversations/month)
- Average: ~1.8-2.0 conversations per day

### Growth Period (2022-2024)
- MRR growth from ~$500K to $8M+ 
- Chat volume increased proportionally from ~50 to 400+ conversations/month
- Daily averages increased to 10-15 conversations/day

### Recent Period (2025)
- MRR continued growth to $12M+
- Peak chat volumes reaching 800+ conversations/month
- Daily averages reaching 25-30 conversations/day

---

## Recommendations

### 1. Use MRR for Forecasting
- Leverage the strong correlation (r=0.805) to predict chat volume based on MRR forecasts
- Formula: Estimated Conversations ≈ (MRR × 0.0000545) ± margin of error

### 2. Scale Support Resources
- As MRR grows, proactively scale support team capacity
- Monitor the ratio: ~0.30 conversations per account per month

### 3. Account for Account Growth
- Account count also strongly correlates (r=0.784) with chat volume
- Consider both MRR and account count when forecasting

### 4. Monitor Daily Patterns
- The even stronger correlation with daily averages (r=0.868) suggests consistent daily patterns
- Use daily averages for more granular capacity planning

### 5. Investigate Outliers
- Review months where chat volume deviates significantly from MRR predictions
- Identify factors causing deviations (product launches, issues, seasonal patterns)

---

## Methodology

### Data Sources
1. **MRR Data:** `MONTHLY_RECURRING_REVENUE.csv`
   - Aggregated by month using `Revenue Calendar Month`
   - Summed total MRR per month
   - Tracked unique account counts

2. **Conversation Data:** `Intercom Conversations - Master Table - Sheet1.csv`
   - Aggregated by month using `Conversation Created PT`
   - Counted total conversations per month
   - Calculated daily averages

### Statistical Analysis
- **Correlation Method:** Pearson correlation coefficient
- **Sample Size:** 70 months of overlapping data
- **Date Range:** February 2020 to November 2025

### Limitations
- Analysis based on aggregate monthly data
- Does not account for:
  - Seasonal variations
  - Product-specific factors
  - Customer segment differences
  - External events (pandemics, market changes)
- Correlation does not imply causation

---

## Files Generated

1. **`mrr_chat_correlation_analysis.json`** - Detailed analysis results in JSON format
2. **`analyze_mrr_chat_correlation.py`** - Analysis script
3. **`visualize_mrr_chat_correlation.py`** - Visualization script (requires matplotlib)
4. **`MRR_CHAT_CORRELATION_ANALYSIS.md`** - This summary document

---

## Next Steps

1. **Generate Visualizations:** Run `visualize_mrr_chat_correlation.py` (requires matplotlib)
2. **Refine Forecasts:** Integrate this correlation into existing forecasting models
3. **Segment Analysis:** Analyze correlations by customer segment, region, or product
4. **Time-Lagged Analysis:** Investigate if MRR changes lead chat volume changes (lag analysis)
5. **Causation Investigation:** Determine if MRR growth causes chat volume, or if both are driven by a third factor

---

## Conclusion

The analysis reveals a **strong positive correlation** between MRR and chat volume, with a correlation coefficient of **0.805**. This relationship is statistically significant and can be used for:

- **Predictive modeling** for support capacity planning
- **Resource allocation** based on revenue forecasts
- **Understanding** the relationship between business growth and support demand

The even stronger correlation with daily averages (r=0.868) suggests that the relationship is consistent and reliable for forecasting purposes.

