"""Email monitoring system orchestrator."""

import logging
from typing import Dict, Any
from agentmail import AgentMail

from config.logging import setup_logging
from config import settings
from schema import EmailActionResult
from agents import Trace, gen_trace_id
from .intent_extractor import IntentExtractorAgent
from .email_response import EmailResponseAgent
from .response_evaluator import ResponseEvaluator
from .email_sender import EmailSenderAgent

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class EmailMonitorSystem:
    """Complete email monitoring system with intent analysis."""
    
    def __init__(self):
        self.intent_extractor = IntentExtractorAgent()
        self.response_agent = EmailResponseAgent()
        self.response_evaluator = ResponseEvaluator()
        self.email_sender = EmailSenderAgent()
        self._agentmail_client = None
    
    @property
    def agentmail_client(self):
        """Lazy-loaded AgentMail client."""
        if self._agentmail_client is None:
            self._agentmail_client = AgentMail(api_key=settings.agentmail_api_key)
        return self._agentmail_client
    
    async def fetch_conversation_history(self, thread_id: str, limit: int = 10) -> str:
        """Fetch previous messages from email thread for context.
        
        Args:
            thread_id: Email thread identifier
            limit: Maximum number of previous messages to fetch
            
        Returns:
            Formatted conversation history string
        """
        if not thread_id:
            return "No thread ID available."
            
        try:
            # Get thread messages from AgentMail
            response = self.agentmail_client.inboxes.threads.list_messages(
                inbox_id=settings.agentmail_inbox_id,
                thread_id=thread_id,
                limit=limit,
                order="asc"  # Oldest first for chronological order
            )
            
            if not response.messages:
                return "No previous messages in thread."
            
            # Format conversation history
            history_parts = []
            for msg in response.messages:
                sender = msg.from_[0] if msg.from_ else "Unknown"
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M") if msg.created_at else "Unknown time"
                content = msg.text or msg.preview or "[No content]"
                
                # Truncate very long messages
                if len(content) > 500:
                    content = content[:500] + "... [truncated]"
                
                history_parts.append(
                    f"[{timestamp}] {sender}:\n{content}\n"
                )
            
            return "\n---\n".join(history_parts)
            
        except Exception as e:
            logger.warning(f"Failed to fetch conversation history for thread {thread_id}: {e}")
            return f"Unable to fetch conversation history: {str(e)}"
    
    async def process_incoming_email(self, email_data: Dict[str, Any]) -> EmailActionResult:
        """Complete email processing pipeline with retry logic and meeting scheduling."""
        # Create a single trace for the entire email processing pipeline
        trace_id = gen_trace_id()
        sender_email = email_data.get('from_', [''])[0]
        subject = email_data.get('subject', '')
        
        with Trace(
            name="email_reply_processing_pipeline",
            trace_id=trace_id,
            inputs={"sender": sender_email, "subject": subject}
        ):
            try:
                content = email_data.get('text', '') or email_data.get('preview', '')
                thread_id = email_data.get('thread_id')
                
                logger.info(f"Processing email from {sender_email}: {subject}")
                
                # Step 1: Extract intent
                intent = await self.intent_extractor.extract_intent(content, subject)
                logger.info(f"Intent: {intent.intent} (confidence: {intent.confidence})")
                
                # Step 2: Get conversation context
                conversation_history = await self.fetch_conversation_history(thread_id) if thread_id else ""
                
                # Step 3: Generate response with retry logic
                max_retries = 2
                retry_count = 0
                
                while retry_count <= max_retries:
                    # Generate response
                    response_result = await self.response_agent.generate_response(
                        email_data, intent, conversation_history
                    )
                    
                    # Handle skipped responses
                    if response_result["action"] == "skipped":
                        return EmailActionResult(
                            action_taken="skipped",
                            success=True,
                            error=response_result.get("reason")
                        )
                    
                    if response_result["action"] != "generated":
                        return EmailActionResult(
                            action_taken="error",
                            success=False,
                            error=response_result.get("reason", "Failed to generate response")
                        )
                    
                    # Step 4: Evaluate response
                    response_text = response_result["response_text"]
                    evaluation_context = {**email_data, "intent": intent.intent}
                    
                    evaluation = await self.response_evaluator.evaluate_response(
                        response_text, evaluation_context
                    )
                    
                    # If approved, proceed to sending
                    if evaluation.approved:
                        logger.info(f"Response approved on attempt {retry_count + 1}")
                        break
                    
                    # If not approved and we have retries left
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"Response rejected (attempt {retry_count}): {evaluation.reason}. Retrying...")
                        # Add feedback to context for next attempt
                        conversation_history += f"\n\nPrevious response was rejected: {evaluation.reason}. Please improve the response."
                    else:
                        logger.error(f"Response rejected after {max_retries + 1} attempts: {evaluation.reason}")
                        return EmailActionResult(
                            action_taken="rejected",
                            success=False,
                            error=f"Evaluator rejected after {max_retries + 1} attempts: {evaluation.reason}"
                        )
                
                # Step 4: Send email with context for potential meeting creation
                email_context = {
                    **email_data,
                    "intent": intent.model_dump(),
                    "conversation_history": conversation_history
                }
                
                result = await self.email_sender.execute_action(response_text, email_context)
                
                logger.info(f"Email processing completed: {result.action_taken}")
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