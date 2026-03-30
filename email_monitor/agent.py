"""Email monitoring agents using OpenAI Agents SDK."""

import sys
from pathlib import Path
from typing import Dict, Any
import logging
from pydantic import BaseModel
from agentmail import AgentMail

# Add project root to path for config import
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from config import settings
from agents import Agent, ModelSettings, Runner, function_tool

logger = logging.getLogger(__name__)


class EmailIntent(BaseModel):
    """Structured intent classification result."""
    intent: str  # meeting_request | question | opt_out | interest | neutral | bounce | spam
    confidence: float  # 0.0 - 1.0


class EmailActionResult(BaseModel):
    """Result of email processing action."""
    action_taken: str
    success: bool
    message_id: str | None = None
    thread_id: str | None = None
    error: str | None = None


@function_tool
def send_reply_email(to_email: str, subject: str, message: str, thread_id: str = None) -> Dict[str, Any]:
    """Send email reply via AgentMail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email message content
        thread_id: Thread ID to reply to (optional)
        
    Returns:
        Dict with send result
    """
    from agentmail import AgentMail
    
    try:
        client = AgentMail(api_key=settings.agentmail_api_key)
        
        send_kwargs = {
            'to': to_email,
            'subject': subject,
            'text': message,
        }
        
        if thread_id:
            send_kwargs['thread_id'] = thread_id
        
        response = client.inboxes.messages.send(settings.agentmail_inbox_id, **send_kwargs)
        
        return {
            'success': True,
            'message_id': str(response.message_id),
            'thread_id': str(response.thread_id)
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {'success': False, 'error': str(e)}


class IntentExtractorAgent:
    """Agent that extracts intent from email content."""
    
    def __init__(self):
        self.agent = Agent(
            name="EmailIntentExtractor",
            instructions="""
Analyze email content and classify the sender's intent with confidence.

Classify into one of these intents:
- meeting_request: Explicitly asking to schedule a meeting/call
- question: Has specific questions about services
- interest: Expressing interest but no specific questions
- opt_out: Requesting to be removed or unsubscribed
- neutral: General inquiry or acknowledgment
- bounce: Automated bounce/out-of-office message
- spam: Spam or irrelevant content

Provide confidence score 0.0-1.0 based on clarity of intent.
Return only the structured response, no additional text.
""",
            model_settings=ModelSettings(
                model="gpt-4",
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=100
            )
        )
    
    async def extract_intent(self, email_content: str, subject: str = "") -> EmailIntent:
        """Extract intent from email content."""
        prompt = f"""
Subject: {subject}
Content: {email_content}

Respond with JSON only:
{{
  "intent": "meeting_request|question|opt_out|interest|neutral|bounce|spam",
  "confidence": 0.0-1.0
}}
"""
        
        result = await Runner.run(self.agent, prompt)
        
        # Parse the JSON response
        try:
            import json
            response_data = json.loads(result.final_output)
            return EmailIntent(**response_data)
        except Exception as e:
            logger.warning(f"Failed to parse intent response: {e}")
            return EmailIntent(intent="neutral", confidence=0.5)


class EmailResponseAgent:
    """Agent that crafts replies based on intent analysis."""
    
    def __init__(self):
        self.agent = Agent(
            name="EmailResponseAgent",
            instructions="""
You are a professional business development assistant responding to client inquiries.

Your PRIMARY goal is to schedule meetings/calls with potential clients.

Response guidelines by intent:
- meeting_request: Confirm availability and provide scheduling options
- question: Answer briefly, then suggest meeting for detailed discussion
- interest: Build value and urgency, push for meeting
- opt_out: Respect request, confirm removal
- neutral: Engage professionally, steer toward meeting if appropriate
- bounce/spam: No response needed

Use email conversation history as context for personalized responses.
Keep responses concise (2-3 paragraphs max).
Always use send_reply_email function to send your response.
""",
            tools=[send_reply_email],
            model_settings=ModelSettings(
                model="gpt-4",
                temperature=0.7,
                max_tokens=800
            )
        )
    
    async def generate_response(self, email_data: Dict[str, Any], intent: EmailIntent, conversation_history: str = "") -> EmailActionResult:
        """Generate and send appropriate response based on intent."""
        sender_email = email_data.get('from_', [''])[0]
        subject = email_data.get('subject', '')
        content = email_data.get('text', '') or email_data.get('preview', '')
        thread_id = email_data.get('thread_id')
        
        # Skip responses for certain intents
        if intent.intent in ['bounce', 'spam'] or intent.confidence < 0.3:
            return EmailActionResult(
                action_taken="skipped",
                success=True,
                error=f"Intent: {intent.intent} (confidence: {intent.confidence})"
            )
        
        # Build context for response
        context = f"""
Incoming email analysis:
- From: {sender_email}
- Subject: {subject}
- Intent: {intent.intent} (confidence: {intent.confidence})
- Content: {content}

Conversation history:
{conversation_history or "No previous conversation."}

Generate appropriate response and send using send_reply_email function.
"""
        
        try:
            result = await Runner.run(self.agent, context)
            
            return EmailActionResult(
                action_taken="replied",
                success=True,
                message_id=None,  # Would be populated by send_reply_email tool
                thread_id=thread_id
            )
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return EmailActionResult(
                action_taken="error",
                success=False,
                error=str(e)
            )
    
class EmailMonitorSystem:
    """Complete email monitoring system with intent analysis."""
    
    def __init__(self):
        self.intent_extractor = IntentExtractorAgent()
        self.response_agent = EmailResponseAgent()
    
    async def process_incoming_email(self, email_data: Dict[str, Any]) -> EmailActionResult:
        """Process incoming email with intent analysis and appropriate response."""
        try:
            sender_email = email_data.get('from_', [''])[0]
            subject = email_data.get('subject', '')
            content = email_data.get('text', '') or email_data.get('preview', '')
            
            logger.info(f"Processing email from {sender_email}: {subject}")
            
            # Extract intent first
            intent = await self.intent_extractor.extract_intent(content, subject)
            logger.info(f"Extracted intent: {intent.intent} (confidence: {intent.confidence})")
            
            # TODO: Fetch conversation history from email thread
            conversation_history = ""
            
            # Generate response based on intent
            result = await self.response_agent.generate_response(
                email_data, intent, conversation_history
            )
            
            logger.info(f"Action taken: {result.action_taken} (success: {result.success})")
            return result
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return EmailActionResult(
                action_taken="error",
                success=False,
                error=str(e)
            )


# Global system instance
email_monitor = EmailMonitorSystem()