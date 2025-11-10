"""
Holiday season impact analysis for support headcount forecasting.

Identifies holiday periods and calculates impact multipliers for volume,
CSAT, and SLA performance.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import statistics


def get_thanksgiving_date(year: int) -> date:
	"""Calculate Thanksgiving date (4th Thursday in November)."""
	# Start with Nov 1
	nov_1 = date(year, 11, 1)
	# Find first Thursday
	days_until_thursday = (3 - nov_1.weekday()) % 7
	first_thursday = nov_1 + timedelta(days=days_until_thursday)
	# Add 3 weeks to get 4th Thursday
	return first_thursday + timedelta(days=21)


def get_thanksgiving_week(year: int) -> Tuple[date, date]:
	"""Get Thanksgiving week (Monday to Sunday containing Thanksgiving)."""
	thanksgiving = get_thanksgiving_date(year)
	# Get Monday of that week
	days_since_monday = thanksgiving.weekday()
	monday = thanksgiving - timedelta(days=days_since_monday)
	sunday = monday + timedelta(days=6)
	return monday, sunday


def get_christmas_period(year: int) -> Tuple[date, date]:
	"""
	Get holiday break period (Dec 21 - Jan 2).
	Based on support policies: "between 12/21 and 1/2"
	"""
	start = date(year, 12, 21)
	end = date(year + 1, 1, 2)
	return start, end


def is_thanksgiving_week(check_date: date) -> bool:
	"""Check if date falls within Thanksgiving week."""
	year = check_date.year
	monday, sunday = get_thanksgiving_week(year)
	return monday <= check_date <= sunday


def is_thanksgiving_day(check_date: date) -> bool:
	"""Check if date is Thanksgiving Day."""
	return check_date == get_thanksgiving_date(check_date.year)


def is_day_after_thanksgiving(check_date: date) -> bool:
	"""Check if date is day after Thanksgiving."""
	thanksgiving = get_thanksgiving_date(check_date.year)
	return check_date == thanksgiving + timedelta(days=1)


def is_christmas_period(check_date: date) -> bool:
	"""Check if date falls within holiday break (Dec 21 - Jan 2)."""
	year = check_date.year
	start, end = get_christmas_period(year)
	return start <= check_date <= end


def is_christmas_day(check_date: date) -> bool:
	"""Check if date is Christmas Day."""
	return check_date.month == 12 and check_date.day == 25


def is_new_years_day(check_date: date) -> bool:
	"""Check if date is New Year's Day."""
	return check_date.month == 1 and check_date.day == 1


def get_holiday_type(check_date: date) -> Optional[str]:
	"""
	Get holiday type for a given date.
	
	Returns:
		'thanksgiving' - Thanksgiving Day
		'day_after_thanksgiving' - Day after Thanksgiving
		'thanksgiving_week' - Other days in Thanksgiving week
		'christmas' - Christmas Day
		'new_years' - New Year's Day
		'holiday_break' - Other days in Dec 21 - Jan 2 period
		None - Not a holiday
	"""
	if is_thanksgiving_day(check_date):
		return 'thanksgiving'
	if is_day_after_thanksgiving(check_date):
		return 'day_after_thanksgiving'
	if is_christmas_day(check_date):
		return 'christmas'
	if is_new_years_day(check_date):
		return 'new_years'
	if is_thanksgiving_week(check_date):
		return 'thanksgiving_week'
	if is_christmas_period(check_date):
		return 'holiday_break'
	return None


