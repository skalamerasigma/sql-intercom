"""
Demo data generator for testing the dashboard without Intercom API access.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

from .config import TEAM_ID, SLA_FIRST_RESPONSE_MINUTES, BUSINESS_TZ


def generate_demo_metrics() -> Dict[str, Any]:
	"""Generate realistic demo metrics data."""
	now = int(time.time())
	
	# Generate totals with some variation
	open_total = random.randint(180, 280)
	snoozed_total = random.randint(50, 90)
	unassigned_open = random.randint(15, 35)
	waiting_first_reply = random.randint(18, 28)
	
	# Generate wait times (in minutes)
	avg_wait_minutes = round(random.uniform(0.5, 8.0), 2)
	p95_wait_minutes = round(random.uniform(avg_wait_minutes * 1.5, avg_wait_minutes * 3), 2)
	
	# Generate SLA metrics
	sla_adherence = round(random.uniform(85, 100), 2)
	sla_sample_size = random.randint(15, 45)
	
	# Generate ratings
	num_rated = random.randint(2, 8)
	num_positive = random.randint(int(num_rated * 0.6), num_rated)
	num_negative = num_rated - num_positive
	
	# Generate top 10 waiting conversations
	top_10_waiting = []
	for i in range(10):
		wait_minutes = round(random.uniform(5, 45), 1)
		assigned = random.choice([True, False])
		is_priority = random.choice([True, False, False])  # ~33% chance of being priority
		admin_name = random.choice([
			"Erica Chase", "Stipo Josipovic", "Alex Johnson", 
			"Sarah Martinez", "Mike Chen", None
		]) if assigned else None
		top_10_waiting.append({
			"conversation_id": f"demo_conv_{i+1}",
			"wait_minutes": wait_minutes,
			"admin_name": admin_name,
			"admin_email": f"{admin_name.lower().replace(' ', '.')}@sigmacomputing.com" if admin_name else None,
			"assigned": assigned,
			"priority": is_priority,
			"intercom_url": f"https://app.intercom.com/a/inbox/demo_conv_{i+1}",
		})
	top_10_waiting.sort(key=lambda x: x["wait_minutes"], reverse=True)
	
	# Generate priority waiting conversations
	priority_count = random.randint(2, 8)
	priority_conversations = []
	for i in range(priority_count):
		wait_minutes = round(random.uniform(3, 30), 1)
		assigned = random.choice([True, False])
		admin_name = random.choice([
			"Erica Chase", "Stipo Josipovic", "Alex Johnson", 
			"Sarah Martinez", "Mike Chen", None
		]) if assigned else None
		contact_name = random.choice([
			"John Smith", "Jane Doe", "Robert Johnson", "Emily Davis",
			"Michael Brown", "Sarah Wilson", "David Lee", "Lisa Anderson"
		])
		contact_email = f"{contact_name.lower().replace(' ', '.')}@example.com"
		title = random.choice([
			"Account access issue",
			"Billing question",
			"Feature request",
			"Technical support needed",
			"Product inquiry",
			"Integration help",
		])
		priority_conversations.append({
			"conversation_id": f"demo_priority_{i+1}",
			"wait_minutes": wait_minutes,
			"admin_name": admin_name,
			"admin_email": f"{admin_name.lower().replace(' ', '.')}@sigmacomputing.com" if admin_name else None,
			"assigned": assigned,
			"intercom_url": f"https://app.intercom.com/a/inbox/demo_priority_{i+1}",
			"contact_name": contact_name,
			"contact_email": contact_email,
			"title": title,
		})
	priority_conversations.sort(key=lambda x: x["wait_minutes"], reverse=True)
	
	return {
		"generated_at": now,
		"team_id": TEAM_ID,
		"totals": {
			"open": open_total,
			"snoozed": snoozed_total,
			"unassigned_open": unassigned_open,
			"waiting_first_reply": waiting_first_reply,
		},
		"wait_times": {
			"average_minutes": avg_wait_minutes,
			"p95_minutes": p95_wait_minutes,
		},
		"sla": {
			"first_response_minutes": SLA_FIRST_RESPONSE_MINUTES,
			"adherence_percent": sla_adherence,
			"sample_size": sla_sample_size,
		},
		"ratings": {
			"num_rated": num_rated,
			"positive": num_positive,
			"negative": num_negative,
		},
		"top_10_waiting": top_10_waiting,
		"priority_waiting": {
			"count": priority_count,
			"conversations": priority_conversations,
		},
		"agents": [],
		"agent_assignment_open": {},
		"agent_assignment_snoozed": {},
		"agent_assignment_waiting": {},
	}


def generate_demo_admins() -> List[Dict[str, Any]]:
	"""Generate demo admin/agent data."""
	demo_admins = [
		{
			"type": "admin",
			"id": "2062707",
			"name": "Erica Chase",
			"email": "erica@sigmacomputing.com",
			"away_mode_enabled": False,
			"away_mode_reassign": False,
			"has_inbox_seat": True,
			"team_ids": [TEAM_ID],
			"team_priority_level": {
				"primary_team_ids": [TEAM_ID]
			},
		},
		{
			"type": "admin",
			"id": "2062789",
			"name": "Stipo Josipovic",
			"email": "stipo@sigmacomputing.com",
			"away_mode_enabled": False,
			"away_mode_reassign": False,
			"has_inbox_seat": True,
			"team_ids": [TEAM_ID],
			"team_priority_level": {
				"primary_team_ids": [TEAM_ID]
			},
		},
		{
			"type": "admin",
			"id": "2063001",
			"name": "Alex Johnson",
			"email": "alex@sigmacomputing.com",
			"away_mode_enabled": random.choice([True, False]),
			"away_mode_reassign": False,
			"has_inbox_seat": True,
			"team_ids": [TEAM_ID],
			"team_priority_level": {
				"primary_team_ids": [TEAM_ID]
			},
		},
		{
			"type": "admin",
			"id": "2063002",
			"name": "Sarah Martinez",
			"email": "sarah@sigmacomputing.com",
			"away_mode_enabled": False,
			"away_mode_reassign": False,
			"has_inbox_seat": True,
			"team_ids": [TEAM_ID],
			"team_priority_level": {
				"primary_team_ids": [TEAM_ID]
			},
		},
		{
			"type": "admin",
			"id": "2063003",
			"name": "Mike Chen",
			"email": "mike@sigmacomputing.com",
			"away_mode_enabled": False,
			"away_mode_reassign": False,
			"has_inbox_seat": True,
			"team_ids": [TEAM_ID],
			"team_priority_level": {
				"primary_team_ids": [TEAM_ID]
			},
		},
	]
	
	return demo_admins


def get_demo_agent_assignments() -> Dict[str, Dict[str, int]]:
	"""Generate demo agent assignment counts."""
	demo_admins = generate_demo_admins()
	metrics = generate_demo_metrics()
	
	total_open = metrics["totals"]["open"]
	total_snoozed = metrics["totals"]["snoozed"]
	total_waiting = metrics["totals"]["waiting_first_reply"]
	
	# Distribute conversations across agents
	open_per_agent = max(1, total_open // len(demo_admins))
	snoozed_per_agent = max(0, total_snoozed // len(demo_admins))
	waiting_per_agent = max(0, total_waiting // len(demo_admins))
	
	agent_assignment_open = {}
	agent_assignment_snoozed = {}
	agent_assignment_waiting = {}
	
	for admin in demo_admins:
		admin_id = str(admin["id"])
		agent_assignment_open[admin_id] = max(0, open_per_agent + random.randint(-3, 3))
		agent_assignment_snoozed[admin_id] = max(0, snoozed_per_agent + random.randint(-2, 2))
		agent_assignment_waiting[admin_id] = max(0, waiting_per_agent + random.randint(-2, 2))
	
	return {
		"agent_assignment_open": agent_assignment_open,
		"agent_assignment_snoozed": agent_assignment_snoozed,
		"agent_assignment_waiting": agent_assignment_waiting,
		"unassigned": metrics["totals"]["unassigned_open"],
		"waiting": metrics["totals"]["waiting_first_reply"],
	}


def generate_demo_conversations(today_only: bool = True) -> List[Dict[str, Any]]:
	"""Generate demo conversation objects with proper timestamps for metrics calculation."""
	now = int(time.time())
	local_tz = ZoneInfo(BUSINESS_TZ)
	now_dt = datetime.fromtimestamp(now, tz=timezone.utc).astimezone(local_tz)
	
	# For business hours filtering, use a time within business hours (10 AM - 4 PM)
	# Ensure it's a weekday and within 6am-6pm window
	business_hour = random.randint(10, 16)  # 10 AM to 4 PM
	business_hour_dt = now_dt.replace(hour=business_hour, minute=random.randint(0, 59), second=0, microsecond=0)
	# If current time is before business hours or it's a weekend, use yesterday
	if business_hour_dt > now_dt or (now_dt.weekday() >= 5 and business_hour_dt.weekday() >= 5):
		business_hour_dt -= timedelta(days=1)
	# Ensure it's a weekday
	while business_hour_dt.weekday() >= 5:
		business_hour_dt -= timedelta(days=1)
	business_hour_ts = int(business_hour_dt.timestamp())
	
	conversations = []
	
	# Generate waiting conversations (for wait times)
	for i in range(15):
		wait_minutes = random.uniform(5, 120)
		waiting_since = business_hour_ts - int(wait_minutes * 60)
		updated_at = now if today_only else random.randint(now - 86400 * 7, now)  # Within last week if not today_only
		
		conv = {
			"id": f"demo_waiting_{i}",
			"team_assignee_id": TEAM_ID,
			"state": "open",
			"open": True,
			"waiting_since": waiting_since,
			"updated_at": updated_at,
			"admin_assignee_id": random.choice([None, "2062707", "2062789", "2063001"]),
			"priority": random.choice(["priority", "not_priority"]),
			"statistics": {
				"first_admin_reply_at": None,
			},
			"conversation_rating": None,
		}
		conversations.append(conv)
	
	# Generate conversations with first replies (for SLA)
	for i in range(25):
		wait_minutes = random.uniform(1, 30)
		waiting_since = business_hour_ts - int(wait_minutes * 60)
		first_reply_at = waiting_since + int(random.uniform(1, 20) * 60)
		updated_at = now if today_only else random.randint(now - 86400 * 7, now)
		
		conv = {
			"id": f"demo_sla_{i}",
			"team_assignee_id": TEAM_ID,
			"state": "open",
			"open": True,
			"waiting_since": waiting_since,
			"updated_at": updated_at,
			"admin_assignee_id": random.choice(["2062707", "2062789", "2063001", "2063002"]),
			"priority": random.choice(["priority", "not_priority"]),
			"statistics": {
				"first_admin_reply_at": first_reply_at,
			},
			"conversation_rating": None,
		}
		conversations.append(conv)
	
	# Generate conversations with ratings
	rating_types = [
		{"score": 5, "rating": "positive"},
		{"score": 4, "rating": "positive"},
		{"score": 3, "rating": None},
		{"score": 2, "rating": "negative"},
		{"score": 1, "rating": "negative"},
	]
	for i in range(8):
		updated_at = now if today_only else random.randint(now - 86400 * 7, now)
		rating = random.choice(rating_types)
		
		conv = {
			"id": f"demo_rating_{i}",
			"team_assignee_id": TEAM_ID,
			"state": "open",
			"open": True,
			"waiting_since": business_hour_ts - 3600,
			"updated_at": updated_at,
			"admin_assignee_id": random.choice(["2062707", "2062789", "2063001"]),
			"priority": "not_priority",
			"statistics": {
				"first_admin_reply_at": business_hour_ts - 1800,
			},
			"conversation_rating": rating,
		}
		conversations.append(conv)
	
	return conversations

