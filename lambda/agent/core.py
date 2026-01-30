"""
Main Jarvis Agent - The brain of the assistant
"""
import json
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI

from agent.config import settings
from agent.prompts import SYSTEM_PROMPT_BASE, SYSTEM_PROMPT_WITH_CONTEXT, build_user_context
from memory.models import UserProfile, UserRole
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.extractor import MemoryExtractor
from storage.supabase_client import SupabaseStorage
from tools import get_tool_definitions, get_tool_registry

logger = logging.getLogger(__name__)


class JarvisAgent:
    """Main agent with memory and tools"""
    
    def __init__(self):
        # Validate settings
        settings.validate()
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        
        # Initialize storage and memory
        self.storage = SupabaseStorage()
        self.short_term = ShortTermMemory(self.storage)
        self.long_term = LongTermMemory(self.storage)
        self.extractor = MemoryExtractor(self.long_term)
        
        # Current session state
        self.current_user: Optional[UserProfile] = None
        self.tool_registry: Dict[str, Any] = {}
        self.tool_definitions: List[Dict] = []
        
        logger.info("JarvisAgent initialized")
    
    def start_session(
        self,
        user_id: Optional[str] = None,
        alexa_session_id: Optional[str] = None
    ) -> UserProfile:
        """Start a new session for a user"""
        
        # Use default user if not specified
        user_id = user_id or settings.default_user_id
        
        # Load or create user profile
        user = self.long_term.get_user(user_id)
        if not user:
            logger.info(f"Creating new user: {user_id}")
            user = self.long_term.create_user(UserProfile(
                id=user_id,
                name="Friend",  # Will learn real name from conversation
                role=UserRole.ADULT,
                can_approve_orders=True
            ))
        
        self.current_user = user
        
        # Start conversation tracking
        self.short_term.start_conversation(user_id, alexa_session_id)
        
        # Initialize tools for this user
        self.tool_registry = get_tool_registry(user_id, self.storage)
        self.tool_definitions = get_tool_definitions(user_id, self.storage)
        
        logger.info(f"Session started for user: {user.name}")
        return user
    
    def process(self, user_input: str) -> str:
        """Process user input and return response"""
        
        # Ensure session is started
        if not self.current_user:
            self.start_session()
        
        # Add user message to short-term memory
        self.short_term.add_message("user", user_input)
        
        # Build personalized system prompt
        system_prompt = self._build_system_prompt(user_input)
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *self.short_term.get_messages_for_llm()
        ]
        
        try:
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tool_definitions if self.tool_definitions else None,
                tool_choice="auto" if self.tool_definitions else None,
                max_tokens=500,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message
            
            # Handle tool calls if any
            if assistant_message.tool_calls:
                reply = self._handle_tool_calls(assistant_message, messages)
            else:
                reply = assistant_message.content or "I'm not sure how to respond to that."
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            reply = "Sorry, I had trouble thinking about that. Could you try again?"
        
        # Truncate for voice if too long
        if len(reply) > settings.max_response_length:
            reply = self._truncate_for_voice(reply)
        
        # Add response to short-term memory
        self.short_term.add_message("assistant", reply)
        
        return reply
    
    def _build_system_prompt(self, user_input: str) -> str:
        """Build personalized system prompt with user context"""
        
        if not self.current_user:
            return SYSTEM_PROMPT_BASE
        
        try:
            # Get relevant facts for this query
            facts = self.long_term.get_relevant_facts(
                self.current_user.id,
                context=user_input,
                limit=10
            )
            
            # Get user preferences
            preferences = self.long_term.get_preferences(self.current_user.id)
            
            # Get recent conversation summaries
            summaries = self.long_term.get_conversation_summaries(
                self.current_user.id,
                limit=3
            )
            
            # Build context
            user_context = build_user_context(
                self.current_user,
                facts,
                preferences,
                summaries
            )
            
            return SYSTEM_PROMPT_WITH_CONTEXT.format(
                base_prompt=SYSTEM_PROMPT_BASE,
                user_context=user_context
            )
            
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return SYSTEM_PROMPT_BASE
    
    def _handle_tool_calls(self, assistant_message, messages: list) -> str:
        """Execute tools and get final response"""
        
        # Add assistant message with tool calls to messages
        tool_calls_data = []
        for tc in assistant_message.tool_calls:
            tool_calls_data.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            })
        
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": tool_calls_data
        })
        
        # Execute each tool
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
            # Get tool and execute
            tool = self.tool_registry.get(tool_name)
            if tool:
                try:
                    result = tool.execute(**tool_args)
                    result_content = json.dumps({
                        "success": result.success,
                        "data": result.data,
                        "message": result.message,
                        "error": result.error
                    })
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    result_content = json.dumps({
                        "success": False,
                        "error": str(e)
                    })
            else:
                result_content = json.dumps({
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                })
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_content
            })
            
            # Also track in short-term memory
            self.short_term.add_message(
                "tool",
                result_content,
                tool_name=tool_name,
                tool_call_id=tool_call.id
            )
        
        # Get final response after tool execution
        try:
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500
            )
            return final_response.choices[0].message.content or "Done."
        except Exception as e:
            logger.error(f"Error getting final response: {e}")
            return "I completed the task, but had trouble summarizing it."
    
    def _truncate_for_voice(self, text: str) -> str:
        """Truncate long responses for voice output"""
        
        if len(text) <= settings.max_response_length:
            return text
        
        # Find a good breaking point (end of sentence)
        truncated = text[:settings.max_response_length]
        
        # Look for sentence endings
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclaim = truncated.rfind('!')
        
        break_point = max(last_period, last_question, last_exclaim)
        
        if break_point > settings.max_response_length // 2:
            return text[:break_point + 1]
        
        return truncated + "..."
    
    def end_session(self, extract_learnings: bool = True):
        """End session and optionally extract learnings"""
        
        if not self.short_term.current_conversation:
            return
        
        conversation = self.short_term.current_conversation
        summary = None
        
        # Extract learnings from conversation
        if extract_learnings and len(conversation.messages) >= 4:
            try:
                logger.info("Extracting learnings from conversation...")
                extracted = self.extractor.extract_and_save(conversation)
                summary = extracted.get("summary")
                
                if not summary:
                    summary = self.extractor.generate_summary(conversation)
                    
                logger.info(f"Extracted {len(extracted.get('facts', []))} facts")
            except Exception as e:
                logger.error(f"Extraction failed: {e}")
        
        # End and save conversation
        self.short_term.end_conversation(summary=summary)
        
        # Update user stats
        if self.current_user:
            self.long_term.increment_conversation_count(self.current_user.id)
        
        # Clear session state
        self.current_user = None
        self.tool_registry = {}
        self.tool_definitions = []
        
        logger.info("Session ended")
    
    def get_greeting(self) -> str:
        """Get personalized greeting"""
        
        if not self.current_user:
            return "Hi! I'm Jarvis, your home assistant. How can I help you today?"
        
        name = self.current_user.name
        
        # Check if we've talked before
        try:
            summaries = self.long_term.get_conversation_summaries(
                self.current_user.id,
                limit=1
            )
            
            if summaries:
                return f"Hi {name}! Good to talk to you again. How can I help?"
        except:
            pass
        
        return f"Hi {name}! How can I help you today?"
