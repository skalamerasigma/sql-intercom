from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .config import (
	INTERCOM_API_BASE,
	INTERCOM_BEARER_TOKEN,
	REQUEST_TIMEOUT_SECONDS,
	PER_PAGE,
)


class IntercomClient:
	def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
		if not INTERCOM_BEARER_TOKEN:
			raise RuntimeError(
				"Missing INTERCOM_BEARER_TOKEN. Set it in environment or .env."
			)
		timeout = httpx.Timeout(
			REQUEST_TIMEOUT_SECONDS, connect=min(REQUEST_TIMEOUT_SECONDS, 10.0)
		)
		self._client = client or httpx.AsyncClient(
			base_url=INTERCOM_API_BASE,
			headers={
				"Authorization": f"Bearer {INTERCOM_BEARER_TOKEN}",
				"Accept": "application/json",
				"Content-Type": "application/json",
				# Many search endpoints require the Unstable version header
				"Intercom-Version": "Unstable",
			},
			timeout=timeout,
		)

	async def aclose(self) -> None:
		await self._client.aclose()

	# ---------------------------
	# Admins
	# ---------------------------
	async def list_all_admins(self) -> List[Dict[str, Any]]:
		"""
		GET /admins with pagination support (best-effort; if not present, returns single page).
		"""
		admins: List[Dict[str, Any]] = []
		starting_after: Optional[str] = None
		while True:
			params = {}
			# Some Intercom endpoints accept pagination via "starting_after"
			# and/or "per_page". If unsupported, server will ignore.
			if starting_after:
				params["starting_after"] = starting_after
			params["per_page"] = PER_PAGE

			resp = await self._client.get("/admins", params=params)
			resp.raise_for_status()
			data = resp.json()

			# Response may be {type:"list", data:[...], pages:{...}}
			items = data.get("data") or data.get("admins") or data
			if isinstance(items, list):
				admins.extend(items)
			elif isinstance(items, dict) and items.get("type") == "list":
				admins.extend(items.get("data", []))
			elif isinstance(items, dict) and items.get("type") == "admin.list":
				admins.extend(items.get("admins", []))
			else:
				# Fallback for sample-like response
				if isinstance(data, list):
					admins.extend(data)
				else:
					break

			pages = data.get("pages", {})
			next_obj = pages.get("next") if isinstance(pages, dict) else None
			if next_obj and next_obj.get("starting_after"):
				starting_after = next_obj["starting_after"]
				continue
			break
		return admins

	# ---------------------------
	# Conversations search
	# ---------------------------
	async def search_conversations_one_page(
		self,
		query_clauses: List[Dict[str, Any]],
		per_page: int = 1,
	) -> Dict[str, Any]:
		"""
		POST /conversations/search returning only the first page.
		Use this to read total_count quickly without paginating.
		"""
		body: Dict[str, Any] = {
			"query": {"operator": "AND", "value": query_clauses},
			"pagination": {"per_page": per_page},
		}
		resp = await self._client.post("/conversations/search", json=body)
		resp.raise_for_status()
		return resp.json()

	async def search_conversations_paginated(
		self,
		query_clauses: List[Dict[str, Any]],
		per_page: int = PER_PAGE,
	) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
		"""
		POST /conversations/search with pagination collecting all pages.
		Returns (conversations, last_pages_object)
		"""
		all_conversations: List[Dict[str, Any]] = []
		starting_after: Optional[str] = None
		last_pages: Dict[str, Any] = {}

		while True:
			body: Dict[str, Any] = {
				"query": {
					"operator": "AND",
					"value": query_clauses,
				},
				"pagination": {"per_page": per_page},
			}
			if starting_after:
				body["pagination"]["starting_after"] = starting_after

			resp = await self._client.post("/conversations/search", json=body)
			resp.raise_for_status()
			data = resp.json()
			last_pages = data.get("pages", {}) or {}

			all_conversations.extend(data.get("conversations", []))

			next_obj = last_pages.get("next")
			if next_obj and next_obj.get("starting_after"):
				starting_after = next_obj["starting_after"]
				continue
			break

		return all_conversations, last_pages
	
	async def search_conversations_sampled(
		self,
		query_clauses: List[Dict[str, Any]],
		per_page: int = PER_PAGE,
		max_pages: int = 3,
	) -> Tuple[List[Dict[str, Any]], int]:
		"""
		Collect up to max_pages pages and return (sampled_conversations, total_count_from_first_page).
		"""
		collected: List[Dict[str, Any]] = []
		starting_after: Optional[str] = None
		total_count: int = 0
		page_no = 0
		per_page_local = min(per_page, 75)
		while page_no < max_pages:
			body: Dict[str, Any] = {
				"query": {"operator": "AND", "value": query_clauses},
				"pagination": {"per_page": per_page_local},
			}
			if starting_after:
				body["pagination"]["starting_after"] = starting_after
			resp = await self._client.post("/conversations/search", json=body)
			resp.raise_for_status()
			data = resp.json()
			if not total_count:
				total_count = int(data.get("total_count") or 0)
			collected.extend(data.get("conversations", []))
			pages = data.get("pages") or {}
			next_obj = pages.get("next") if isinstance(pages, dict) else None
			if not (next_obj and next_obj.get("starting_after")):
				break
			starting_after = next_obj["starting_after"]
			page_no += 1
		return collected, total_count

	# Helper searches
	async def get_open_conversations_for_team(self, team_id: int) -> List[Dict[str, Any]]:
		convs, _ = await self.search_conversations_paginated(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "open", "operator": "=", "value": True},
			]
		)
		return convs
	
	async def get_snoozed_conversations_for_team(self, team_id: int) -> List[Dict[str, Any]]:
		# Query only snoozed, not all non-open, to avoid fetching huge closed history
		convs, _ = await self.search_conversations_paginated(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "state", "operator": "=", "value": "snoozed"},
			]
		)
		return convs
	
	async def get_snoozed_count_for_team(self, team_id: int) -> int:
		data = await self.search_conversations_one_page(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "state", "operator": "=", "value": "snoozed"},
			],
			per_page=1,
		)
		return int(data.get("total_count") or 0)
	
	async def count_unassigned_open_for_team(self, team_id: int) -> int:
		data = await self.search_conversations_one_page(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "open", "operator": "=", "value": True},
				{"field": "admin_assignee_id", "operator": "=", "value": None},
			],
			per_page=1,
		)
		return int(data.get("total_count") or 0)
	
	async def count_waiting_first_reply_for_team(self, team_id: int) -> int:
		# Waiting = open and first_admin_reply_at is null
		data = await self.search_conversations_one_page(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "open", "operator": "=", "value": True},
				{"field": "statistics.first_admin_reply_at", "operator": "=", "value": None},
			],
			per_page=1,
		)
		return int(data.get("total_count") or 0)

	async def count_open_for_admin(self, team_id: int, admin_id: str | int) -> int:
		data = await self.search_conversations_one_page(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "admin_assignee_id", "operator": "=", "value": str(admin_id)},
				{"field": "open", "operator": "=", "value": True},
			],
			per_page=1,
		)
		return int(data.get("total_count") or 0)

	async def count_snoozed_for_admin(self, team_id: int, admin_id: str | int) -> int:
		data = await self.search_conversations_one_page(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "admin_assignee_id", "operator": "=", "value": str(admin_id)},
				{"field": "state", "operator": "=", "value": "snoozed"},
			],
			per_page=1,
		)
		return int(data.get("total_count") or 0)

	async def count_waiting_for_admin(self, team_id: int, admin_id: str | int) -> int:
		# Open, assigned to admin, and first_admin_reply_at is null
		data = await self.search_conversations_one_page(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "admin_assignee_id", "operator": "=", "value": str(admin_id)},
				{"field": "open", "operator": "=", "value": True},
				{"field": "statistics.first_admin_reply_at", "operator": "=", "value": None},
			],
			per_page=1,
		)
		return int(data.get("total_count") or 0)

	async def get_all_team_conversations(self, team_id: int) -> List[Dict[str, Any]]:
		open_task = asyncio.create_task(self.get_open_conversations_for_team(team_id))
		snoozed_task = asyncio.create_task(self.get_snoozed_conversations_for_team(team_id))
		open_list, snoozed_list = await asyncio.gather(open_task, snoozed_task)
		return [*open_list, *snoozed_list]

	async def get_open_conversations_sampled_and_total(
		self, team_id: int, max_pages: int = 3
	) -> Tuple[List[Dict[str, Any]], int]:
		return await self.search_conversations_sampled(
			[
				{"field": "team_assignee_id", "operator": "=", "value": str(team_id)},
				{"field": "open", "operator": "=", "value": True},
			],
			per_page=50,
			max_pages=max_pages,
		)


