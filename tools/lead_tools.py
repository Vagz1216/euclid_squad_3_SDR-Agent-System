"""Tool wrappers for lead-related operations.

Each function returns a strict JSON structure:
{
  "success": bool,
  "data": ...,
  "error": null|string
}
"""
from typing import Dict, Any, Optional
from services import lead_service


def get_leads_tool(email_cap: int = 5) -> Dict[str, Any]:
    if not isinstance(email_cap, int) or email_cap <= 0:
        return {"success": False, "data": None, "error": "email_cap must be a positive integer"}
    return lead_service.get_leads(email_cap=email_cap)


def update_lead_touch_tool(lead_id: int, campaign_id: int) -> Dict[str, Any]:
    if not isinstance(lead_id, int) or not isinstance(campaign_id, int):
        return {"success": False, "data": None, "error": "lead_id and campaign_id must be integers"}
    return lead_service.update_lead_touch(lead_id=lead_id, campaign_id=campaign_id)


def get_thread_tool(lead_id: int) -> Dict[str, Any]:
    if not isinstance(lead_id, int):
        return {"success": False, "data": None, "error": "lead_id must be an integer"}
    return lead_service.get_thread(lead_id=lead_id)


def update_lead_status_tool(lead_id: int, status: str) -> Dict[str, Any]:
    if not isinstance(lead_id, int) or not isinstance(status, str):
        return {"success": False, "data": None, "error": "lead_id must be int and status must be string"}
    return lead_service.update_lead_status(lead_id=lead_id, status=status)


def log_event_tool(type: str, payload: Optional[str] = None, metadata: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(type, str) or not type:
        return {"success": False, "data": None, "error": "type is required and must be a string"}
    return lead_service.log_event(event_type=type, payload=payload, metadata=metadata)
