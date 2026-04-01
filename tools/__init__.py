"""Tools for agent operations and shared send helpers."""

from schema import SendEmailResult

from .email_reply import send_reply_email
from .send_email import send_agent_email, send_plain_email

__all__ = ["send_agent_email", "send_plain_email", "send_reply_email", "SendEmailResult"]
