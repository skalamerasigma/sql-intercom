from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

import orjson
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from intercom_dashboard.config import (
	REFRESH_INTERVAL_SECONDS,
	TEAM_ID,
	DEMO_MODE,
)
from intercom_dashboard.intercom_client import IntercomClient
from intercom_dashboard.metrics import compute_metrics_with_overrides, format_unassigned_conversations
from intercom_dashboard.demo_data import generate_demo_metrics, generate_demo_admins, get_demo_agent_assignments, generate_demo_conversations
from intercom_dashboard.capacity import calculate_capacity_metrics


@asynccontextmanager
async def lifespan(_: FastAPI):
	if not DEMO_MODE:
		client = IntercomClient()
		app.state.ic_client = client
	else:
		app.state.ic_client = None
	yield
	if not DEMO_MODE and app.state.ic_client:
		await app.state.ic_client.aclose()


app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def _orjson_dumps(v: Any, *, default: Any) -> str:
	return orjson.dumps(v, default=default).decode()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
	return templates.TemplateResponse(
		"index.html",
		{
			"request": request,
			"team_id": TEAM_ID,
			"refresh_interval": REFRESH_INTERVAL_SECONDS,
			"demo_mode": DEMO_MODE,
		},
	)


@app.get("/tse", response_class=HTMLResponse)
async def tse_table(request: Request) -> HTMLResponse:
	return templates.TemplateResponse(
		"tse.html",
		{
			"request": request,
			"team_id": TEAM_ID,
			"refresh_interval": REFRESH_INTERVAL_SECONDS,
			"demo_mode": DEMO_MODE,
		},
	)


@app.get("/api/agents")
async def agents() -> Dict[str, Any]:
	if DEMO_MODE:
		admins = generate_demo_admins()
		return {"admins": admins}
	
	client: IntercomClient = app.state.ic_client
	admins = await client.list_all_admins()
	return {"admins": admins}