def calculate_holiday_impact(
	daily_data: Dict[str, Dict],
	holiday_type: str,
	baseline_days: Optional[List[str]] = None
) -> Dict[str, float]:
	"""
	Calculate impact multipliers for a specific holiday type.
	
	Args:
		daily_data: Daily aggregates dict (date -> metrics)
		holiday_type: Type of holiday ('thanksgiving', 'christmas', etc.)
		baseline_days: Optional list of date keys to use as baseline
			If None, uses all non-holiday days
	
	Returns:
		Dict with impact multipliers:
		- volume_multiplier: Ratio of holiday volume to baseline
		- csat_impact: Difference in CSAT (holiday - baseline)
		- sla_impact: Difference in SLA adherence % (holiday - baseline)
		- avg_ir_impact: Difference in avg IR minutes (holiday - baseline)
	"""
	# Identify holiday days
	holiday_days = []
	for date_key, data in daily_data.items():
		check_date = data['date']
		if check_date and get_holiday_type(check_date) == holiday_type:
			holiday_days.append(date_key)
	
	if not holiday_days:
		return {
			'volume_multiplier': 1.0,
			'csat_impact': 0.0,
			'sla_impact': 0.0,
			'avg_ir_impact': 0.0,
			'sample_size': 0,
		}
	
	# Get baseline days
	if baseline_days is None:
		baseline_days = [
			date_key for date_key, data in daily_data.items()
			if data['date'] and get_holiday_type(data['date']) is None
		]
	
	if not baseline_days:
		return {
			'volume_multiplier': 1.0,
			'csat_impact': 0.0,
			'sla_impact': 0.0,
			'avg_ir_impact': 0.0,
			'sample_size': len(holiday_days),
		}
	
	# Calculate holiday metrics
	holiday_volumes = [daily_data[d]['total_chats'] for d in holiday_days if d in daily_data]
	holiday_csats = [
		daily_data[d]['avg_csat'] for d in holiday_days
		if d in daily_data and daily_data[d]['avg_csat'] is not None
	]
	holiday_slas = [
		daily_data[d]['sla_adherence_pct'] for d in holiday_days
		if d in daily_data and daily_data[d]['sla_adherence_pct'] is not None
	]
	holiday_irs = [
		daily_data[d]['avg_ir_minutes'] for d in holiday_days
		if d in daily_data and daily_data[d]['avg_ir_minutes'] is not None
	]
	
	# Calculate baseline metrics
	baseline_volumes = [daily_data[d]['total_chats'] for d in baseline_days if d in daily_data]
	baseline_csats = [
		daily_data[d]['avg_csat'] for d in baseline_days
		if d in daily_data and daily_data[d]['avg_csat'] is not None
	]
	baseline_slas = [
		daily_data[d]['sla_adherence_pct'] for d in baseline_days
		if d in daily_data and daily_data[d]['sla_adherence_pct'] is not None
	]
	baseline_irs = [
		daily_data[d]['avg_ir_minutes'] for d in baseline_days
		if d in daily_data and daily_data[d]['avg_ir_minutes'] is not None
	]
	
	# Calculate multipliers and impacts
	avg_holiday_volume = statistics.mean(holiday_volumes) if holiday_volumes else 0
	avg_baseline_volume = statistics.mean(baseline_volumes) if baseline_volumes else 1
	
	volume_multiplier = avg_holiday_volume / avg_baseline_volume if avg_baseline_volume > 0 else 1.0
	
	avg_holiday_csat = statistics.mean(holiday_csats) if holiday_csats else None
	avg_baseline_csat = statistics.mean(baseline_csats) if baseline_csats else None
	csat_impact = (avg_holiday_csat - avg_baseline_csat) if (avg_holiday_csat and avg_baseline_csat) else 0.0
	
	avg_holiday_sla = statistics.mean(holiday_slas) if holiday_slas else None
	avg_baseline_sla = statistics.mean(baseline_slas) if baseline_slas else None
	sla_impact = (avg_holiday_sla - avg_baseline_sla) if (avg_holiday_sla and avg_baseline_sla) else 0.0
	
	avg_holiday_ir = statistics.mean(holiday_irs) if holiday_irs else None
	avg_baseline_ir = statistics.mean(baseline_irs) if baseline_irs else None
	ir_impact = (avg_holiday_ir - avg_baseline_ir) if (avg_holiday_ir and avg_baseline_ir) else 0.0
	
	return {
		'volume_multiplier': volume_multiplier,
		'csat_impact': csat_impact,
		'sla_impact': sla_impact,
		'avg_ir_impact': ir_impact,
		'sample_size': len(holiday_days),
		'avg_holiday_volume': avg_holiday_volume,
		'avg_baseline_volume': avg_baseline_volume,
	}


def analyze_all_holidays(daily_data: Dict[str, Dict]) -> Dict[str, Dict]:
	"""
	Analyze impact of all major holidays.
	
	Returns dict mapping holiday type to impact metrics.
	"""
	holiday_types = [
		'thanksgiving',
		'day_after_thanksgiving',
		'thanksgiving_week',
		'christmas',
		'new_years',
		'holiday_break',
	]
	
	results = {}
	for holiday_type in holiday_types:
		results[holiday_type] = calculate_holiday_impact(daily_data, holiday_type)
	
	return results


def get_holiday_adjustment(date: date, holiday_impacts: Dict[str, Dict]) -> Dict[str, float]:
	"""
	Get holiday adjustment factors for a given date.
	
	Returns dict with adjustment factors:
		- volume_multiplier: Multiplier for expected volume
		- csat_adjustment: Expected CSAT change
		- sla_adjustment: Expected SLA adherence change
		- ir_adjustment: Expected IR time change (minutes)
	"""
	holiday_type = get_holiday_type(date)
	
	if holiday_type and holiday_type in holiday_impacts:
		impact = holiday_impacts[holiday_type]
		return {
			'volume_multiplier': impact['volume_multiplier'],
			'csat_adjustment': impact['csat_impact'],
			'sla_adjustment': impact['sla_impact'],
			'ir_adjustment': impact['avg_ir_impact'],
		}
	
	# No holiday, return neutral adjustments
	return {
		'volume_multiplier': 1.0,
		'csat_adjustment': 0.0,
		'sla_adjustment': 0.0,
		'ir_adjustment': 0.0,
	}

