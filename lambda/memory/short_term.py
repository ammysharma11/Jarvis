"""Short-term memory - current conversation context"""
import logging
from typing import List, Optional
from datetime import datetime

from memory.models import Message, Conversation
from agent.config import settings

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """Manages current conversation state"""
    
    def __init__(self, storage):
        self.storage = storage
        self.max_messages = settings.max_conversation_messages
        self.current_conversation: Optional[Conversation] = None
        self._message_buffer: List[Message] = []  # Unsaved messages
    
    def start_conversation(
        self,
        user_id: str,
        alexa_session_id: Optional[str] = None
    ) -> Conversation:
        """Start a new conversation"""
        self.current_conversation = self.storage.create_conversation(
            user_id=user_id,
            alexa_session_id=alexa_session_id
        )
        self._message_buffer = []
        logger.info(f"Started conversation: {self.current_conversation.id}")
        return self.current_conversation
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load an existing conversation (for continued sessions)"""
        conversation = self.storage.get_conversation(conversation_id)
        if conversation:
            self.current_conversation = conversation
            self._message_buffer = []
        return conversation
    
    def add_message(
        self,
        role: str,
        content: str,
        tool_name: Optional[str] = None,
        tool_call_id: Optional[str] = None
    ) -> Message:
        """Add a message to current conversation"""
        message = Message(
            role=role,
            content=content,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            timestamp=datetime.utcnow()
        )
        
        if self.current_conversation:
            self.current_conversation.messages.append(message)
            self._message_buffer.append(message)
            
            # Trim if exceeds max (keep recent messages)
            if len(self.current_conversation.messages) > self.max_messages:
                self.current_conversation.messages = \
                    self.current_conversation.messages[-self.max_messages:]
        
        return message
    
    def get_messages_for_llm(self) -> List[dict]:
        """Get messages formatted for OpenAI API"""
        if not self.current_conversation:
            return []
        
        formatted = []
        for msg in self.current_conversation.messages:
            if msg.role == "tool":
                formatted.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id
                })
            else:
                formatted.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return formatted
    
    def get_conversation_text(self) -> str:
        """Get conversation as plain text (for summarization)"""
        if not self.current_conversation:
            return ""
        
        lines = []
        for msg in self.current_conversation.messages:
            if msg.role in ["user", "assistant"]:
                role_name = "User" if msg.role == "user" else "Jarvis"
                lines.append(f"{role_name}: {msg.content}")
        
        return "\n".join(lines)
    
    def end_conversation(self, summary: Optional[str] = None):
        """End and persist the conversation"""
        if not self.current_conversation:
            return
        
        self.current_conversation.ended_at = datetime.utcnow()
        self.current_conversation.summary = summary
        
        # Save to database
        try:
            self.storage.save_conversation(self.current_conversation)
            logger.info(f"Saved conversation: {self.current_conversation.id}")
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
        
        # Clear state
        self.current_conversation = None
        self._message_buffer = []
    
    def save_progress(self):
        """Save conversation progress without ending it"""
        if self.current_conversation and self._message_buffer:
            try:
                self.storage.save_conversation(self.current_conversation)
                self._message_buffer = []
            except Exception as e:
                logger.error(f"Failed to save progress: {e}")
