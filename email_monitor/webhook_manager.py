"""Webhook management for AgentMail."""

import sys
from pathlib import Path
import logging
from typing import List, Dict, Any
from agentmail import AgentMail

# Add project root to path for config import
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from config import settings


logger = logging.getLogger(__name__)


class WebhookManager:
    """Manages AgentMail webhooks."""
    
    def __init__(self):
        self.client = AgentMail(api_key=settings.agentmail_api_key)
    
    def setup_webhook(self, webhook_url: str) -> str:
        """Set up webhook for message.received events.
        
        Args:
            webhook_url: The webhook endpoint URL
            
        Returns:
            Webhook ID
        """
        try:
            # Clean up existing webhooks for this URL
            self._cleanup_existing_webhooks(webhook_url)
            
            # Create new webhook
            webhook = self.client.webhooks.create(
                url=webhook_url,
                event_types=["message.received"],
                inbox_ids=[settings.agentmail_inbox_id]
            )
            
            logger.info(f"Created webhook {webhook.webhook_id} for {webhook_url}")
            return webhook.webhook_id
            
        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            raise
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all existing webhooks."""
        try:
            response = self.client.webhooks.list()
            return [{
                "id": wh.webhook_id,
                "url": wh.url,
                "enabled": wh.enabled,
                "events": wh.event_types,
                "created": wh.created_at
            } for wh in response.webhooks]
            
        except Exception as e:
            logger.error(f"Failed to list webhooks: {e}")
            raise
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        try:
            self.client.webhooks.delete(webhook_id)
            logger.info(f"Deleted webhook {webhook_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete webhook {webhook_id}: {e}")
            return False
    
    def _cleanup_existing_webhooks(self, webhook_url: str) -> None:
        """Remove any existing webhooks for this URL."""
        webhooks = self.list_webhooks()
        for webhook in webhooks:
            if webhook["url"] == webhook_url:
                logger.info(f"Removing existing webhook for {webhook_url}")
                self.delete_webhook(webhook["id"])