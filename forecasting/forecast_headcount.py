#!/usr/bin/env python3
"""
Support Headcount Forecasting Tool

Analyzes historical Intercom conversation data and MRR trends to forecast
daily TSE headcount requirements 3 months ahead, with special focus on
holiday season patterns.
"""

from __future__ import annotations

import argparse
import json
import csv
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Import our modules
try:
	# Try relative imports (when used as package)
	from .data_processor import (
		load_conversations_csv,
		load_mrr_csv,
		create_daily_aggregates,
		aggregate_mrr_by_month,
		calculate_mrr_growth_rates,
		get_date_range,
	)
	from .holiday_analyzer import analyze_all_holidays
	from .revenue_correlation import (
		correlate_mrr_with_chat_volume,
		correlate_new_customers_with_chat_volume,
	)
	from .forecast_model import generate_forecast
	from .headcount_calculator import calculate_headcount_with_quality_metrics
except ImportError:
	# Fall back to absolute imports (when run as script)
	from pathlib import Path
	forecasting_dir = Path(__file__).parent
	parent_dir = forecasting_dir.parent
	if str(parent_dir) not in sys.path:
		sys.path.insert(0, str(parent_dir))
	
	from forecasting.data_processor import (
		load_conversations_csv,
		load_mrr_csv,
		create_daily_aggregates,
		aggregate_mrr_by_month,
		calculate_mrr_growth_rates,
		get_date_range,
	)
	from forecasting.holiday_analyzer import analyze_all_holidays
	from forecasting.revenue_correlation import (
		correlate_mrr_with_chat_volume,
		correlate_new_customers_with_chat_volume,
	)
	from forecasting.forecast_model import generate_forecast
	from forecasting.headcount_calculator import calculate_headcount_with_quality_metrics


def load_data(
	conversations_path: str,
	mrr_path: str
) -> tuple[Dict[str, Dict], Dict[str, Dict], Dict[str, float]]:
	"""Load and process all data files."""
	print("Loading conversations data...")
	conversations = load_conversations_csv(conversations_path)
	print(f"  Loaded {len(conversations)} conversations")
	
	print("Loading MRR data...")
	mrr_records = load_mrr_csv(mrr_path)
	print(f"  Loaded {len(mrr_records)} MRR records")
	
	print("Creating daily aggregates...")
	daily_data = create_daily_aggregates(conversations)
	print(f"  Created aggregates for {len(daily_data)} days")
	
	print("Aggregating MRR by month...")
	monthly_mrr = aggregate_mrr_by_month(mrr_records)
	print(f"  Aggregated {len(monthly_mrr)} months")
	
	print("Calculating MRR growth rates...")
	mrr_growth_rates = calculate_mrr_growth_rates(monthly_mrr)
	print(f"  Calculated growth rates for {len(mrr_growth_rates)} months")
	
	return daily_data, monthly_mrr, mrr_growth_rates


def analyze_historical_trends(
	daily_data: Dict[str, Dict],
	monthly_mrr: Dict[str, Dict],
	mrr_growth_rates: Dict[str, float]
) -> Dict[str, any]:
	"""Perform historical trend analysis."""
	print("\nAnalyzing historical trends...")
	
	# Holiday impact analysis
	print("  Analyzing holiday impacts...")
	holiday_impacts = analyze_all_holidays(daily_data)
	
	# Revenue correlation
	print("  Analyzing revenue correlations...")
	mrr_correlation = correlate_mrr_with_chat_volume(daily_data, monthly_mrr, mrr_growth_rates)
	new_customer_correlation = correlate_new_customers_with_chat_volume(daily_data, monthly_mrr)
	
	# Calculate date range
	min_date, max_date = get_date_range(daily_data)
	
	# Calculate recent averages
	sorted_dates = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	recent_30_days = sorted_dates[-30:] if len(sorted_dates) >= 30 else sorted_dates
	recent_volumes = [daily_data[d]['total_chats'] for d in recent_30_days]
	recent_csats = [
		daily_data[d]['avg_csat'] for d in recent_30_days
		if daily_data[d]['avg_csat'] is not None
	]
	recent_slas = [
		daily_data[d]['sla_adherence_pct'] for d in recent_30_days
		if daily_data[d]['sla_adherence_pct'] is not None
	]
	
	import statistics
	
	return {
		'date_range': {
			'start': min_date.isoformat(),
			'end': max_date.isoformat(),
			'days': (max_date - min_date).days,
		},
		'holiday_impacts': holiday_impacts,
		'mrr_correlation': mrr_correlation,
		'new_customer_correlation': new_customer_correlation,
		'recent_metrics': {
			'avg_daily_chats': statistics.mean(recent_volumes) if recent_volumes else 0,
			'avg_csat': statistics.mean(recent_csats) if recent_csats else None,
			'avg_sla_adherence': statistics.mean(recent_slas) if recent_slas else None,
		},
	}


