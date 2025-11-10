# Support Headcount Forecasting Model

A comprehensive forecasting system that analyzes historical Intercom conversation data and MRR trends to predict daily TSE headcount requirements 3 months ahead, with special focus on holiday season patterns.

## Features

- **Historical Trend Analysis**: Analyzes daily chat volume, CSAT ratings, and SLA performance over time
- **Holiday Impact Analysis**: Identifies and quantifies the impact of holiday periods (Thanksgiving, Christmas, New Year) on support volume and quality metrics
- **Revenue Correlation**: Correlates MRR/ARR growth and new customer additions with support chat volume
- **Time Series Forecasting**: Uses historical patterns, seasonality, and holiday effects to forecast future chat volume
- **Headcount Calculation**: Calculates required TSE headcount based on projected volume, SLA requirements (1 min initial response, 4.7 CSAT), and productivity constraints (max 5 chats per TSE)
- **Quality Metrics**: Estimates expected CSAT and SLA adherence given projected volume and headcount

## Requirements

### Python Dependencies

The forecasting model uses standard library modules plus optional visualization support:

**Required:**
- Python 3.7+
- Standard library only (csv, datetime, statistics, math, etc.)

**Optional (for visualization):**
- matplotlib (for generating plots and charts)

Install optional dependencies:
```bash
pip install matplotlib
```

## Usage

### Basic Usage

Run the forecasting script from the project root directory:

```bash
python -m forecasting.forecast_headcount \
  --conversations "Intercom Conversations - Master Table - Sheet1.csv" \
  --mrr "MONTHLY_RECURRING_REVENUE.csv" \
  --days 90
```

### Command-Line Options

```
--conversations PATH    Path to conversations CSV file (default: "Intercom Conversations - Master Table - Sheet1.csv")
--mrr PATH              Path to MRR CSV file (default: "MONTHLY_RECURRING_REVENUE.csv")
--days N                Number of days to forecast (default: 90)
--output-csv PATH       Export forecast to CSV file
--output-json PATH      Export forecast to JSON file
--output-report PATH    Export text summary report
```

### Example

```bash
python -m forecasting.forecast_headcount \
  --conversations "Intercom Conversations - Master Table - Sheet1.csv" \
  --mrr "MONTHLY_RECURRING_REVENUE.csv" \
  --days 90 \
  --output-csv forecast_output.csv \
  --output-json forecast_output.json \
  --output-report forecast_report.txt
```

## Output Format

### CSV Output

The CSV file contains daily forecasts with the following columns:

- `date`: Forecast date (YYYY-MM-DD)
- `projected_chats`: Projected daily chat volume
- `confidence_lower`: Lower bound of 80% confidence interval
- `confidence_upper`: Upper bound of 80% confidence interval
- `required_headcount`: Required number of TSEs
- `estimated_csat`: Estimated CSAT rating given headcount
- `estimated_sla_adherence`: Estimated SLA adherence percentage
- `meets_csat_target`: Whether CSAT target (4.7) is met (Yes/No)
- `meets_sla_target`: Whether SLA target (95%) is met (Yes/No)
- `chats_per_tse`: Average chats per TSE per day
- `is_holiday`: Whether date is a holiday period
- `holiday_type`: Type of holiday (if applicable)

### JSON Output

The JSON file contains the same data in structured format, suitable for programmatic access.

### Text Report

The text report includes:
- Historical analysis summary
- Holiday impact multipliers
- Revenue correlation findings
- Forecast summary with key metrics

## Key Metrics

Based on support policies:

- **CSAT Target**: 4.7 average rating
- **SLA Target**: Initial response ≤ 1 minute
- **Max Concurrent Chats per TSE**: 5
- **Sustainable Chats per TSE per Day**: 10-12
- **Max Chats per TSE per Day**: 16 (target to reduce)
- **Support Hours**: 2am - 6pm PT (16 hours)
- **Major Holidays**: Thanksgiving, Day After Thanksgiving, Christmas, New Year's Day
- **Holiday Break**: Dec 21 - Jan 2 (reduced capacity period)

## Model Components

### 1. Data Processing (`data_processor.py`)

- Loads and parses CSV files
- Creates daily aggregates (chat volume, CSAT, IR times, SLA adherence)
- Aggregates MRR data by month
- Calculates MRR growth rates

### 2. Holiday Analysis (`holiday_analyzer.py`)

- Identifies holiday periods (Thanksgiving week, Christmas period, etc.)
- Calculates impact multipliers for volume, CSAT, and SLA
- Compares holiday periods vs baseline periods

### 3. Revenue Correlation (`revenue_correlation.py`)

- Correlates MRR growth with chat volume
- Analyzes new customer additions vs support volume
- Provides revenue-based volume estimates

### 4. Forecasting Model (`forecast_model.py`)

- Uses historical patterns (day of week, month effects)
- Applies holiday adjustments
- Incorporates revenue trends
- Generates forecasts with confidence intervals

### 5. Headcount Calculator (`headcount_calculator.py`)

- Calculates required headcount based on:
  - Projected volume and productivity targets
  - Peak hourly coverage requirements
  - SLA requirements
- Estimates expected CSAT and SLA adherence
- Applies safety margins

## Visualization

The `visualization.py` module provides functions for creating plots:

- `plot_historical_volume()`: Historical chat volume trends
- `plot_forecast()`: Historical data with forecast overlay
- `plot_headcount_forecast()`: Required headcount over time
- `plot_holiday_comparison()`: Holiday impact multipliers
- `plot_csat_trends()`: CSAT trends over time

Example:
```python
from forecasting.visualization import plot_forecast

plot_forecast(historical_data, forecasts, output_path='forecast.png')
```

## Programmatic Usage

You can also use the forecasting modules programmatically:

```python
from forecasting.data_processor import load_conversations_csv, create_daily_aggregates
from forecasting.holiday_analyzer import analyze_all_holidays
from forecasting.forecast_model import generate_forecast
from forecasting.headcount_calculator import calculate_headcount_with_quality_metrics

# Load data
conversations = load_conversations_csv('conversations.csv')
daily_data = create_daily_aggregates(conversations)

# Analyze holidays
holiday_impacts = analyze_all_holidays(daily_data)

# Generate forecast
forecasts = generate_forecast(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 31),
    daily_data=daily_data,
    holiday_impacts=holiday_impacts
)

# Calculate headcount
for forecast in forecasts:
    headcount = calculate_headcount_with_quality_metrics(
        forecast['projected_chats'],
        target_csat=4.7,
        target_sla_adherence=0.95
    )
    print(f"{forecast['date']}: {headcount['required_headcount']} TSEs")
```

## Limitations

- The model uses simplified assumptions for SLA and CSAT estimation
- Revenue correlation may not capture all factors affecting support volume
- Holiday impacts are based on historical data and may vary year-to-year
- The model assumes consistent TSE productivity; actual performance may vary

## Future Enhancements

- Integration with real-time Intercom API data
- Machine learning models for improved accuracy
- More sophisticated SLA and CSAT modeling
- Regional/geographic analysis
- Integration with scheduling systems

## License

Internal use only.

