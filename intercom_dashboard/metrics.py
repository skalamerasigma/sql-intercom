from __future__ import annotations

import statistics
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import SLA_FIRST_RESPONSE_MINUTES

SECONDS_PER_MINUTE = 60


def _is_waiting_for_first_reply(conv: Dict[str, Any]) -> bool:
	if not conv.get("open", False):
		return False
	stats = conv.get("statistics") or {}
	return stats.get("first_admin_reply_at") in (None, 0)


def _age_minutes_from_waiting_since(conv: Dict[str, Any], now_s: Optional[int] = None) -> Optional[float]:
	waiting_since = conv.get("waiting_since")
	if not waiting_since:
		return None
	now = now_s or int(time.time())
	return max(0.0, (now - int(waiting_since)) / SECONDS_PER_MINUTE)


def _is_unassigned(conv: Dict[str, Any]) -> bool:
	return conv.get("admin_assignee_id") in (None, "", 0)


def _is_snoozed(conv: Dict[str, Any]) -> bool:
	# Count as snoozed if explicit state or snoozed_until has a timestamp
	if conv.get("state") == "snoozed":
		return True
	return bool(conv.get("snoozed_until"))


def _is_open(conv: Dict[str, Any]) -> bool:
	return bool(conv.get("open", False))


def _extract_rating(conv: Dict[str, Any]) -> Optional[Dict[str, Any]]:
	# Intercom returns a `conversation_rating` object when present (OpenAPI shows numeric score)
	rating = conv.get("conversation_rating")
	return rating if isinstance(rating, dict) else None


def _first_response_met_sla(conv: Dict[str, Any], minutes: int) -> Optional[bool]:
	stats = conv.get("statistics") or {}
	first_reply = stats.get("first_admin_reply_at")
	waiting_since = conv.get("waiting_since")
	if not first_reply or not waiting_since:
		return None
	elapsed_min = (int(first_reply) - int(waiting_since)) / SECONDS_PER_MINUTE
	return elapsed_min <= minutes


def _group_by_admin(conversations: Iterable[Dict[str, Any]]) -> Dict[str, int]:
	per_admin: Dict[str, int] = {}
	for c in conversations:
		admin_id = str(c.get("admin_assignee_id") or "")
		if not admin_id:
			continue
		per_admin[admin_id] = per_admin.get(admin_id, 0) + 1
	return per_admin


def compute_metrics(
	conversations: List[Dict[str, Any]],
	admins: List[Dict[str, Any]],
	team_id: int,
	now_s: Optional[int] = None,
) -> Dict[str, Any]:
	return _compute_metrics_internal(conversations, admins, team_id, now_s)


def compute_metrics_with_overrides(
	conversations: List[Dict[str, Any]],
	admins: List[Dict[str, Any]],
	team_id: int,
	snoozed_total_override: Optional[int] = None,
	open_total_override: Optional[int] = None,
	unassigned_total_override: Optional[int] = None,
	waiting_total_override: Optional[int] = None,
	agent_assignment_override: Optional[Dict[str, int]] = None,
	now_s: Optional[int] = None,
) -> Dict[str, Any]:
	return _compute_metrics_internal(
		conversations,
		admins,
		team_id,
		now_s,
		snoozed_total_override,
		open_total_override,
		unassigned_total_override,
		waiting_total_override,
		agent_assignment_override,
	)


