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
)
from intercom_dashboard.intercom_client import IntercomClient
from intercom_dashboard.metrics import compute_metrics_with_overrides


@asynccontextmanager
async def lifespan(_: FastAPI):
	client = IntercomClient()
	app.state.ic_client = client
	yield
	await client.aclose()


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
		},
	)


@app.get("/api/agents")
async def agents() -> Dict[str, Any]:
	client: IntercomClient = app.state.ic_client
	admins = await client.list_all_admins()
	return {"admins": admins}


@app.get("/api/metrics")
async def metrics(team_id: int = TEAM_ID) -> Dict[str, Any]:
	client: IntercomClient = app.state.ic_client
	try:
		# Fetch open conversations as a SAMPLE plus total count; get snoozed count fast.
		open_sample_task = asyncio.create_task(client.get_open_conversations_sampled_and_total(team_id, max_pages=1))
		snoozed_count_task = asyncio.create_task(client.get_snoozed_count_for_team(team_id))
		unassigned_count_task = asyncio.create_task(client.count_unassigned_open_for_team(team_id))
		waiting_count_task = asyncio.create_task(client.count_waiting_first_reply_for_team(team_id))
		(open_sample, open_total), snoozed_total, unassigned_total, waiting_total = await asyncio.gather(
			open_sample_task, snoozed_count_task, unassigned_count_task, waiting_count_task
		)

		data = compute_metrics_with_overrides(
			conversations=open_sample,
			admins=[],
			team_id=team_id,
			snoozed_total_override=snoozed_total,
			open_total_override=open_total,
			unassigned_total_override=unassigned_total,
			waiting_total_override=waiting_total,
		)
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