@app.get("/api/metrics")
async def metrics(team_id: int = TEAM_ID, today_only: bool = True) -> Dict[str, Any]:
	if DEMO_MODE:
		# Generate demo data
		import time
		demo_metrics_base = generate_demo_metrics()
		demo_admins = generate_demo_admins()
		agent_assignments = get_demo_agent_assignments()
		demo_conversations = generate_demo_conversations(today_only=today_only)
		
		# Compute metrics from demo conversations
		demo_metrics = compute_metrics_with_overrides(
			conversations=demo_conversations,
			admins=demo_admins,
			team_id=team_id,
			snoozed_total_override=demo_metrics_base["totals"]["snoozed"],
			open_total_override=demo_metrics_base["totals"]["open"],
			unassigned_total_override=demo_metrics_base["totals"]["unassigned_open"],
			waiting_total_override=demo_metrics_base["totals"]["waiting_first_reply"],
			agent_assignment_open_override=agent_assignments["agent_assignment_open"],
			agent_assignment_snoozed_override=agent_assignments["agent_assignment_snoozed"],
			agent_assignment_waiting_override=agent_assignments["agent_assignment_waiting"],
			today_only=today_only,
		)
		# Override with demo-specific data
		demo_metrics["top_10_waiting"] = demo_metrics_base["top_10_waiting"]
		demo_metrics["priority_waiting"] = demo_metrics_base["priority_waiting"]
		# Generate demo unassigned conversations
		demo_unassigned = [c for c in demo_conversations if c.get("state") == "open" and not c.get("admin_assignee_id")]
		demo_metrics["unassigned_conversations"] = format_unassigned_conversations(demo_unassigned, demo_admins, now_s=int(time.time()))
		return demo_metrics
	
	client: IntercomClient = app.state.ic_client
	try:
		# Fetch open conversations as a SAMPLE plus total count; get other totals fast.
		open_sample_task = asyncio.create_task(client.get_open_conversations_sampled_and_total(team_id, max_pages=1))
		snoozed_count_task = asyncio.create_task(client.get_snoozed_count_for_team(team_id))
		unassigned_count_task = asyncio.create_task(client.count_unassigned_open_for_team(team_id))
		unassigned_convs_task = asyncio.create_task(client.get_unassigned_conversations_for_team(team_id, max_pages=10))
		waiting_count_task = asyncio.create_task(client.count_waiting_first_reply_for_team(team_id))
		waiting_convs_task = asyncio.create_task(client.get_waiting_conversations_for_team(team_id, max_pages=20))
		admins_task = asyncio.create_task(client.list_all_admins())
		(open_sample, open_total), snoozed_total, unassigned_total, unassigned_convs, waiting_total, waiting_convs, admins = await asyncio.gather(
			open_sample_task, snoozed_count_task, unassigned_count_task, unassigned_convs_task, waiting_count_task, waiting_convs_task, admins_task
		)

		# Build exact per-agent open counts (parallel)
		def _is_team_member(a: dict) -> bool:
			ids = set(a.get("team_ids") or [])
			pri = set((a.get("team_priority_level") or {}).get("primary_team_ids") or [])
			return (team_id in ids) or (team_id in pri)
		team_admins = [a for a in admins if _is_team_member(a)]
		open_tasks = [asyncio.create_task(client.count_open_for_admin(team_id, a.get("id"))) for a in team_admins]
		snoozed_tasks = [asyncio.create_task(client.count_snoozed_for_admin(team_id, a.get("id"))) for a in team_admins]
		waiting_tasks = [asyncio.create_task(client.count_waiting_for_admin(team_id, a.get("id"))) for a in team_admins]
		open_counts = await asyncio.gather(*open_tasks) if open_tasks else []
		snoozed_counts = await asyncio.gather(*snoozed_tasks) if snoozed_tasks else []
		waiting_counts = await asyncio.gather(*waiting_tasks) if waiting_tasks else []
		agent_assignment_open = {str(team_admins[i].get("id")): int(open_counts[i] or 0) for i in range(len(team_admins))}
		agent_assignment_snoozed = {str(team_admins[i].get("id")): int(snoozed_counts[i] or 0) for i in range(len(team_admins))}
		agent_assignment_waiting = {str(team_admins[i].get("id")): int(waiting_counts[i] or 0) for i in range(len(team_admins))}
		# Derive unassigned if API returned 0 (fallback)
		if not unassigned_total:
			unassigned_total = max(0, int(open_total) - sum(agent_assignment_open.values()))

		# Combine open_sample with waiting_convs and unassigned_convs for metrics computation
		# (waiting_convs and unassigned_convs are subsets of open conversations)
		all_convs_for_metrics = list({c.get("id"): c for c in open_sample + waiting_convs + unassigned_convs}.values())
		
		# Verify waiting count by actually filtering the fetched waiting conversations
		# The API count might be inaccurate, so we'll verify each conversation meets our criteria
		from intercom_dashboard.metrics import _is_waiting_for_first_reply, _is_open
		# Filter waiting_convs to only include those that actually meet our criteria
		verified_waiting_convs = [c for c in waiting_convs if _is_open(c) and _is_waiting_for_first_reply(c)]
		verified_waiting_count = len(verified_waiting_convs)
		
		# If verified count is 0 but API says there are waiting conversations,
		# the API query is likely wrong - use 0
		# If verified count differs significantly, use verified count (we fetched up to 10 pages = 500 conversations)
		if verified_waiting_count == 0:
			# Our sample shows 0 waiting conversations - trust this over API
			use_waiting_total = 0
		elif len(waiting_convs) >= 50 and abs(verified_waiting_count - waiting_total) > 2:
			# We have a good sample and it differs from API - use verified count
			use_waiting_total = verified_waiting_count
		else:
			# Use API count if it's close to verified or we don't have enough sample
			use_waiting_total = waiting_total
		
		data = compute_metrics_with_overrides(
			conversations=all_convs_for_metrics,
			admins=admins,
			team_id=team_id,
			snoozed_total_override=snoozed_total,
			open_total_override=open_total,
			unassigned_total_override=unassigned_total,
			waiting_total_override=use_waiting_total,
			agent_assignment_open_override=agent_assignment_open,
			agent_assignment_snoozed_override=agent_assignment_snoozed,
			agent_assignment_waiting_override=agent_assignment_waiting,
			today_only=today_only,
		)
		
		# Add unassigned conversations list to the response (similar to priority_waiting)
		import time
		data["unassigned_conversations"] = format_unassigned_conversations(unassigned_convs, admins, now_s=int(time.time()))
		
		return data
	except Exception as exc:
		return ORJSONResponse(
			{
				"error": "failed_to_fetch_metrics",
				"detail": str(exc),
				"team_id": team_id,
			},
			status_code=status.HTTP_502_BAD_GATEWAY,
		)


