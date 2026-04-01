from pathlib import Path
import sys
import logging
import re
from typing import Any, Dict, Optional

# Insert project root to sys.path so imports like `tools.*` work reliably.
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool

# Import tool modules (should be resolvable once project root is on sys.path)
from tools import lead_tools, email_tools, meeting_tools  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="Tools API")


class ParamsModel(BaseModel):
	params: Dict[str, Any] = Field(default_factory=dict)


def _sanitize_error(exc: Exception) -> str:
	"""
	Produce a short, sanitized error string suitable for returning to clients.
	Strips common SQL keywords and any suspicious characters to avoid leaking raw queries.
	"""
	exc_type = exc.__class__.__name__
	raw = str(exc) or ""
	# Remove common SQL keywords and semicolons (case-insensitive)
	sanitized = re.sub(r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|DROP|ALTER|TRUNCATE)\b", "[REDACTED]", raw)
	sanitized = sanitized.replace(";", "")
	# Collapse whitespace and truncate
	sanitized = re.sub(r"\s+", " ", sanitized).strip()
	if len(sanitized) > 200:
		sanitized = sanitized[:197] + "..."
	if sanitized:
		return f"{exc_type}: {sanitized}"
	return f"{exc_type}: An internal error occurred"


async def _call_tool(module, func_name: str, params: Dict[str, Any]) -> Any:
	"""
	Calls a function named `func_name` in `module` with a single dict argument `params`.
	Falls back gracefully if the function isn't found or raises an exception.
	Uses threadpool to avoid blocking the event loop if the tool is synchronous.
	"""
	if not hasattr(module, func_name):
		raise AttributeError(f"Tool function '{func_name}' not found in module '{module.__name__}'")
	func = getattr(module, func_name)
	# Prefer calling with a dict positional param; many tools accept a dict.
	return await run_in_threadpool(func, params)


def _response(success: bool, data: Any = None, error: Optional[str] = None) -> Dict[str, Any]:
	return {"success": success, "data": data if success else None, "error": error if not success else None}


# POST endpoints for tools
@app.post("/tools/get_leads")
async def get_leads(body: ParamsModel):
	try:
		result = await _call_tool(lead_tools, "get_leads_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/get_leads")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/save_email")
async def save_email(body: ParamsModel):
	try:
		result = await _call_tool(email_tools, "save_email_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/save_email")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/update_lead_touch")
async def update_lead_touch(body: ParamsModel):
	try:
		result = await _call_tool(lead_tools, "update_lead_touch_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/update_lead_touch")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/fetch_inbound_messages")
async def fetch_inbound_messages(body: ParamsModel):
	try:
		result = await _call_tool(email_tools, "fetch_inbound_messages_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/fetch_inbound_messages")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/get_thread")
async def get_thread(body: ParamsModel):
	try:
		result = await _call_tool(lead_tools, "get_thread_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/get_thread")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/mark_processed")
async def mark_processed(body: ParamsModel):
	try:
		result = await _call_tool(email_tools, "mark_processed_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/mark_processed")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/update_lead_status")
async def update_lead_status(body: ParamsModel):
	try:
		result = await _call_tool(lead_tools, "update_lead_status_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/update_lead_status")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/schedule_meeting")
async def schedule_meeting(body: ParamsModel):
	try:
		result = await _call_tool(meeting_tools, "schedule_meeting_tool", body.params)
		return _response(True, result, None)
	except Exception as e:
		logger.exception("Error in /tools/schedule_meeting")
		return _response(False, None, _sanitize_error(e))


@app.post("/tools/log_event")
async def log_event(body: ParamsModel):
	try:
		# log_event might live in lead_tools or a shared place; try lead_tools first, fallback to email_tools then meeting_tools
		last_exc = None
		for mod, fname in ((lead_tools, 'log_event_tool'), (email_tools, 'log_event_tool'), (meeting_tools, 'log_event_tool')):
			try:
				result = await _call_tool(mod, fname, body.params)
				return _response(True, result, None)
			except AttributeError as ae:
				last_exc = ae
				continue
		# If not found in any module, raise the last attribute error
		if last_exc:
			raise last_exc
	except Exception as e:
		logger.exception("Error in /tools/log_event")
		return _response(False, None, _sanitize_error(e))


# OpenAI-compatible function specs for each tool
@app.get("/openai/functions")
def openai_functions():
	"""
	Returns an array of function specifications describing the available tool endpoints.
	Each spec includes a name, description and a JSON schema for the parameters shape.
	The schema is intentionally generic: each function accepts a single `params` object.
	"""
	base_param_schema = {
		"type": "object",
		"properties": {
			"params": {
				"type": "object",
				"description": "Parameters for the tool (tool-specific keys)"
			}
		},
		"required": ["params"]
	}

	specs = [
		{
			"name": "get_leads",
			"description": "Retrieve leads matching given filters and pagination.",
			"parameters": base_param_schema
		},
		{
			"name": "save_email",
			"description": "Save an inbound or outbound email to the system.",
			"parameters": base_param_schema
		},
		{
			"name": "update_lead_touch",
			"description": "Record a touch/interactions for a lead.",
			"parameters": base_param_schema
		},
		{
			"name": "fetch_inbound_messages",
			"description": "Fetch inbound messages from external providers.",
			"parameters": base_param_schema
		},
		{
			"name": "get_thread",
			"description": "Retrieve a message thread by thread identifier.",
			"parameters": base_param_schema
		},
		{
			"name": "mark_processed",
			"description": "Mark a message or item as processed so it is not handled again.",
			"parameters": base_param_schema
		},
		{
			"name": "update_lead_status",
			"description": "Update the lifecycle status of a lead (e.g. open, won, lost).",
			"parameters": base_param_schema
		},
		{
			"name": "schedule_meeting",
			"description": "Schedule a meeting and persist invite/metadata.",
			"parameters": base_param_schema
		},
		{
			"name": "log_event",
			"description": "Log a generic event for audit or analytics purposes.",
			"parameters": base_param_schema
		},
	]
	return {"success": True, "data": specs, "error": None}


@app.get("/health")
def health():
	return {"status": "ok"}


if __name__ == "__main__":
	# Minimal runner for local testing
	import uvicorn

	uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
