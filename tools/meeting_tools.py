"""Tool wrappers for meeting operations."""
from typing import Dict, Any, Optional
from services import meeting_service


def schedule_meeting_tool(lead_id: int, staff_id: int, start_time: str, meet_link: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(lead_id, int) or not isinstance(staff_id, int):
        return {"success": False, "data": None, "error": "lead_id and staff_id must be integers"}
    if not isinstance(start_time, str) or not start_time:
        return {"success": False, "data": None, "error": "start_time must be an ISO string"}
    return meeting_service.schedule_meeting(lead_id=lead_id, staff_id=staff_id, start_time=start_time, meet_link=meet_link)