def generate_headcount_forecast(
	daily_data: Dict[str, Dict],
	monthly_mrr: Dict[str, Dict],
	mrr_growth_rates: Dict[str, float],
	holiday_impacts: Dict[str, Dict],
	forecast_days: int = 90
) -> List[Dict[str, any]]:
	"""Generate headcount forecast for specified number of days."""
	print(f"\nGenerating {forecast_days}-day forecast...")
	
	# Get last historical date
	sorted_dates = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	if not sorted_dates:
		raise ValueError("No historical data available")
	
	last_date = daily_data[sorted_dates[-1]]['date']
	start_date = last_date + timedelta(days=1)
	end_date = start_date + timedelta(days=forecast_days - 1)
	
	print(f"  Forecast period: {start_date} to {end_date}")
	
	# Get MRR correlation for revenue-based adjustments
	mrr_correlation = correlate_mrr_with_chat_volume(daily_data, monthly_mrr, mrr_growth_rates)
	
	# Generate volume forecasts
	print("  Forecasting chat volumes...")
	volume_forecasts = generate_forecast(
		start_date,
		end_date,
		daily_data,
		holiday_impacts,
		monthly_mrr,
		mrr_correlation
	)
	
	# Calculate headcount for each day
	print("  Calculating required headcount...")
	forecasts = []
	for vol_forecast in volume_forecasts:
		headcount_calc = calculate_headcount_with_quality_metrics(
			vol_forecast['projected_chats'],
			target_csat=4.7,
			target_sla_adherence=0.95,
			use_sustainable_target=True,
			safety_margin=1.1
		)
		
		forecasts.append({
			'date': vol_forecast['date'],
			'projected_chats': round(vol_forecast['projected_chats'], 1),
			'confidence_lower': round(vol_forecast['confidence_lower'], 1),
			'confidence_upper': round(vol_forecast['confidence_upper'], 1),
			'required_headcount': headcount_calc['required_headcount'],
			'estimated_csat': round(headcount_calc['estimated_csat'], 2),
			'estimated_sla_adherence': round(headcount_calc['estimated_sla_adherence'] * 100, 1),
			'meets_csat_target': headcount_calc['meets_csat_target'],
			'meets_sla_target': headcount_calc['meets_sla_target'],
			'chats_per_tse': round(headcount_calc['chats_per_tse'], 1),
			'is_holiday': vol_forecast['is_holiday'],
			'holiday_type': vol_forecast['holiday_type'],
		})
	
	return forecasts


def export_forecast_csv(forecasts: List[Dict], output_path: str):
	"""Export forecasts to CSV file."""
	print(f"\nExporting forecast to {output_path}...")
	
	fieldnames = [
		'date', 'projected_chats', 'confidence_lower', 'confidence_upper',
		'required_headcount', 'estimated_csat', 'estimated_sla_adherence',
		'meets_csat_target', 'meets_sla_target', 'chats_per_tse',
		'is_holiday', 'holiday_type'
	]
	
	with open(output_path, 'w', newline='', encoding='utf-8') as f:
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		for forecast in forecasts:
			row = forecast.copy()
			row['date'] = row['date'].isoformat()
			row['meets_csat_target'] = 'Yes' if row['meets_csat_target'] else 'No'
			row['meets_sla_target'] = 'Yes' if row['meets_sla_target'] else 'No'
			writer.writerow(row)
	
	print(f"  Exported {len(forecasts)} forecast records")


def export_forecast_json(forecasts: List[Dict], output_path: str):
	"""Export forecasts to JSON file."""
	print(f"\nExporting forecast to {output_path}...")
	
	# Convert dates to strings for JSON
	json_data = []
	for forecast in forecasts:
		json_forecast = forecast.copy()
		json_forecast['date'] = forecast['date'].isoformat()
		json_data.append(json_forecast)
	
	with open(output_path, 'w', encoding='utf-8') as f:
		json.dump(json_data, f, indent=2)
	
	print(f"  Exported {len(forecasts)} forecast records")


