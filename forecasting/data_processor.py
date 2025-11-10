"""
Data processing utilities for support headcount forecasting.

Handles loading and cleaning of Intercom conversations and MRR data,
creates daily aggregates and feature engineering.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


# Constants from support policies
CSAT_TARGET = 4.7
SLA_IR_SECONDS = 60  # 1 minute initial response
MAX_CHATS_PER_TSE = 5
SUSTAINABLE_CHATS_PER_TSE_PER_DAY = 11  # Average of 10-12
MAX_CHATS_PER_TSE_PER_DAY = 16
SUPPORT_HOURS_START = 2  # 2am PT
SUPPORT_HOURS_END = 18  # 6pm PT
SUPPORT_HOURS_DURATION = 16  # hours


def parse_date(date_str: str) -> Optional[datetime]:
	"""Parse date string in various formats."""
	if not date_str or date_str.strip() == '':
		return None
	
	# Try common formats
	formats = [
		'%m/%d/%Y %H:%M:%S',
		'%Y-%m-%d %H:%M:%S',
		'%Y-%m-%d',
		'%m/%d/%Y',
	]
	
	for fmt in formats:
		try:
			return datetime.strptime(date_str.strip(), fmt)
		except ValueError:
			continue
	
	return None


def parse_float(value: str) -> Optional[float]:
	"""Parse float value, handling empty strings and commas."""
	if not value or value.strip() == '':
		return None
	try:
		# Remove commas and whitespace
		cleaned = value.strip().replace(',', '')
		return float(cleaned)
	except ValueError:
		return None


def parse_int(value: str) -> Optional[int]:
	"""Parse int value, handling empty strings."""
	if not value or value.strip() == '':
		return None
	try:
		return int(value.strip())
	except ValueError:
		return None


def load_conversations_csv(filepath: str) -> List[Dict]:
	"""Load Intercom conversations CSV file."""
	conversations = []
	
	with open(filepath, 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			# Parse key fields
			conv = {
				'conversation_id': row.get('Conversation Id', '').strip(),
				'created_at': parse_date(row.get('Conversation Created PT', '')),
				'tse_assigned': row.get('TSE Assigned to', '').strip(),
				'tse_rated': row.get('TSE Rated', '').strip(),
				'rating': parse_float(row.get('Rating', '')),
				'ir_seconds': parse_float(row.get('IR (s)', '')) or parse_float(row.get('Adjusted IR (s)', '')),
				'waiting_time_seconds': parse_float(row.get('Waiting Time (s)', '')),
				'waiting_time_minutes': parse_float(row.get('Waiting Time (min)', '')),
				'week_of_conversation': row.get('Week of Conversation', '').strip(),
				'fiscal_quarter': row.get('Fiscal Q', '').strip(),
				'fiscal_quarter_month': row.get('Fiscal Quarter Month', '').strip(),
				'closed_same_day': row.get('Closed Same Day?', '').strip().upper() == 'TRUE',
				'status': row.get('Intercom Chat Status', '').strip().lower(),
			}
			
			# Only include conversations with valid dates
			if conv['created_at']:
				conversations.append(conv)
	
	return conversations


def load_mrr_csv(filepath: str) -> List[Dict]:
	"""Load Monthly Recurring Revenue CSV file."""
	mrr_records = []
	
	with open(filepath, 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			# Parse key fields
			record = {
				'revenue_month': parse_date(row.get('Revenue Calendar Month', '')),
				'fiscal_quarter': row.get('Revenue Fiscal Quarter', '').strip(),
				'fiscal_year': row.get('Revenue Fiscal Year', '').strip(),
				'account_guid': row.get('Account Guid', '').strip(),
				'account_name': row.get('Account Name', '').strip(),
				'mrr': parse_float(row.get('Mrr', '')),
				'arr': parse_float(row.get('Arr', '')),
				'customer_is_active': row.get('Customer Is Active', '').strip() == '1',
				'customer_is_new': row.get('Customer Is New', '').strip() == '1',
				'customer_is_returning': row.get('Customer Is Returning', '').strip() == '1',
			}
			
			# Only include records with valid dates
			if record['revenue_month']:
				mrr_records.append(record)
	
	return mrr_records


def create_daily_aggregates(conversations: List[Dict]) -> Dict[str, Dict]:
	"""
	Create daily aggregates from conversations.
	
	Returns dict mapping date (YYYY-MM-DD) to daily metrics.
	"""
	daily_data = defaultdict(lambda: {
		'date': None,
		'total_chats': 0,
		'rated_chats': 0,
		'ratings': [],
		'ir_times': [],
		'sla_met': 0,
		'sla_total': 0,
		'tse_chat_counts': defaultdict(int),  # TSE -> chat count
		'unique_tses': set(),
	})
	
	for conv in conversations:
		date_key = conv['created_at'].strftime('%Y-%m-%d')
		daily = daily_data[date_key]
		
		if daily['date'] is None:
			daily['date'] = conv['created_at'].date()
		
		daily['total_chats'] += 1
		
		# Track TSE assignments
		if conv['tse_assigned']:
			daily['unique_tses'].add(conv['tse_assigned'])
			daily['tse_chat_counts'][conv['tse_assigned']] += 1
		
		# Track ratings
		if conv['rating'] is not None:
			daily['rated_chats'] += 1
			daily['ratings'].append(conv['rating'])
		
		# Track IR times
		if conv['ir_seconds'] is not None:
			daily['ir_times'].append(conv['ir_seconds'])
			daily['sla_total'] += 1
			if conv['ir_seconds'] <= SLA_IR_SECONDS:
				daily['sla_met'] += 1
	
	# Convert to final format and calculate aggregates
	result = {}
	for date_key, daily in daily_data.items():
		ratings = daily['ratings']
		ir_times = daily['ir_times']
		
		# Calculate TSE productivity
		tse_chat_counts = list(daily['tse_chat_counts'].values())
		avg_chats_per_tse = statistics.mean(tse_chat_counts) if tse_chat_counts else 0
		
		result[date_key] = {
			'date': daily['date'],
			'total_chats': daily['total_chats'],
			'avg_csat': statistics.mean(ratings) if ratings else None,
			'num_rated': len(ratings),
			'avg_ir_seconds': statistics.mean(ir_times) if ir_times else None,
			'avg_ir_minutes': (statistics.mean(ir_times) / 60) if ir_times else None,
			'sla_adherence_pct': (daily['sla_met'] / daily['sla_total'] * 100) if daily['sla_total'] > 0 else None,
			'sla_met': daily['sla_met'],
			'sla_total': daily['sla_total'],
			'unique_tses': len(daily['unique_tses']),
			'avg_chats_per_tse': avg_chats_per_tse,
			'max_chats_per_tse': max(tse_chat_counts) if tse_chat_counts else 0,
		}
	
	return result


def aggregate_mrr_by_month(mrr_records: List[Dict]) -> Dict[str, Dict]:
	"""
	Aggregate MRR data by month.
	
	Returns dict mapping month (YYYY-MM) to monthly metrics.
	"""
	monthly_data = defaultdict(lambda: {
		'month': None,
		'total_mrr': 0.0,
		'total_arr': 0.0,
		'active_customers': set(),
		'new_customers': set(),
		'returning_customers': set(),
	})
	
	for record in mrr_records:
		month_key = record['revenue_month'].strftime('%Y-%m')
		monthly = monthly_data[month_key]
		
		if monthly['month'] is None:
			monthly['month'] = record['revenue_month'].replace(day=1).date()
		
		if record['mrr']:
			monthly['total_mrr'] += record['mrr']
		if record['arr']:
			monthly['total_arr'] += record['arr']
		
		if record['customer_is_active']:
			monthly['active_customers'].add(record['account_guid'])
		if record['customer_is_new']:
			monthly['new_customers'].add(record['account_guid'])
		if record['customer_is_returning']:
			monthly['returning_customers'].add(record['account_guid'])
	
	# Convert to final format
	result = {}
	for month_key, monthly in monthly_data.items():
		result[month_key] = {
			'month': monthly['month'],
			'total_mrr': monthly['total_mrr'],
			'total_arr': monthly['total_arr'],
			'active_customer_count': len(monthly['active_customers']),
			'new_customer_count': len(monthly['new_customers']),
			'returning_customer_count': len(monthly['returning_customers']),
		}
	
	return result


def calculate_mrr_growth_rates(monthly_mrr: Dict[str, Dict]) -> Dict[str, float]:
	"""
	Calculate month-over-month MRR growth rates.
	
	Returns dict mapping month (YYYY-MM) to growth rate percentage.
	"""
	sorted_months = sorted(monthly_mrr.keys())
	growth_rates = {}
	
	for i in range(1, len(sorted_months)):
		current_month = sorted_months[i]
		prev_month = sorted_months[i - 1]
		
		current_mrr = monthly_mrr[current_month]['total_mrr']
		prev_mrr = monthly_mrr[prev_month]['total_mrr']
		
		if prev_mrr > 0:
			growth_rate = ((current_mrr - prev_mrr) / prev_mrr) * 100
			growth_rates[current_month] = growth_rate
		else:
			growth_rates[current_month] = 0.0
	
	return growth_rates


def get_date_range(daily_data: Dict[str, Dict]) -> Tuple[datetime, datetime]:
	"""Get the date range from daily data."""
	if not daily_data:
		raise ValueError("No daily data available")
	
	dates = [data['date'] for data in daily_data.values() if data['date']]
	if not dates:
		raise ValueError("No valid dates in daily data")
	
	min_date = min(dates)
	max_date = max(dates)
	
	return datetime.combine(min_date, datetime.min.time()), datetime.combine(max_date, datetime.min.time())