def _compute_metrics_internal(
	conversations: List[Dict[str, Any]],
	admins: List[Dict[str, Any]],
	team_id: int,
	now_s: Optional[int] = None,
	snoozed_total_override: Optional[int] = None,
	open_total_override: Optional[int] = None,
	unassigned_total_override: Optional[int] = None,
	waiting_total_override: Optional[int] = None,
	agent_assignment_override: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
	now = now_s or int(time.time())
	open_convs = [c for c in conversations if _is_open(c) and c.get("team_assignee_id") == team_id]
	snoozed_convs = [c for c in conversations if _is_snoozed(c) and c.get("team_assignee_id") == team_id]
	unassigned_open = [c for c in open_convs if _is_unassigned(c)]
	waiting_first_reply = [c for c in open_convs if _is_waiting_for_first_reply(c)]

	wait_times = [
		_age_minutes_from_waiting_since(c, now) for c in waiting_first_reply
	]
	wait_times = [w for w in wait_times if w is not None]
	avg_wait_time_min = statistics.mean(wait_times) if wait_times else 0.0
	p95_wait_time_min = statistics.quantiles(wait_times, n=20)[18] if len(wait_times) >= 20 else (max(wait_times) if wait_times else 0.0)

	# SLA adherence: among conversations that have received first admin reply
	first_reply_samples = [c for c in conversations if (c.get("team_assignee_id") == team_id)]
	sla_results = [_first_response_met_sla(c, SLA_FIRST_RESPONSE_MINUTES) for c in first_reply_samples]
	sla_results = [s for s in sla_results if s is not None]
	sla_adherence_pct = (sum(1 for s in sla_results if s) / len(sla_results) * 100.0) if sla_results else 0.0

	# Ratings
	ratings = [_extract_rating(c) for c in conversations]
	ratings = [r for r in ratings if r]
	num_rated = len(ratings)
	# Prefer numeric score when available (1-5). Fallback to string rating if present.
	def _score_or_polarity(r: Dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
		score = r.get("score")
		if isinstance(score, (int, float)):
			try:
				return int(score), None
			except Exception:
				pass
		polarity = str(r.get("rating") or "").lower()
		return None, polarity

	num_positive = 0
	num_negative = 0
	for r in ratings:
		score, polarity = _score_or_polarity(r)
		if score is not None:
			if score >= 4:
				num_positive += 1
			elif score <= 2:
				num_negative += 1
		else:
			if polarity in ("positive", "good"):
				num_positive += 1
			elif polarity in ("negative", "bad"):
				num_negative += 1

	# Agent roster for the team (filter admins)
	def _is_team_member(a: Dict[str, Any]) -> bool:
		team_ids = set(a.get("team_ids") or [])
		primary = set((a.get("team_priority_level") or {}).get("primary_team_ids") or [])
		return (team_id in team_ids) or (team_id in primary)

	team_admins = [a for a in admins if _is_team_member(a)]
	agent_assignment_counts = agent_assignment_override or _group_by_admin(open_convs)
	agents = []
	for a in team_admins:
		aid = str(a.get("id"))
		agents.append(
			{
				"id": aid,
				"name": a.get("name"),
				"email": a.get("email"),
				"away": bool(a.get("away_mode_enabled")),
				"has_inbox_seat": bool(a.get("has_inbox_seat")),
				"assigned_count": agent_assignment_counts.get(aid, 0),
			}
		)

	return {
		"generated_at": now,
		"team_id": team_id,
		"totals": {
			"open": int(open_total_override) if open_total_override is not None else len(open_convs),
			"snoozed": int(snoozed_total_override) if snoozed_total_override is not None else len(snoozed_convs),
			"unassigned_open": int(unassigned_total_override) if unassigned_total_override is not None else len(unassigned_open),
			"waiting_first_reply": int(waiting_total_override) if waiting_total_override is not None else len(waiting_first_reply),
		},
		"wait_times": {
			"average_minutes": round(avg_wait_time_min, 2),
			"p95_minutes": round(p95_wait_time_min, 2),
		},
		"sla": {
			"first_response_minutes": SLA_FIRST_RESPONSE_MINUTES,
			"adherence_percent": round(sla_adherence_pct, 2),
			"sample_size": len(sla_results),
		},
		"ratings": {
			"num_rated": num_rated,
			"positive": num_positive,
			"negative": num_negative,
		},
		"agents": agents,
		"agent_assignment": agent_assignment_counts,
	}


