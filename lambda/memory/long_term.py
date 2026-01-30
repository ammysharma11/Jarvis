"""Long-term memory - persistent user knowledge"""
import logging
from typing import List, Dict, Optional

from memory.models import UserProfile, UserFact, Conversation, Importance

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Manages persistent user memory"""
    
    def __init__(self, storage):
        self.storage = storage
    
    # ==========================================
    # USER PROFILE
    # ==========================================
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return self.storage.get_user(user_id)
    
    def create_user(self, profile: UserProfile) -> UserProfile:
        """Create new user"""
        return self.storage.create_user(profile)
    
    def update_user(self, profile: UserProfile) -> UserProfile:
        """Update user profile"""
        return self.storage.update_user(profile)
    
    def increment_conversation_count(self, user_id: str):
        """Increment user's conversation count"""
        try:
            user = self.get_user(user_id)
            if user:
                user.total_conversations += 1
                self.update_user(user)
        except Exception as e:
            logger.error(f"Failed to increment conversation count: {e}")
    
    # ==========================================
    # FACTS
    # ==========================================
    
    def add_fact(
        self,
        user_id: str,
        fact: str,
        category: str,
        importance: str = "normal",
        source_conversation: Optional[str] = None
    ) -> UserFact:
        """Add a learned fact"""
        user_fact = UserFact(
            user_id=user_id,
            fact=fact,
            category=category,
            importance=Importance(importance),
            source_conversation=source_conversation
        )
        return self.storage.add_fact(user_fact)
    
    def get_facts(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[UserFact]:
        """Get facts about a user"""
        return self.storage.get_facts(user_id, category=category, limit=limit)
    
    def get_relevant_facts(
        self,
        user_id: str,
        context: str,
        limit: int = 10
    ) -> List[UserFact]:
        """Get facts relevant to current context"""
        return self.storage.get_relevant_facts(user_id, context, limit)
    
    def mark_fact_used(self, fact_id: str):
        """Mark a fact as referenced (for relevance tracking)"""
        try:
            self.storage.update_fact_reference(fact_id)
        except Exception as e:
            logger.error(f"Failed to mark fact used: {e}")
    
    # ==========================================
    # PREFERENCES
    # ==========================================
    
    def set_preference(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        source_conversation: Optional[str] = None
    ):
        """Set or update a preference"""
        self.storage.set_preference(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            source_conversation=source_conversation
        )
    
    def get_preferences(self, user_id: str) -> Dict[str, Dict[str, str]]:
        """Get all preferences"""
        return self.storage.get_preferences(user_id)
    
    def get_preference(self, user_id: str, category: str, key: str) -> Optional[str]:
        """Get single preference"""
        return self.storage.get_preference(user_id, category, key)
    
    # ==========================================
    # CONVERSATION HISTORY
    # ==========================================
    
    def get_recent_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Conversation]:
        """Get recent conversations"""
        return self.storage.get_recent_conversations(user_id, limit)
    
    def get_conversation_summaries(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[str]:
        """Get summaries of recent conversations"""
        return self.storage.get_conversation_summaries(user_id, limit)
