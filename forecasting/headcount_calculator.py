"""
Headcount calculation for support team forecasting.

Calculates required TSE headcount based on projected chat volume,
SLA requirements, and productivity constraints.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List
import math

from .data_processor import (
	SUSTAINABLE_CHATS_PER_TSE_PER_DAY,
	MAX_CHATS_PER_TSE_PER_DAY,
	MAX_CHATS_PER_TSE,
	SUPPORT_HOURS_DURATION,
	CSAT_TARGET,
	SLA_IR_SECONDS,
)


def calculate_headcount_from_volume(
	projected_chats: float,
	chats_per_tse_per_day: float = SUSTAINABLE_CHATS_PER_TSE_PER_DAY
) -> int:
	"""
	Calculate required headcount based on daily chat volume.
	
	Args:
		projected_chats: Projected daily chat volume
		chats_per_tse_per_day: Target chats per TSE per day (default: 11)
	
	Returns:
		Required number of TSEs
	"""
	if chats_per_tse_per_day <= 0:
		return 0
	
	return math.ceil(projected_chats / chats_per_tse_per_day)


def calculate_headcount_from_peak_hourly(
	projected_chats: float,
	peak_hour_multiplier: float = 1.5
) -> int:
	"""
	Calculate required headcount based on peak hourly volume.
	
	Assumes peak hour has 1.5x average hourly volume.
	
	Args:
		projected_chats: Projected daily chat volume
		peak_hour_multiplier: Multiplier for peak hour vs average (default: 1.5)
	
	Returns:
		Required number of TSEs for peak hour coverage
	"""
	avg_hourly_chats = projected_chats / SUPPORT_HOURS_DURATION
	peak_hourly_chats = avg_hourly_chats * peak_hour_multiplier
	
	# Each TSE can handle MAX_CHATS_PER_TSE concurrently
	return math.ceil(peak_hourly_chats / MAX_CHATS_PER_TSE)


def calculate_headcount_for_sla(
	projected_chats: float,
	target_response_time_seconds: int = SLA_IR_SECONDS,
	avg_response_time_seconds: float = 30.0
) -> int:
	"""
	Calculate required headcount to meet SLA requirements.
	
	This is a simplified calculation. In reality, SLA adherence
	depends on many factors including queue management, TSE availability, etc.
	
	Args:
		projected_chats: Projected daily chat volume
		target_response_time_seconds: Target initial response time (default: 60s)
		avg_response_time_seconds: Average time to respond (default: 30s)
	
	Returns:
		Estimated required TSEs for SLA coverage
	"""
	# Simplified: assume we need enough TSEs to handle incoming chats
	# within the target response time
	# This is a rough estimate - actual SLA modeling is more complex
	
	# Average chats per hour
	avg_hourly_chats = projected_chats / SUPPORT_HOURS_DURATION
	
	# Time available per TSE per hour (in seconds)
	# Assuming TSEs can respond to multiple chats concurrently
	seconds_per_hour = 3600
	
	# Chats a TSE can handle per hour (simplified)
	# Based on response time and concurrent capacity
	chats_per_tse_per_hour = (seconds_per_hour / avg_response_time_seconds) * MAX_CHATS_PER_TSE
	
	if chats_per_tse_per_hour <= 0:
		return 0
	
	return math.ceil(avg_hourly_chats / chats_per_tse_per_hour)


def calculate_required_headcount(
	projected_chats: float,
	use_sustainable_target: bool = True,
	include_peak_coverage: bool = True,
	include_sla_coverage: bool = True,
	safety_margin: float = 1.1
) -> Dict[str, any]:
	"""
	Calculate required headcount using multiple methods and take the maximum.
	
	Args:
		projected_chats: Projected daily chat volume
		use_sustainable_target: Use sustainable (11) vs max (16) chats per TSE
		include_peak_coverage: Include peak hour coverage requirement
		include_sla_coverage: Include SLA coverage requirement
		safety_margin: Safety margin multiplier (default: 1.1 = 10% buffer)
	
	Returns:
		Dict with headcount calculations and breakdown
	"""
	chats_per_tse = SUSTAINABLE_CHATS_PER_TSE_PER_DAY if use_sustainable_target else MAX_CHATS_PER_TSE_PER_DAY
	
	# Method 1: Volume-based
	headcount_volume = calculate_headcount_from_volume(projected_chats, chats_per_tse)
	
	# Method 2: Peak hourly coverage
	headcount_peak = 0
	if include_peak_coverage:
		headcount_peak = calculate_headcount_from_peak_hourly(projected_chats)
	
	# Method 3: SLA coverage
	headcount_sla = 0
	if include_sla_coverage:
		headcount_sla = calculate_headcount_for_sla(projected_chats)
	
	# Take maximum of all methods
	required_headcount = max(headcount_volume, headcount_peak, headcount_sla)
	
	# Apply safety margin
	required_headcount = math.ceil(required_headcount * safety_margin)
	
	return {
		'required_headcount': required_headcount,
		'headcount_volume': headcount_volume,
		'headcount_peak': headcount_peak,
		'headcount_sla': headcount_sla,
		'projected_chats': projected_chats,
		'chats_per_tse_used': chats_per_tse,
		'safety_margin': safety_margin,
		'breakdown': {
			'volume_based': headcount_volume,
			'peak_coverage': headcount_peak,
			'sla_coverage': headcount_sla,
		}
	}


def estimate_csat_given_headcount(
	projected_chats: float,
	headcount: int,
	baseline_csat: float = CSAT_TARGET
) -> float:
	"""
	Estimate expected CSAT given projected volume and headcount.
	
	Simplified model: CSAT degrades as TSEs become overloaded.
	
	Args:
		projected_chats: Projected daily chat volume
		headcount: Available TSE headcount
		baseline_csat: Baseline CSAT when not overloaded (default: 4.7)
	
	Returns:
		Estimated CSAT rating
	"""
	if headcount <= 0:
		return 0.0
	
	chats_per_tse = projected_chats / headcount
	
	# CSAT degradation model
	# If chats per TSE exceeds sustainable (11), CSAT degrades
	# If exceeds max (16), CSAT degrades more significantly
	if chats_per_tse <= SUSTAINABLE_CHATS_PER_TSE_PER_DAY:
		# Within sustainable range, maintain baseline
		return baseline_csat
	elif chats_per_tse <= MAX_CHATS_PER_TSE_PER_DAY:
		# Between sustainable and max, linear degradation
		overload_ratio = (chats_per_tse - SUSTAINABLE_CHATS_PER_TSE_PER_DAY) / (
			MAX_CHATS_PER_TSE_PER_DAY - SUSTAINABLE_CHATS_PER_TSE_PER_DAY
		)
		# Degrade by up to 0.5 points
		return baseline_csat - (overload_ratio * 0.5)
	else:
		# Exceeds max, significant degradation
		excess_ratio = (chats_per_tse - MAX_CHATS_PER_TSE_PER_DAY) / MAX_CHATS_PER_TSE_PER_DAY
		# Degrade by 0.5 + additional degradation
		return max(0.0, baseline_csat - 0.5 - (excess_ratio * 1.0))


def estimate_sla_adherence_given_headcount(
	projected_chats: float,
	headcount: int,
	baseline_sla_adherence: float = 0.95
) -> float:
	"""
	Estimate expected SLA adherence given projected volume and headcount.
	
	Simplified model: SLA adherence decreases as TSEs become overloaded.
	
	Args:
		projected_chats: Projected daily chat volume
		headcount: Available TSE headcount
		baseline_sla_adherence: Baseline SLA adherence when not overloaded (default: 95%)
	
	Returns:
		Estimated SLA adherence percentage
	"""
	if headcount <= 0:
		return 0.0
	
	chats_per_tse = projected_chats / headcount
	
	# SLA degradation model
	if chats_per_tse <= SUSTAINABLE_CHATS_PER_TSE_PER_DAY:
		# Within sustainable range, maintain baseline
		return baseline_sla_adherence
	elif chats_per_tse <= MAX_CHATS_PER_TSE_PER_DAY:
		# Between sustainable and max, linear degradation
		overload_ratio = (chats_per_tse - SUSTAINABLE_CHATS_PER_TSE_PER_DAY) / (
			MAX_CHATS_PER_TSE_PER_DAY - SUSTAINABLE_CHATS_PER_TSE_PER_DAY
		)
		# Degrade by up to 15 percentage points
		return max(0.0, baseline_sla_adherence - (overload_ratio * 0.15))
	else:
		# Exceeds max, significant degradation
		excess_ratio = (chats_per_tse - MAX_CHATS_PER_TSE_PER_DAY) / MAX_CHATS_PER_TSE_PER_DAY
		# Degrade by 15% + additional degradation
		return max(0.0, baseline_sla_adherence - 0.15 - (excess_ratio * 0.25))


def calculate_headcount_with_quality_metrics(
	projected_chats: float,
	target_csat: float = CSAT_TARGET,
	target_sla_adherence: float = 0.95,
	use_sustainable_target: bool = True,
	safety_margin: float = 1.1
) -> Dict[str, any]:
	"""
	Calculate required headcount ensuring quality metrics are met.
	
	Iteratively finds headcount that meets both CSAT and SLA targets.
	
	Args:
		projected_chats: Projected daily chat volume
		target_csat: Target CSAT rating (default: 4.7)
		target_sla_adherence: Target SLA adherence % (default: 95%)
		use_sustainable_target: Use sustainable chats per TSE
		safety_margin: Safety margin multiplier
	
	Returns:
		Dict with headcount and quality metrics
	"""
	# Start with volume-based calculation
	chats_per_tse = SUSTAINABLE_CHATS_PER_TSE_PER_DAY if use_sustainable_target else MAX_CHATS_PER_TSE_PER_DAY
	initial_headcount = calculate_headcount_from_volume(projected_chats, chats_per_tse)
	
	# Iteratively find headcount that meets quality targets
	headcount = initial_headcount
	max_iterations = 20
	
	for _ in range(max_iterations):
		estimated_csat = estimate_csat_given_headcount(projected_chats, headcount)
		estimated_sla = estimate_sla_adherence_given_headcount(projected_chats, headcount)
		
		# Check if targets are met
		if estimated_csat >= target_csat and estimated_sla >= target_sla_adherence:
			break
		
		# Increase headcount if targets not met
		headcount += 1
	
	# Apply safety margin
	final_headcount = math.ceil(headcount * safety_margin)
	
	# Recalculate metrics with final headcount
	final_csat = estimate_csat_given_headcount(projected_chats, final_headcount)
	final_sla = estimate_sla_adherence_given_headcount(projected_chats, final_headcount)
	
	return {
		'required_headcount': final_headcount,
		'projected_chats': projected_chats,
		'estimated_csat': final_csat,
		'estimated_sla_adherence': final_sla,
		'target_csat': target_csat,
		'target_sla_adherence': target_sla_adherence,
		'meets_csat_target': final_csat >= target_csat,
		'meets_sla_target': final_sla >= target_sla_adherence,
		'chats_per_tse': projected_chats / final_headcount if final_headcount > 0 else 0,
		'safety_margin': safety_margin,
	}