def generate_summary_report(
	analysis: Dict[str, any],
	forecasts: List[Dict]
) -> str:
	"""Generate a text summary report."""
	report = []
	report.append("=" * 80)
	report.append("SUPPORT HEADCOUNT FORECASTING REPORT")
	report.append("=" * 80)
	report.append("")
	
	# Historical analysis
	report.append("HISTORICAL ANALYSIS")
	report.append("-" * 80)
	date_range = analysis['date_range']
	report.append(f"Data Period: {date_range['start']} to {date_range['end']} ({date_range['days']} days)")
	
	recent = analysis['recent_metrics']
	report.append(f"\nRecent 30-Day Averages:")
	report.append(f"  Daily Chats: {recent['avg_daily_chats']:.1f}")
	if recent['avg_csat']:
		report.append(f"  CSAT: {recent['avg_csat']:.2f}")
	if recent['avg_sla_adherence']:
		report.append(f"  SLA Adherence: {recent['avg_sla_adherence']:.1f}%")
	
	# Holiday impacts
	report.append("\nHOLIDAY IMPACT ANALYSIS")
	report.append("-" * 80)
	holiday_impacts = analysis['holiday_impacts']
	for holiday_type, impact in holiday_impacts.items():
		if impact['sample_size'] > 0:
			report.append(f"\n{holiday_type.replace('_', ' ').title()}:")
			report.append(f"  Volume Multiplier: {impact['volume_multiplier']:.2f}x")
			report.append(f"  CSAT Impact: {impact['csat_impact']:+.2f}")
			report.append(f"  SLA Impact: {impact['sla_impact']:+.1f}%")
			report.append(f"  Sample Size: {impact['sample_size']} days")
	
	# Revenue correlation
	report.append("\nREVENUE CORRELATION")
	report.append("-" * 80)
	mrr_corr = analysis['mrr_correlation']
	report.append(f"MRR-Chat Volume Correlation: {mrr_corr['correlation']:.3f}")
	report.append(f"Growth Rate Correlation: {mrr_corr['growth_correlation']:.3f}")
	report.append(f"Chats per $1M MRR: {mrr_corr['chat_per_mrr_ratio'] * 1000000:.1f}")
	
	new_cust_corr = analysis['new_customer_correlation']
	report.append(f"\nNew Customer-Chat Volume Correlation: {new_cust_corr['correlation']:.3f}")
	report.append(f"Chats per New Customer: {new_cust_corr['chats_per_new_customer']:.1f}")
	
	# Forecast summary
	report.append("\nFORECAST SUMMARY")
	report.append("-" * 80)
	if forecasts:
		forecast_start = forecasts[0]['date']
		forecast_end = forecasts[-1]['date']
		report.append(f"Forecast Period: {forecast_start} to {forecast_end}")
		
		avg_chats = sum(f['projected_chats'] for f in forecasts) / len(forecasts)
		avg_headcount = sum(f['required_headcount'] for f in forecasts) / len(forecasts)
		max_headcount = max(f['required_headcount'] for f in forecasts)
		min_headcount = min(f['required_headcount'] for f in forecasts)
		
		report.append(f"\nAverage Daily Projections:")
		report.append(f"  Chats: {avg_chats:.1f}")
		report.append(f"  Required Headcount: {avg_headcount:.1f}")
		report.append(f"\nHeadcount Range: {min_headcount} - {max_headcount}")
		
		# Holiday periods
		holiday_days = [f for f in forecasts if f['is_holiday']]
		if holiday_days:
			report.append(f"\nHoliday Periods ({len(holiday_days)} days):")
			holiday_headcounts = [f['required_headcount'] for f in holiday_days]
			report.append(f"  Average Headcount: {sum(holiday_headcounts) / len(holiday_headcounts):.1f}")
			report.append(f"  Max Headcount: {max(holiday_headcounts)}")
	
	report.append("\n" + "=" * 80)
	
	return "\n".join(report)


def main():
	"""Main entry point."""
	parser = argparse.ArgumentParser(
		description='Forecast support team headcount requirements'
	)
	parser.add_argument(
		'--conversations',
		type=str,
		default='Intercom Conversations - Master Table - Sheet1.csv',
		help='Path to conversations CSV file'
	)
	parser.add_argument(
		'--mrr',
		type=str,
		default='MONTHLY_RECURRING_REVENUE.csv',
		help='Path to MRR CSV file'
	)
	parser.add_argument(
		'--days',
		type=int,
		default=90,
		help='Number of days to forecast (default: 90)'
	)
	parser.add_argument(
		'--output-csv',
		type=str,
		help='Output CSV file path'
	)
	parser.add_argument(
		'--output-json',
		type=str,
		help='Output JSON file path'
	)
	parser.add_argument(
		'--output-report',
		type=str,
		help='Output text report file path'
	)
	
	args = parser.parse_args()
	
	# Check if files exist
	conv_path = Path(args.conversations)
	mrr_path = Path(args.mrr)
	
	if not conv_path.exists():
		print(f"Error: Conversations file not found: {args.conversations}", file=sys.stderr)
		sys.exit(1)
	
	if not mrr_path.exists():
		print(f"Error: MRR file not found: {args.mrr}", file=sys.stderr)
		sys.exit(1)
	
	try:
		# Load data
		daily_data, monthly_mrr, mrr_growth_rates = load_data(
			str(conv_path),
			str(mrr_path)
		)
		
		# Analyze historical trends
		analysis = analyze_historical_trends(daily_data, monthly_mrr, mrr_growth_rates)
		
		# Generate forecast
		forecasts = generate_headcount_forecast(
			daily_data,
			monthly_mrr,
			mrr_growth_rates,
			analysis['holiday_impacts'],
			args.days
		)
		
		# Export results
		if args.output_csv:
			export_forecast_csv(forecasts, args.output_csv)
		
		if args.output_json:
			export_forecast_json(forecasts, args.output_json)
		
		if args.output_report:
			report = generate_summary_report(analysis, forecasts)
			with open(args.output_report, 'w', encoding='utf-8') as f:
				f.write(report)
			print(f"\nReport saved to {args.output_report}")
		
		# Print summary to console
		print("\n" + generate_summary_report(analysis, forecasts))
		
		print("\nForecast complete!")
		
	except Exception as e:
		print(f"\nError: {e}", file=sys.stderr)
		import traceback
		traceback.print_exc()
		sys.exit(1)


if __name__ == '__main__':
	main()

