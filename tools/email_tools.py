"""Tool wrappers for email operations."""
from typing import Dict, Any
from services import email_service


def save_email_tool(lead_id: int, campaign_id: int, subject: str, body: str) -> Dict[str, Any]:
    if not isinstance(lead_id, int) or not isinstance(campaign_id, int):
        return {"success": False, "data": None, "error": "lead_id and campaign_id must be integers"}
    if subject is None or body is None:
        return {"success": False, "data": None, "error": "subject and body are required"}
    return email_service.save_email(lead_id=lead_id, campaign_id=campaign_id, subject=subject, body=body)


def fetch_inbound_messages_tool() -> Dict[str, Any]:
    return email_service.fetch_inbound_messages()


def mark_processed_tool(message_id: int, intent: str) -> Dict[str, Any]:
    if not isinstance(message_id, int) or not isinstance(intent, str):
        return {"success": False, "data": None, "error": "message_id must be int and intent must be string"}
    return email_service.mark_processed(message_id=message_id, intent=intent)
