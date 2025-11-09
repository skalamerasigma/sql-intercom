from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from .config import (
	MAX_CHATS_PER_TSE,
	CAPACITY_WARNING_THRESHOLD,
	CAPACITY_CAUTION_THRESHOLD,
	CAPACITY_CRITICAL_THRESHOLD,
	SNOOZED_PROJECTION_HOURS,
	BUSINESS_TZ,
)


def calculate_capacity_metrics(
	admins: List[Dict[str, Any]],
	team_id: int,
	agent_open_counts: Dict[str, int],
	agent_snoozed_counts: Dict[str, int],
	snoozed_conversations: List[Dict[str, Any]],
	unassigned_open_count: int,
	waiting_first_reply_count: int,
	now_s: Optional[int] = None,
) -> Dict[str, Any]:
	"""
	Calculate capacity metrics and recommendations.
	
	Args:
		admins: List of admin objects from Intercom
		team_id: Team ID to filter by
		agent_open_counts: Dict mapping admin_id -> open chat count
		agent_snoozed_counts: Dict mapping admin_id -> snoozed chat count
		snoozed_conversations: List of snoozed conversation objects (with snoozed_until)
		unassigned_open_count: Total unassigned open conversations
		waiting_first_reply_count: Total waiting for first reply
		now_s: Current timestamp (Unix seconds), defaults to now
	
	Returns:
		Dict with capacity metrics, alert level, and recommendations
	"""
	now = now_s or int(time.time())
	
	# Filter to team members
	def _is_team_member(a: dict) -> bool:
		ids = set(a.get("team_ids") or [])
		pri = set((a.get("team_priority_level") or {}).get("primary_team_ids") or [])
		return (team_id in ids) or (team_id in pri)
	
	team_admins = [a for a in admins if _is_team_member(a)]
	
	# Calculate per-TSE metrics
	tse_details = []
	available_tse_count = 0
	total_open_load = 0
	at_capacity_count = 0
	
	for admin in team_admins:
		admin_id = str(admin.get("id"))
		away = admin.get("away_mode_enabled", False)
		open_chats = agent_open_counts.get(admin_id, 0)
		snoozed_chats = agent_snoozed_counts.get(admin_id, 0)
		
		utilization = (open_chats / MAX_CHATS_PER_TSE) * 100.0 if MAX_CHATS_PER_TSE > 0 else 0.0
		at_capacity = open_chats >= MAX_CHATS_PER_TSE
		
		if not away:
			available_tse_count += 1
			total_open_load += open_chats
			if at_capacity:
				at_capacity_count += 1
		
		tse_details.append({
			"admin_id": admin_id,
			"name": admin.get("name", "Unknown"),
			"open_chats": open_chats,
			"snoozed_chats": snoozed_chats,
			"utilization_percent": round(utilization, 1),
			"status": "at_capacity" if at_capacity else ("away" if away else "available"),
			"away": away,
		})
	
	# Calculate team capacity
	total_capacity = available_tse_count * MAX_CHATS_PER_TSE
	available_capacity = max(0, total_capacity - total_open_load)
	utilization_percent = (total_open_load / total_capacity * 100.0) if total_capacity > 0 else 0.0
	
	# Project snoozed returns
	snoozed_projection = project_snoozed_returns(snoozed_conversations, now)
	
	# Calculate projected load (include unassigned conversations that need to be handled)
	# Unassigned conversations represent work that needs capacity
	projected_load_1h = total_open_load + unassigned_open_count + snoozed_projection["returning_in_1h"]
	projected_load_2h = total_open_load + unassigned_open_count + snoozed_projection["returning_in_2h"]
	
	capacity_needed_1h = math.ceil(projected_load_1h / MAX_CHATS_PER_TSE) if MAX_CHATS_PER_TSE > 0 else 0
	capacity_needed_2h = math.ceil(projected_load_2h / MAX_CHATS_PER_TSE) if MAX_CHATS_PER_TSE > 0 else 0
	
	# Determine alert level and recommendation
	alert_level, status, recommendation = determine_alert_level_and_recommendation(
		utilization_percent,
		available_capacity,
		unassigned_open_count,
		at_capacity_count,
		available_tse_count,
		snoozed_projection,
		capacity_needed_1h,
		capacity_needed_2h,
		waiting_first_reply_count,
	)
	
	return {
		"alert_level": alert_level,
		"status": status,
		"current_capacity": {
			"available_tse_count": available_tse_count,
			"total_tse_count": len(team_admins),
			"away_tse_count": len(team_admins) - available_tse_count,
			"total_capacity": total_capacity,
			"current_load": total_open_load,
			"available_capacity": available_capacity,
			"utilization_percent": round(utilization_percent, 1),
			"at_capacity_tse_count": at_capacity_count,
		},
		"snoozed_projection": snoozed_projection,
		"projected_load": {
			"in_1h": projected_load_1h,
			"in_2h": projected_load_2h,
			"capacity_needed_in_1h": capacity_needed_1h,
			"capacity_needed_in_2h": capacity_needed_2h,
		},
		"recommendation": recommendation,
		"tse_details": tse_details,
		"queue_metrics": {
			"unassigned": unassigned_open_count,
			"waiting_first_reply": waiting_first_reply_count,
		},
	}


