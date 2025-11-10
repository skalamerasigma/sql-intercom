"""
Time series forecasting model for support chat volume.

Uses historical patterns, seasonality, holidays, and revenue trends
to forecast future chat volume.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
import math

from .holiday_analyzer import get_holiday_adjustment, get_holiday_type
from .revenue_correlation import estimate_chat_volume_from_mrr


def calculate_trend(daily_data: Dict[str, Dict], days: int = 30) -> float:
	"""
	Calculate trend (growth rate) from recent data.
	
	Uses linear regression on recent daily volumes.
	"""
	sorted_dates = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	if len(sorted_dates) < 2:
		return 0.0
	
	# Use last N days
	recent_dates = sorted_dates[-days:] if len(sorted_dates) > days else sorted_dates
	
	volumes = [daily_data[d]['total_chats'] for d in recent_dates]
	if len(volumes) < 2:
		return 0.0
	
	# Simple linear trend
	n = len(volumes)
	x_values = list(range(n))
	mean_x = statistics.mean(x_values)
	mean_y = statistics.mean(volumes)
	
	numerator = sum((x_values[i] - mean_x) * (volumes[i] - mean_y) for i in range(n))
	denominator = sum((x - mean_x) ** 2 for x in x_values)
	
	if denominator == 0:
		return 0.0
	
	slope = numerator / denominator
	# Convert to daily growth rate percentage
	avg_volume = mean_y
	if avg_volume > 0:
		daily_growth_rate = (slope / avg_volume) * 100
	else:
		daily_growth_rate = 0.0
	
	return daily_growth_rate


def calculate_day_of_week_patterns(daily_data: Dict[str, Dict]) -> Dict[int, float]:
	"""
	Calculate average volume by day of week (0=Monday, 6=Sunday).
	
	Returns dict mapping weekday to average volume multiplier.
	"""
	day_volumes = {i: [] for i in range(7)}
	
	for date_key, data in daily_data.items():
		if data['date']:
			weekday = data['date'].weekday()
			day_volumes[weekday].append(data['total_chats'])
	
	# Calculate averages
	day_averages = {}
	overall_avg = 0.0
	total_count = 0
	
	for weekday in range(7):
		if day_volumes[weekday]:
			avg = statistics.mean(day_volumes[weekday])
			day_averages[weekday] = avg
			overall_avg += sum(day_volumes[weekday])
			total_count += len(day_volumes[weekday])
	
	if total_count == 0:
		return {i: 1.0 for i in range(7)}
	
	overall_avg = overall_avg / total_count
	
	# Convert to multipliers
	day_multipliers = {}
	for weekday in range(7):
		if weekday in day_averages and overall_avg > 0:
			day_multipliers[weekday] = day_averages[weekday] / overall_avg
		else:
			day_multipliers[weekday] = 1.0
	
	return day_multipliers


def calculate_month_patterns(daily_data: Dict[str, Dict]) -> Dict[int, float]:
	"""
	Calculate average volume by month (1=January, 12=December).
	
	Returns dict mapping month to average volume multiplier.
	"""
	month_volumes = {i: [] for i in range(1, 13)}
	
	for date_key, data in daily_data.items():
		if data['date']:
			month = data['date'].month
			month_volumes[month].append(data['total_chats'])
	
	# Calculate averages
	month_averages = {}
	overall_avg = 0.0
	total_count = 0
	
	for month in range(1, 13):
		if month_volumes[month]:
			avg = statistics.mean(month_volumes[month])
			month_averages[month] = avg
			overall_avg += sum(month_volumes[month])
			total_count += len(month_volumes[month])
	
	if total_count == 0:
		return {i: 1.0 for i in range(1, 13)}
	
	overall_avg = overall_avg / total_count
	
	# Convert to multipliers
	month_multipliers = {}
	for month in range(1, 13):
		if month in month_averages and overall_avg > 0:
			month_multipliers[month] = month_averages[month] / overall_avg
		else:
			month_multipliers[month] = 1.0
	
	return month_multipliers


def calculate_baseline_volume(daily_data: Dict[str, Dict], days: int = 30) -> float:
	"""
	Calculate baseline daily volume from recent data.
	"""
	sorted_dates = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	if not sorted_dates:
		return 0.0
	
	# Use last N days
	recent_dates = sorted_dates[-days:] if len(sorted_dates) > days else sorted_dates
	volumes = [daily_data[d]['total_chats'] for d in recent_dates]
	
	return statistics.mean(volumes) if volumes else 0.0


def forecast_daily_volume(
	forecast_date: date,
	daily_data: Dict[str, Dict],
	holiday_impacts: Dict[str, Dict],
	monthly_mrr: Optional[Dict[str, Dict]] = None,
	mrr_correlation: Optional[Dict[str, float]] = None,
	days_ahead: int = 0
) -> Dict[str, float]:
	"""
	Forecast chat volume for a specific date.
	
	Args:
		forecast_date: Date to forecast
		daily_data: Historical daily aggregates
		holiday_impacts: Holiday impact multipliers
		monthly_mrr: Optional monthly MRR data for revenue-based adjustment
		mrr_correlation: Optional MRR correlation data
		days_ahead: Number of days ahead from last historical date
	
	Returns:
		Dict with forecast metrics:
		- volume: Projected daily chat volume
		- confidence_lower: Lower bound (80% confidence)
		- confidence_upper: Upper bound (80% confidence)
		- components: Breakdown of forecast components
	"""
	# Calculate baseline and patterns
	baseline = calculate_baseline_volume(daily_data, days=60)
	trend = calculate_trend(daily_data, days=30)
	day_patterns = calculate_day_of_week_patterns(daily_data)
	month_patterns = calculate_month_patterns(daily_data)
	
	# Start with baseline
	forecast = baseline
	
	# Apply trend (compound daily growth)
	if trend != 0:
		growth_factor = 1 + (trend / 100)
		forecast = forecast * (growth_factor ** days_ahead)
	
	# Apply day of week pattern
	weekday = forecast_date.weekday()
	day_multiplier = day_patterns.get(weekday, 1.0)
	forecast = forecast * day_multiplier
	
	# Apply month pattern
	month = forecast_date.month
	month_multiplier = month_patterns.get(month, 1.0)
	forecast = forecast * month_multiplier
	
	# Apply holiday adjustment
	holiday_adj = get_holiday_adjustment(forecast_date, holiday_impacts)
	forecast = forecast * holiday_adj['volume_multiplier']
	
	# Apply revenue-based adjustment if available
	revenue_adjustment = 1.0
	if monthly_mrr and mrr_correlation:
		month_key = forecast_date.strftime('%Y-%m')
		if month_key in monthly_mrr:
			mrr = monthly_mrr[month_key]['total_mrr']
			estimated_from_mrr = estimate_chat_volume_from_mrr(mrr, mrr_correlation)
			if estimated_from_mrr > 0 and forecast > 0:
				# Blend historical forecast with revenue-based estimate
				revenue_weight = 0.3  # 30% weight on revenue estimate
				forecast = (1 - revenue_weight) * forecast + revenue_weight * estimated_from_mrr
	
	# Calculate confidence interval (simplified)
	# Use historical volatility
	sorted_dates = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	if sorted_dates:
		recent_volumes = [daily_data[d]['total_chats'] for d in sorted_dates[-30:]]
		if recent_volumes:
			std_dev = statistics.stdev(recent_volumes) if len(recent_volumes) > 1 else 0.0
			# 80% confidence interval (approximately 1.28 standard deviations)
			confidence_range = std_dev * 1.28
			confidence_lower = max(0, forecast - confidence_range)
			confidence_upper = forecast + confidence_range
		else:
			confidence_lower = forecast * 0.8
			confidence_upper = forecast * 1.2
	else:
		confidence_lower = forecast * 0.8
		confidence_upper = forecast * 1.2
	
	return {
		'volume': max(0, forecast),
		'confidence_lower': max(0, confidence_lower),
		'confidence_upper': max(0, confidence_upper),
		'components': {
			'baseline': baseline,
			'trend_factor': (1 + (trend / 100)) ** days_ahead if trend != 0 else 1.0,
			'day_multiplier': day_multiplier,
			'month_multiplier': month_multiplier,
			'holiday_multiplier': holiday_adj['volume_multiplier'],
			'revenue_adjustment': revenue_adjustment,
		}
	}


def generate_forecast(
	start_date: date,
	end_date: date,
	daily_data: Dict[str, Dict],
	holiday_impacts: Dict[str, Dict],
	monthly_mrr: Optional[Dict[str, Dict]] = None,
	mrr_correlation: Optional[Dict[str, float]] = None
) -> List[Dict[str, any]]:
	"""
	Generate daily forecasts for a date range.
	
	Returns list of forecast dicts, one per day.
	"""
	# Find last historical date
	sorted_dates = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	if not sorted_dates:
		raise ValueError("No historical data available")
	
	last_historical_date = daily_data[sorted_dates[-1]]['date']
	
	forecasts = []
	current_date = start_date
	
	while current_date <= end_date:
		days_ahead = (current_date - last_historical_date).days
		
		forecast = forecast_daily_volume(
			current_date,
			daily_data,
			holiday_impacts,
			monthly_mrr,
			mrr_correlation,
			days_ahead
		)
		
		forecasts.append({
			'date': current_date,
			'projected_chats': forecast['volume'],
			'confidence_lower': forecast['confidence_lower'],
			'confidence_upper': forecast['confidence_upper'],
			'is_holiday': get_holiday_type(current_date) is not None,
			'holiday_type': get_holiday_type(current_date),
			'components': forecast['components'],
		})
		
		current_date += timedelta(days=1)
	
	return forecasts

