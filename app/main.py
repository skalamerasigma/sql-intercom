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
from intercom_dashboard.metrics import compute_metrics


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
		admins_task = asyncio.create_task(client.list_all_admins())
		all_conversations_task = asyncio.create_task(client.get_all_team_conversations(team_id))
		admins, conversations = await asyncio.gather(admins_task, all_conversations_task)
		data = compute_metrics(conversations=conversations, admins=admins, team_id=team_id)
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