@app.get("/api/capacity")
async def capacity(team_id: int = TEAM_ID) -> Dict[str, Any]:
	"""Get capacity management metrics and recommendations."""
	if DEMO_MODE:
		# Generate demo capacity data
		demo_admins = generate_demo_admins()
		agent_assignments = get_demo_agent_assignments()
		demo_conversations = generate_demo_conversations(today_only=False)
		demo_snoozed = [c for c in demo_conversations if c.get("state") == "snoozed"]
		
		# Add snoozed_until timestamps to demo snoozed conversations
		import time
		now = int(time.time())
		for i, conv in enumerate(demo_snoozed[:10]):  # Limit to 10 for demo
			conv["snoozed_until"] = now + (i * 1800)  # Stagger returns over 5 hours
		
		return calculate_capacity_metrics(
			admins=demo_admins,
			team_id=team_id,
			agent_open_counts=agent_assignments["agent_assignment_open"],
			agent_snoozed_counts=agent_assignments["agent_assignment_snoozed"],
			snoozed_conversations=demo_snoozed,
			unassigned_open_count=agent_assignments.get("unassigned", 5),
			waiting_first_reply_count=agent_assignments.get("waiting", 8),
		)
	
	client: IntercomClient = app.state.ic_client
	try:
		# Fetch required data in parallel
		admins_task = asyncio.create_task(client.list_all_admins())
		snoozed_convs_task = asyncio.create_task(client.get_snoozed_conversations_for_team(team_id))
		unassigned_task = asyncio.create_task(client.count_unassigned_open_for_team(team_id))
		waiting_task = asyncio.create_task(client.count_waiting_first_reply_for_team(team_id))
		open_total_task = asyncio.create_task(client.get_open_conversations_sampled_and_total(team_id, max_pages=1))
		
		admins, snoozed_convs, unassigned_total, waiting_total, (open_sample, open_total) = await asyncio.gather(
			admins_task, snoozed_convs_task, unassigned_task, waiting_task, open_total_task
		)
		
		# Build per-agent counts
		def _is_team_member(a: dict) -> bool:
			ids = set(a.get("team_ids") or [])
			pri = set((a.get("team_priority_level") or {}).get("primary_team_ids") or [])
			return (team_id in ids) or (team_id in pri)
		
		team_admins = [a for a in admins if _is_team_member(a)]
		open_tasks = [asyncio.create_task(client.count_open_for_admin(team_id, a.get("id"))) for a in team_admins]
		snoozed_tasks = [asyncio.create_task(client.count_snoozed_for_admin(team_id, a.get("id"))) for a in team_admins]
		
		open_counts = await asyncio.gather(*open_tasks) if open_tasks else []
		snoozed_counts = await asyncio.gather(*snoozed_tasks) if snoozed_tasks else []
		
		agent_open_counts = {str(team_admins[i].get("id")): int(open_counts[i] or 0) for i in range(len(team_admins))}
		agent_snoozed_counts = {str(team_admins[i].get("id")): int(snoozed_counts[i] or 0) for i in range(len(team_admins))}
		
		# Always use fallback calculation (same as /api/metrics endpoint)
		# The API's unassigned count query may not be reliable, so derive it from totals
		assigned_total = sum(agent_open_counts.values())
		# Use the larger of: API unassigned count OR calculated unassigned (total_open - assigned)
		calculated_unassigned = max(0, int(open_total) - assigned_total)
		unassigned_total = max(unassigned_total or 0, calculated_unassigned)
		
		# Calculate capacity metrics
		return calculate_capacity_metrics(
			admins=admins,
			team_id=team_id,
			agent_open_counts=agent_open_counts,
			agent_snoozed_counts=agent_snoozed_counts,
			snoozed_conversations=snoozed_convs,
			unassigned_open_count=unassigned_total,
			waiting_first_reply_count=waiting_total,
		)
	except Exception as exc:
		return ORJSONResponse(
			{
				"error": "failed_to_fetch_capacity",
				"detail": str(exc),
				"team_id": team_id,
			},
			status_code=status.HTTP_502_BAD_GATEWAY,
		)


