"""Senior Marketing Agent that orchestrates database-driven outreach campaigns with tracing."""

import logging
import json
from typing import Dict, Any

from config.logging import setup_logging
from agents import Agent, ModelSettings, Runner, set_default_openai_key, trace
from config import settings

# Import database-driven tools
from tools.campaign_tools import get_campaign_tool
from tools.lead_tools import get_lead_tool
from tools.send_email import send_agent_email
from tools.content_tools import (
    create_professional_email,
    create_engaging_email,
    create_concise_email
)


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Set OpenAI API key for agents library
if settings.openai_api_key:
    set_default_openai_key(settings.openai_api_key)


class SeniorMarketingAgent:
    """Orchestrates complete database-driven outreach campaigns with AI content generation."""
    
    def __init__(self):
        # Collect all database-driven outreach tools
        self.tools = [
            get_campaign_tool,
            get_lead_tool,
            create_professional_email,
            create_engaging_email,
            create_concise_email,
            send_agent_email
        ]
        
        self.agent = Agent(
            name="SeniorMarketingAgent",
            model=settings.outreach_model,
            instructions="""You are a Senior Marketing Agent that orchestrates outreach campaigns. Follow this EXACT workflow:

1. **Get Campaign**: Use get_campaign_tool to retrieve campaign details from database
2. **Get Lead**: Use get_lead_tool to retrieve target lead information 
3. **Generate Content**: Create 3 email variations using:
   - create_professional_email
   - create_engaging_email  
   - create_concise_email
4. **Evaluate & Select**: Compare the 3 drafts and choose the BEST one based on:
   - Relevance to campaign value proposition
   - Personalization for the lead
   - Professional quality and clarity
5. **Send ONE Email**: Use send_agent_email to send ONLY the selected best email

IMPORTANT: Send exactly ONE email per campaign. Do not send multiple emails.

For email generation, provide:
- name: The lead's company/contact name from get_lead_tool
- value_proposition: The campaign value proposition from get_campaign_tool

Complete the entire workflow and report success.""",
            model_settings=ModelSettings(
                temperature=0.4,
                max_tokens=1000
            ),
            tools=self.tools
        )
    
    async def execute_campaign(self) -> Dict[str, Any]:
        """Execute a complete database-driven outreach campaign with tracing."""
        logger.info("Starting automated database-driven outreach campaign")
        
        try:
            with trace("Outreach Campaign Execution"):
                runner = Runner()
                result = await runner.run(
                    self.agent,
                    "Execute automated outreach campaign"
                )
                
                if hasattr(result, 'value') and result.value:
                    logger.info("Database-driven outreach campaign completed successfully")
                    return {
                        "success": True,
                        "message": "Automated campaign executed with full database integration and tracing",
                        "agent_result": str(result.value) if hasattr(result, 'value') else "Campaign completed"
                    }
                else:
                    logger.info("Database-driven outreach campaign completed successfully (no result value)")
                    return {
                        "success": True,
                        "message": "Automated campaign executed with full database integration and tracing",
                        "agent_result": "Campaign completed successfully"
                    }
                    
        except Exception as e:
            logger.error(f"Campaign execution error: {e}")
            return {"success": False, "error": str(e)}

# Create global instance for API usage
senior_marketing_agent = SeniorMarketingAgent()