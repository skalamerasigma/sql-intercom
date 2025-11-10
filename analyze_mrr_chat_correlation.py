"""
Analyze correlation between MRR and Chat Volume from CSV files.

This script analyzes the relationship between Monthly Recurring Revenue (MRR)
and Intercom chat/conversation volume to identify correlations.
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple
import json


def load_mrr_data(file_path: str) -> Dict[str, Dict]:
	"""
	Load MRR data from CSV and aggregate by month.
	
	Returns dict with month keys (YYYY-MM) containing:
	- total_mrr: Sum of all MRR for that month
	- account_count: Number of unique accounts
	- avg_mrr_per_account: Average MRR per account
	"""
	mrr_by_month = defaultdict(lambda: {
		'total_mrr': 0.0,
		'accounts': set(),
		'mrr_values': []
	})
	
	with open(file_path, 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			try:
				# Parse date from Revenue Calendar Month
				date_str = row.get('Revenue Calendar Month', '').strip()
				if not date_str:
					continue
				
				# Parse date (format: YYYY-MM-DD)
				date_obj = datetime.strptime(date_str, '%Y-%m-%d')
				month_key = date_obj.strftime('%Y-%m')
				
				# Get MRR value
				mrr_str = row.get('Mrr', '').strip()
				if mrr_str:
					mrr = float(mrr_str)
					if mrr > 0:
						mrr_by_month[month_key]['total_mrr'] += mrr
						mrr_by_month[month_key]['mrr_values'].append(mrr)
						
						# Track unique accounts
						account_id = row.get('Account Guid', '').strip()
						if account_id:
							mrr_by_month[month_key]['accounts'].add(account_id)
			except (ValueError, KeyError) as e:
				# Skip rows with invalid data
				continue
	
	# Convert sets to counts and calculate averages
	result = {}
	for month_key, data in mrr_by_month.items():
		result[month_key] = {
			'total_mrr': data['total_mrr'],
			'account_count': len(data['accounts']),
			'avg_mrr_per_account': data['total_mrr'] / len(data['accounts']) if data['accounts'] else 0.0,
			'mrr_values': data['mrr_values']
		}
	
	return result


def load_conversation_data(file_path: str) -> Dict[str, Dict]:
	"""
	Load conversation data from CSV and aggregate by month.
	
	Returns dict with month keys (YYYY-MM) containing:
	- total_conversations: Total number of conversations
	- closed_conversations: Number of closed conversations
	- open_conversations: Number of open conversations
	"""
	conversations_by_month = defaultdict(lambda: {
		'total': 0,
		'closed': 0,
		'open': 0,
		'dates': []
	})
	
	with open(file_path, 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			try:
				# Parse date from Conversation Created PT
				date_str = row.get('Conversation Created PT', '').strip()
				if not date_str:
					continue
				
				# Parse date (format: M/D/YYYY H:MM:SS)
				date_obj = datetime.strptime(date_str, '%m/%d/%Y %H:%M:%S')
				month_key = date_obj.strftime('%Y-%m')
				
				conversations_by_month[month_key]['total'] += 1
				conversations_by_month[month_key]['dates'].append(date_obj)
				
				# Check status
				status = row.get('Intercom Chat Status', '').strip().lower()
				if status == 'closed':
					conversations_by_month[month_key]['closed'] += 1
				elif status == 'open':
					conversations_by_month[month_key]['open'] += 1
			except (ValueError, KeyError) as e:
				# Skip rows with invalid data
				continue
	
	# Convert to final format
	result = {}
	for month_key, data in conversations_by_month.items():
		result[month_key] = {
			'total_conversations': data['total'],
			'closed_conversations': data['closed'],
			'open_conversations': data['open'],
			'days_with_conversations': len(set(d.date() for d in data['dates'])),
			'avg_daily_conversations': data['total'] / len(set(d.date() for d in data['dates'])) if data['dates'] else 0.0
		}
	
	return result


def calculate_correlation(x_values: List[float], y_values: List[float]) -> Tuple[float, Dict]:
	"""
	Calculate Pearson correlation coefficient and statistics.
	
	Returns:
		(correlation_coefficient, statistics_dict)
	"""
	if len(x_values) != len(y_values) or len(x_values) < 2:
		return 0.0, {
			'error': 'Insufficient data points',
			'x_count': len(x_values),
			'y_count': len(y_values)
		}
	
	n = len(x_values)
	mean_x = statistics.mean(x_values)
	mean_y = statistics.mean(y_values)
	
	# Calculate correlation coefficient
	numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
	
	sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
	sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
	
	denominator = (sum_sq_x * sum_sq_y) ** 0.5
	
	if denominator == 0:
		return 0.0, {'error': 'Zero variance in data'}
	
	correlation = numerator / denominator
	
	# Calculate additional statistics
	std_x = statistics.stdev(x_values) if n > 1 else 0.0
	std_y = statistics.stdev(y_values) if n > 1 else 0.0
	
	stats = {
		'correlation': correlation,
		'sample_size': n,
		'mean_x': mean_x,
		'mean_y': mean_y,
		'std_x': std_x,
		'std_y': std_y,
		'min_x': min(x_values),
		'max_x': max(x_values),
		'min_y': min(y_values),
		'max_y': max(y_values),
	}
	
	return correlation, stats


def analyze_correlation(mrr_data: Dict[str, Dict], conversation_data: Dict[str, Dict]) -> Dict:
	"""
	Analyze correlation between MRR and conversation volume.
	
	Returns comprehensive analysis results.
	"""
	# Find common months
	common_months = sorted(set(mrr_data.keys()) & set(conversation_data.keys()))
	
	if len(common_months) < 2:
		return {
			'error': 'Insufficient overlapping months',
			'mrr_months': len(mrr_data),
			'conversation_months': len(conversation_data),
			'common_months': len(common_months)
		}
	
	# Prepare data for correlation analysis
	mrr_values = []
	conversation_values = []
	avg_daily_conversation_values = []
	account_count_values = []
	
	monthly_data = []
	
	for month_key in common_months:
		mrr = mrr_data[month_key]['total_mrr']
		conversations = conversation_data[month_key]['total_conversations']
		avg_daily = conversation_data[month_key]['avg_daily_conversations']
		accounts = mrr_data[month_key]['account_count']
		
		if mrr > 0 and conversations > 0:
			mrr_values.append(mrr)
			conversation_values.append(conversations)
			avg_daily_conversation_values.append(avg_daily)
			account_count_values.append(accounts)
			
			monthly_data.append({
				'month': month_key,
				'total_mrr': mrr,
				'total_conversations': conversations,
				'avg_daily_conversations': avg_daily,
				'account_count': accounts,
				'avg_mrr_per_account': mrr_data[month_key]['avg_mrr_per_account']
			})
	
	# Calculate correlations
	corr_mrr_total, stats_mrr_total = calculate_correlation(mrr_values, conversation_values)
	corr_mrr_daily, stats_mrr_daily = calculate_correlation(mrr_values, avg_daily_conversation_values)
	corr_accounts_conversations, stats_accounts_conversations = calculate_correlation(
		account_count_values, conversation_values
	)
	
	# Calculate ratios
	avg_mrr = statistics.mean(mrr_values) if mrr_values else 0.0
	avg_conversations = statistics.mean(conversation_values) if conversation_values else 0.0
	avg_daily_conversations = statistics.mean(avg_daily_conversation_values) if avg_daily_conversation_values else 0.0
	
	conversations_per_mrr = avg_conversations / avg_mrr if avg_mrr > 0 else 0.0
	conversations_per_account = avg_conversations / statistics.mean(account_count_values) if account_count_values else 0.0
	
	return {
		'summary': {
			'common_months': len(common_months),
			'date_range': {
				'start': common_months[0],
				'end': common_months[-1]
			},
			'avg_monthly_mrr': avg_mrr,
			'avg_monthly_conversations': avg_conversations,
			'avg_daily_conversations': avg_daily_conversations,
			'conversations_per_mrr': conversations_per_mrr,
			'conversations_per_account': conversations_per_account
		},
		'correlations': {
			'mrr_vs_total_conversations': {
				'coefficient': corr_mrr_total,
				'strength': interpret_correlation(corr_mrr_total),
				'stats': stats_mrr_total
			},
			'mrr_vs_avg_daily_conversations': {
				'coefficient': corr_mrr_daily,
				'strength': interpret_correlation(corr_mrr_daily),
				'stats': stats_mrr_daily
			},
			'account_count_vs_conversations': {
				'coefficient': corr_accounts_conversations,
				'strength': interpret_correlation(corr_accounts_conversations),
				'stats': stats_accounts_conversations
			}
		},
		'monthly_data': monthly_data
	}


def interpret_correlation(corr: float) -> str:
	"""Interpret correlation coefficient strength."""
	abs_corr = abs(corr)
	if abs_corr >= 0.9:
		return 'Very Strong'
	elif abs_corr >= 0.7:
		return 'Strong'
	elif abs_corr >= 0.5:
		return 'Moderate'
	elif abs_corr >= 0.3:
		return 'Weak'
	else:
		return 'Very Weak'


def print_analysis_report(analysis: Dict):
	"""Print a formatted analysis report."""
	print("=" * 80)
	print("MRR vs CHAT VOLUME CORRELATION ANALYSIS")
	print("=" * 80)
	print()
	
	if 'error' in analysis:
		print(f"ERROR: {analysis['error']}")
		return
	
	summary = analysis['summary']
	print("SUMMARY")
	print("-" * 80)
	print(f"Analysis Period: {summary['date_range']['start']} to {summary['date_range']['end']}")
	print(f"Months Analyzed: {summary['common_months']}")
	print()
	print(f"Average Monthly MRR: ${summary['avg_monthly_mrr']:,.2f}")
	print(f"Average Monthly Conversations: {summary['avg_monthly_conversations']:,.0f}")
	print(f"Average Daily Conversations: {summary['avg_daily_conversations']:.2f}")
	print(f"Conversations per $1 MRR: {summary['conversations_per_mrr']:.4f}")
	print(f"Conversations per Account: {summary['conversations_per_account']:.2f}")
	print()
	
	print("CORRELATION RESULTS")
	print("-" * 80)
	
	correlations = analysis['correlations']
	
	# MRR vs Total Conversations
	mrr_total = correlations['mrr_vs_total_conversations']
	print(f"\n1. MRR vs Total Monthly Conversations:")
	print(f"   Correlation Coefficient: {mrr_total['coefficient']:.4f}")
	print(f"   Strength: {mrr_total['strength']}")
	if 'stats' in mrr_total:
		stats = mrr_total['stats']
		print(f"   Sample Size: {stats.get('sample_size', 'N/A')}")
		print(f"   MRR Range: ${stats.get('min_x', 0):,.0f} - ${stats.get('max_x', 0):,.0f}")
		print(f"   Conversations Range: {stats.get('min_y', 0):,.0f} - {stats.get('max_y', 0):,.0f}")
	
	# MRR vs Daily Average
	mrr_daily = correlations['mrr_vs_avg_daily_conversations']
	print(f"\n2. MRR vs Average Daily Conversations:")
	print(f"   Correlation Coefficient: {mrr_daily['coefficient']:.4f}")
	print(f"   Strength: {mrr_daily['strength']}")
	if 'stats' in mrr_daily:
		stats = mrr_daily['stats']
		print(f"   Sample Size: {stats.get('sample_size', 'N/A')}")
	
	# Account Count vs Conversations
	accounts = correlations['account_count_vs_conversations']
	print(f"\n3. Account Count vs Total Conversations:")
	print(f"   Correlation Coefficient: {accounts['coefficient']:.4f}")
	print(f"   Strength: {accounts['strength']}")
	if 'stats' in accounts:
		stats = accounts['stats']
		print(f"   Sample Size: {stats.get('sample_size', 'N/A')}")
	
	print()
	print("=" * 80)
	print()
	
	# Print monthly breakdown
	print("MONTHLY BREAKDOWN (First 12 months)")
	print("-" * 80)
	print(f"{'Month':<12} {'MRR':<15} {'Conversations':<15} {'Daily Avg':<12} {'Accounts':<10}")
	print("-" * 80)
	
	for data in analysis['monthly_data'][:12]:
		print(f"{data['month']:<12} ${data['total_mrr']:>12,.0f} {data['total_conversations']:>13,.0f} "
		      f"{data['avg_daily_conversations']:>10.2f} {data['account_count']:>9,}")
	
	if len(analysis['monthly_data']) > 12:
		print(f"\n... and {len(analysis['monthly_data']) - 12} more months")
	
	print()


def main():
	"""Main execution function."""
	mrr_file = '/Users/stephen.skalamera/Documents/Projects/Intercom App/MONTHLY_RECURRING_REVENUE.csv'
	conversation_file = '/Users/stephen.skalamera/Documents/Projects/Intercom App/Intercom Conversations - Master Table - Sheet1.csv'
	
	print("Loading MRR data...")
	mrr_data = load_mrr_data(mrr_file)
	print(f"  Loaded MRR data for {len(mrr_data)} months")
	
	print("\nLoading conversation data...")
	conversation_data = load_conversation_data(conversation_file)
	print(f"  Loaded conversation data for {len(conversation_data)} months")
	
	print("\nAnalyzing correlation...")
	analysis = analyze_correlation(mrr_data, conversation_data)
	
	print_analysis_report(analysis)
	
	# Save results to JSON
	output_file = '/Users/stephen.skalamera/Documents/Projects/Intercom App/mrr_chat_correlation_analysis.json'
	with open(output_file, 'w') as f:
		json.dump(analysis, f, indent=2, default=str)
	print(f"\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
	main()