def project_snoozed_returns(
	snoozed_conversations: List[Dict[str, Any]],
	now_s: int,
	projection_hours: int = SNOOZED_PROJECTION_HOURS,
) -> Dict[str, int]:
	"""
	Project how many snoozed conversations will return in the next N hours.
	
	Args:
		snoozed_conversations: List of snoozed conversation objects
		now_s: Current timestamp (Unix seconds)
		projection_hours: Number of hours to project ahead
	
	Returns:
		Dict with counts for different time windows
	"""
	now_1h = now_s + (1 * 3600)
	now_2h = now_s + (2 * 3600)
	now_today_end = _get_today_end_timestamp(now_s)
	
	returning_in_1h = 0
	returning_in_2h = 0
	returning_today = 0
	
	for conv in snoozed_conversations:
		snoozed_until = conv.get("snoozed_until")
		if not snoozed_until:
			continue
		
		try:
			snoozed_ts = int(snoozed_until)
			if snoozed_ts <= now_1h:
				returning_in_1h += 1
			if snoozed_ts <= now_2h:
				returning_in_2h += 1
			if snoozed_ts <= now_today_end:
				returning_today += 1
		except (ValueError, TypeError):
			continue
	
	return {
		"returning_in_1h": returning_in_1h,
		"returning_in_2h": returning_in_2h,
		"returning_today": returning_today,
		"total_snoozed": len(snoozed_conversations),
	}


def _get_today_end_timestamp(now_s: int) -> int:
	"""Get timestamp for end of today in business timezone."""
	try:
		tz = ZoneInfo(BUSINESS_TZ)
		now_dt = datetime.fromtimestamp(now_s, tz=timezone.utc).astimezone(tz)
		today_end = datetime.combine(now_dt.date(), datetime.max.time()).replace(tzinfo=tz)
		return int(today_end.timestamp())
	except Exception:
		# Fallback: end of day UTC
		return now_s + (24 * 3600)


def determine_alert_level_and_recommendation(
	utilization_percent: float,
	available_capacity: int,
	unassigned_count: int,
	at_capacity_tse_count: int,
	available_tse_count: int,
	snoozed_projection: Dict[str, int],
	capacity_needed_1h: int,
	capacity_needed_2h: int,
	waiting_first_reply_count: int = 0,
) -> Tuple[str, str, Dict[str, Any]]:
	"""
	Determine alert level and generate recommendation.
	
	Returns:
		Tuple of (alert_level, status, recommendation_dict)
	"""
	utilization_ratio = utilization_percent / 100.0
	
	# Determine alert level
	# Special case: if no TSE's are available but there's work to do, it's always critical
	if available_tse_count == 0:
		if unassigned_count > 0 or waiting_first_reply_count > 0:
			alert_level = "red"
			status = "Critical"
			urgency = "critical"
		else:
			# No work to do, so optimal
			alert_level = "green"
			status = "Optimal"
			urgency = "low"
	elif utilization_ratio >= CAPACITY_CRITICAL_THRESHOLD or unassigned_count > 12 or (available_tse_count > 0 and at_capacity_tse_count >= (available_tse_count * 0.5)):
		alert_level = "red"
		status = "Critical"
		urgency = "critical"
	elif utilization_ratio >= CAPACITY_CAUTION_THRESHOLD or unassigned_count > 7 or at_capacity_tse_count >= 3 or snoozed_projection["returning_in_1h"] > available_capacity:
		alert_level = "orange"
		status = "Caution"
		urgency = "high"
	elif utilization_ratio >= CAPACITY_WARNING_THRESHOLD or unassigned_count > 3 or at_capacity_tse_count >= 2:
		alert_level = "yellow"
		status = "Warning"
		urgency = "medium"
	else:
		alert_level = "green"
		status = "Optimal"
		urgency = "low"
	
	# Generate recommendation
	additional_tse_needed = max(0, capacity_needed_1h - available_tse_count)
	
	if alert_level == "red":
		action = "add_tse"
		# If no TSE's available, ensure we recommend at least enough to handle the work
		if available_tse_count == 0:
			# Calculate minimum TSE's needed based on unassigned conversations
			min_tse_needed = math.ceil(unassigned_count / MAX_CHATS_PER_TSE) if (MAX_CHATS_PER_TSE > 0 and unassigned_count > 0) else 1
			count = max(additional_tse_needed, min_tse_needed)
			reason = f"No TSE's available. {unassigned_count} unassigned conversations need immediate attention."
		else:
			count = max(additional_tse_needed, 1)  # At least 1
			reason = "Critical capacity threshold exceeded. Immediate action required."
	elif alert_level == "orange":
		action = "add_tse" if additional_tse_needed > 0 else "monitor"
		count = additional_tse_needed
		reason = f"Capacity utilization at {utilization_percent:.1f}%. Consider adding TSE's soon."
	elif alert_level == "yellow":
		action = "monitor" if additional_tse_needed == 0 else "add_tse"
		count = additional_tse_needed
		reason = "Capacity utilization approaching threshold. Monitor closely."
	else:
		action = "none"
		count = 0
		reason = "Capacity is optimal. No action needed."
	
	# Adjust reason based on specific conditions
	if snoozed_projection["returning_in_1h"] > available_capacity:
		reason += f" {snoozed_projection['returning_in_1h']} snoozed chats returning in 1h will exceed capacity."
	if unassigned_count > 5:
		reason += f" {unassigned_count} unassigned conversations in queue."
	
	return (
		alert_level,
		status,
		{
			"action": action,
			"count": count,
			"reason": reason.strip(),
			"urgency": urgency,
		},
	)

