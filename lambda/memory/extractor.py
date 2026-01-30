"""Extract facts and preferences from conversations"""
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

from memory.models import Conversation
from memory.long_term import LongTermMemory
from agent.prompts import EXTRACTION_PROMPT, SUMMARY_PROMPT
from agent.config import settings

logger = logging.getLogger(__name__)


class MemoryExtractor:
    """Extracts learnings from conversations"""
    
    def __init__(self, long_term_memory: LongTermMemory):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.memory = long_term_memory
        self.model = settings.openai_model_cheap  # Use cheaper model for extraction
    
    def extract_and_save(self, conversation: Conversation) -> Dict[str, Any]:
        """Extract facts/preferences and save to memory"""
        
        # Format conversation
        conv_text = self._format_conversation(conversation)
        
        if not conv_text or len(conv_text) < 50:
            return {"facts": [], "preferences": [], "summary": None}
        
        try:
            # Extract using LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You extract facts and preferences from conversations. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": EXTRACTION_PROMPT.format(conversation=conv_text)
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            extracted = json.loads(response.choices[0].message.content)
            
            # Save facts
            facts_saved = 0
            for fact_data in extracted.get("facts", []):
                try:
                    self.memory.add_fact(
                        user_id=conversation.user_id,
                        fact=fact_data["fact"],
                        category=fact_data.get("category", "other"),
                        importance=fact_data.get("importance", "normal"),
                        source_conversation=conversation.id
                    )
                    facts_saved += 1
                except Exception as e:
                    logger.error(f"Error saving fact: {e}")
            
            # Save preferences
            prefs_saved = 0
            for pref_data in extracted.get("preferences", []):
                try:
                    self.memory.set_preference(
                        user_id=conversation.user_id,
                        category=pref_data.get("category", "other"),
                        key=pref_data["key"],
                        value=pref_data["value"],
                        source_conversation=conversation.id
                    )
                    prefs_saved += 1
                except Exception as e:
                    logger.error(f"Error saving preference: {e}")
            
            logger.info(f"Extracted {facts_saved} facts, {prefs_saved} preferences")
            return extracted
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"facts": [], "preferences": [], "summary": None}
    
    def generate_summary(self, conversation: Conversation) -> Optional[str]:
        """Generate a conversation summary"""
        conv_text = self._format_conversation(conversation)
        
        if not conv_text or len(conv_text) < 50:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You summarize conversations briefly. 2-3 sentences max."
                    },
                    {
                        "role": "user",
                        "content": SUMMARY_PROMPT.format(conversation=conv_text)
                    }
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return None
    
    def _format_conversation(self, conversation: Conversation) -> str:
        """Format conversation for analysis"""
        lines = []
        for msg in conversation.messages:
            if msg.role in ["user", "assistant"]:
                role_name = "User" if msg.role == "user" else "Assistant"
                lines.append(f"{role_name}: {msg.content}")
        return "\n".join(lines)
