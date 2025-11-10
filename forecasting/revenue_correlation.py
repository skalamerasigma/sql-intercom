"""
Revenue correlation analysis for support headcount forecasting.

Analyzes relationships between MRR/ARR growth and support chat volume.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import statistics


def correlate_mrr_with_chat_volume(
	daily_data: Dict[str, Dict],
	monthly_mrr: Dict[str, Dict],
	mrr_growth_rates: Dict[str, float]
) -> Dict[str, float]:
	"""
	Correlate monthly MRR growth with chat volume.
	
	Returns correlation metrics and regression coefficients.
	"""
	# Aggregate daily chat volume by month
	monthly_chats = {}
	for date_key, data in daily_data.items():
		if data['date']:
			month_key = data['date'].strftime('%Y-%m')
			if month_key not in monthly_chats:
				monthly_chats[month_key] = {
					'total_chats': 0,
					'avg_daily_chats': [],
					'avg_csat': [],
					'avg_sla': [],
				}
			monthly_chats[month_key]['total_chats'] += data['total_chats']
			monthly_chats[month_key]['avg_daily_chats'].append(data['total_chats'])
			if data['avg_csat']:
				monthly_chats[month_key]['avg_csat'].append(data['avg_csat'])
			if data['sla_adherence_pct']:
				monthly_chats[month_key]['avg_sla'].append(data['sla_adherence_pct'])
	
	# Calculate monthly averages
	for month_key in monthly_chats:
		monthly_chats[month_key]['avg_daily_chats'] = statistics.mean(
			monthly_chats[month_key]['avg_daily_chats']
		)
		if monthly_chats[month_key]['avg_csat']:
			monthly_chats[month_key]['avg_csat'] = statistics.mean(
				monthly_chats[month_key]['avg_csat']
			)
		else:
			monthly_chats[month_key]['avg_csat'] = None
		if monthly_chats[month_key]['avg_sla']:
			monthly_chats[month_key]['avg_sla'] = statistics.mean(
				monthly_chats[month_key]['avg_sla']
			)
		else:
			monthly_chats[month_key]['avg_sla'] = None
	
	# Find overlapping months
	common_months = sorted(set(monthly_chats.keys()) & set(monthly_mrr.keys()))
	
	if len(common_months) < 2:
		return {
			'correlation': 0.0,
			'sample_size': len(common_months),
			'chat_per_mrr_ratio': 0.0,
		}
	
	# Prepare data for correlation
	mrr_values = []
	chat_values = []
	mrr_growth_values = []
	chat_growth_values = []
	
	for i, month_key in enumerate(common_months):
		if month_key in monthly_mrr:
			mrr = monthly_mrr[month_key]['total_mrr']
			chats = monthly_chats[month_key]['avg_daily_chats']
			if mrr > 0 and chats > 0:
				mrr_values.append(mrr)
				chat_values.append(chats)
			
			# Calculate growth rates
			if i > 0:
				prev_month = common_months[i - 1]
				if prev_month in monthly_chats and month_key in monthly_chats:
					prev_chats = monthly_chats[prev_month]['avg_daily_chats']
					curr_chats = monthly_chats[month_key]['avg_daily_chats']
					if prev_chats > 0:
						chat_growth = ((curr_chats - prev_chats) / prev_chats) * 100
						chat_growth_values.append(chat_growth)
						if month_key in mrr_growth_rates:
							mrr_growth_values.append(mrr_growth_rates[month_key])
	
	# Calculate correlation
	if len(mrr_values) < 2 or len(chat_values) < 2:
		return {
			'correlation': 0.0,
			'sample_size': len(common_months),
			'chat_per_mrr_ratio': 0.0,
		}
	
	# Simple correlation coefficient
	correlation = calculate_correlation(mrr_values, chat_values)
	
	# Calculate chat per MRR ratio
	avg_chats = statistics.mean(chat_values)
	avg_mrr = statistics.mean(mrr_values)
	chat_per_mrr_ratio = avg_chats / avg_mrr if avg_mrr > 0 else 0.0
	
	# Calculate growth correlation
	growth_correlation = 0.0
	if len(mrr_growth_values) >= 2 and len(chat_growth_values) >= 2:
		growth_correlation = calculate_correlation(mrr_growth_values, chat_growth_values)
	
	return {
		'correlation': correlation,
		'growth_correlation': growth_correlation,
		'sample_size': len(common_months),
		'chat_per_mrr_ratio': chat_per_mrr_ratio,
		'avg_daily_chats': avg_chats,
		'avg_mrr': avg_mrr,
	}


def correlate_new_customers_with_chat_volume(
	daily_data: Dict[str, Dict],
	monthly_mrr: Dict[str, Dict]
) -> Dict[str, float]:
	"""
	Correlate new customer additions with chat volume.
	"""
	# Aggregate daily chat volume by month
	monthly_chats = {}
	for date_key, data in daily_data.items():
		if data['date']:
			month_key = data['date'].strftime('%Y-%m')
			if month_key not in monthly_chats:
				monthly_chats[month_key] = []
			monthly_chats[month_key].append(data['total_chats'])
	
	# Calculate monthly averages
	for month_key in monthly_chats:
		monthly_chats[month_key] = statistics.mean(monthly_chats[month_key])
	
	# Find overlapping months
	common_months = sorted(set(monthly_chats.keys()) & set(monthly_mrr.keys()))
	
	if len(common_months) < 2:
		return {
			'correlation': 0.0,
			'sample_size': len(common_months),
			'chats_per_new_customer': 0.0,
		}
	
	# Prepare data
	new_customer_counts = []
	chat_values = []
	
	for month_key in common_months:
		if month_key in monthly_mrr:
			new_customers = monthly_mrr[month_key]['new_customer_count']
			chats = monthly_chats[month_key]
			if new_customers > 0 and chats > 0:
				new_customer_counts.append(new_customers)
				chat_values.append(chats)
	
	if len(new_customer_counts) < 2:
		return {
			'correlation': 0.0,
			'sample_size': len(common_months),
			'chats_per_new_customer': 0.0,
		}
	
	# Calculate correlation
	correlation = calculate_correlation(new_customer_counts, chat_values)
	
	# Calculate chats per new customer
	avg_chats = statistics.mean(chat_values)
	avg_new_customers = statistics.mean(new_customer_counts)
	chats_per_new_customer = avg_chats / avg_new_customers if avg_new_customers > 0 else 0.0
	
	return {
		'correlation': correlation,
		'sample_size': len(common_months),
		'chats_per_new_customer': chats_per_new_customer,
		'avg_daily_chats': avg_chats,
		'avg_new_customers': avg_new_customers,
	}


def calculate_correlation(x_values: List[float], y_values: List[float]) -> float:
	"""
	Calculate Pearson correlation coefficient.
	
	Simple implementation without numpy dependency.
	"""
	if len(x_values) != len(y_values) or len(x_values) < 2:
		return 0.0
	
	n = len(x_values)
	mean_x = statistics.mean(x_values)
	mean_y = statistics.mean(y_values)
	
	numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
	
	sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
	sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
	
	denominator = (sum_sq_x * sum_sq_y) ** 0.5
	
	if denominator == 0:
		return 0.0
	
	return numerator / denominator


def estimate_chat_volume_from_mrr(
	mrr: float,
	correlation_data: Dict[str, float]
) -> float:
	"""
	Estimate expected daily chat volume based on MRR.
	
	Uses the chat_per_mrr_ratio from correlation analysis.
	"""
	ratio = correlation_data.get('chat_per_mrr_ratio', 0.0)
	return mrr * ratio


def estimate_chat_volume_from_new_customers(
	new_customers: int,
	correlation_data: Dict[str, float]
) -> float:
	"""
	Estimate expected daily chat volume based on new customer count.
	"""
	ratio = correlation_data.get('chats_per_new_customer', 0.0)
	return new_customers * ratio

