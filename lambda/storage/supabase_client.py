"""Supabase storage client"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from supabase import create_client, Client

from agent.config import settings
from memory.models import (
    UserProfile, UserRole, UserFact, UserPreference,
    Conversation, Message, Order, OrderItem, OrderStatus,
    Reminder, GroceryItem, MedicalInfo, Importance
)

logger = logging.getLogger(__name__)


class SupabaseStorage:
    """Storage layer using Supabase"""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("Supabase client initialized")
    
    # ==========================================
    # USER PROFILES
    # ==========================================
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID"""
        try:
            result = self.client.table("users")\
                .select("*")\
                .eq("id", user_id)\
                .maybe_single()\
                .execute()
            
            if result.data:
                return self._row_to_user(result.data)
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def create_user(self, profile: UserProfile) -> UserProfile:
        """Create a new user"""
        data = {
            "id": profile.id,
            "name": profile.name,
            "role": profile.role.value,
            "age": profile.age,
            "preferred_language": profile.preferred_language,
            "preferred_response_length": profile.preferred_response_length,
            "daily_order_limit": profile.daily_order_limit,
            "requires_approval": profile.requires_approval,
            "can_approve_orders": profile.can_approve_orders,
            "medical_info": profile.medical_info.model_dump() if profile.medical_info else None
        }
        
        result = self.client.table("users").insert(data).execute()
        return self._row_to_user(result.data[0])
    
    def update_user(self, profile: UserProfile) -> UserProfile:
        """Update user profile"""
        data = {
            "name": profile.name,
            "role": profile.role.value,
            "age": profile.age,
            "preferred_language": profile.preferred_language,
            "preferred_response_length": profile.preferred_response_length,
            "daily_order_limit": profile.daily_order_limit,
            "requires_approval": profile.requires_approval,
            "can_approve_orders": profile.can_approve_orders,
            "medical_info": profile.medical_info.model_dump() if profile.medical_info else None,
            "total_conversations": profile.total_conversations,
            "last_interaction": datetime.utcnow().isoformat()
        }
        
        result = self.client.table("users")\
            .update(data)\
            .eq("id", profile.id)\
            .execute()
        
        return self._row_to_user(result.data[0])
    
    def _row_to_user(self, row: dict) -> UserProfile:
        """Convert DB row to UserProfile"""
        return UserProfile(
            id=row["id"],
            name=row["name"],
            role=UserRole(row["role"]),
            age=row.get("age"),
            voice_id=row.get("voice_id"),
            preferred_language=row.get("preferred_language", "english"),
            preferred_response_length=row.get("preferred_response_length", "medium"),
            daily_order_limit=row.get("daily_order_limit"),
            requires_approval=row.get("requires_approval", False),
            can_approve_orders=row.get("can_approve_orders", False),
            medical_info=MedicalInfo(**row["medical_info"]) if row.get("medical_info") else None,
            total_conversations=row.get("total_conversations", 0),
            created_at=row.get("created_at"),
            last_interaction=row.get("last_interaction")
        )
    
    # ==========================================
    # FACTS
    # ==========================================
    
    def add_fact(self, fact: UserFact) -> UserFact:
        """Add a new fact"""
        data = {
            "user_id": fact.user_id,
            "fact": fact.fact,
            "category": fact.category,
            "importance": fact.importance.value,
            "source_conversation": fact.source_conversation
        }
        
        result = self.client.table("facts").insert(data).execute()
        fact.id = result.data[0]["id"]
        return fact
    
    def get_facts(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[UserFact]:
        """Get facts for a user"""
        try:
            query = self.client.table("facts")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if category:
                query = query.eq("category", category)
            
            result = query.execute()
            return [self._row_to_fact(row) for row in result.data]
        except Exception as e:
            logger.error(f"Error getting facts: {e}")
            return []
    
    def get_relevant_facts(
        self,
        user_id: str,
        context: str,
        limit: int = 10
    ) -> List[UserFact]:
        """Get facts relevant to current context (keyword-based)"""
        all_facts = self.get_facts(user_id, limit=100)
        
        if not all_facts:
            return []
        
        context_lower = context.lower()
        context_words = set(context_lower.split())
        
        scored_facts = []
        for fact in all_facts:
            score = 0
            fact_words = set(fact.fact.lower().split())
            
            # Keyword overlap
            overlap = context_words & fact_words
            score += len(overlap) * 2
            
            # Importance boost
            if fact.importance == Importance.CRITICAL:
                score += 5
            elif fact.importance == Importance.HIGH:
                score += 3
            
            # Recent reference boost
            if fact.last_referenced:
                try:
                    days_ago = (datetime.utcnow() - fact.last_referenced).days
                    if days_ago < 7:
                        score += 2
                except:
                    pass
            
            if score > 0:
                scored_facts.append((score, fact))
        
        scored_facts.sort(key=lambda x: x[0], reverse=True)
        return [fact for _, fact in scored_facts[:limit]]
    
    def update_fact_reference(self, fact_id: str):
        """Mark a fact as referenced"""
        try:
            self.client.table("facts")\
                .update({
                    "last_referenced": datetime.utcnow().isoformat(),
                    "reference_count": self.client.table("facts")
                        .select("reference_count")
                        .eq("id", fact_id)
                        .single()
                        .execute()
                        .data.get("reference_count", 0) + 1
                })\
                .eq("id", fact_id)\
                .execute()
        except Exception as e:
            logger.error(f"Error updating fact reference: {e}")
    
    def _row_to_fact(self, row: dict) -> UserFact:
        """Convert DB row to UserFact"""
        return UserFact(
            id=row["id"],
            user_id=row["user_id"],
            fact=row["fact"],
            category=row["category"],
            importance=Importance(row.get("importance", "normal")),
            source_conversation=row.get("source_conversation"),
            created_at=row.get("created_at"),
            last_referenced=row.get("last_referenced"),
            reference_count=row.get("reference_count", 0)
        )
    
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
        data = {
            "user_id": user_id,
            "category": category,
            "key": key,
            "value": value,
            "source_conversation": source_conversation,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            self.client.table("preferences")\
                .upsert(data, on_conflict="user_id,category,key")\
                .execute()
        except Exception as e:
            logger.error(f"Error setting preference: {e}")
    
    def get_preferences(self, user_id: str) -> Dict[str, Dict[str, str]]:
        """Get all preferences as nested dict"""
        try:
            result = self.client.table("preferences")\
                .select("category, key, value")\
                .eq("user_id", user_id)\
                .execute()
            
            prefs = {}
            for row in result.data:
                cat = row["category"]
                if cat not in prefs:
                    prefs[cat] = {}
                prefs[cat][row["key"]] = row["value"]
            
            return prefs
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {}
    
    def get_preference(self, user_id: str, category: str, key: str) -> Optional[str]:
        """Get a single preference value"""
        try:
            result = self.client.table("preferences")\
                .select("value")\
                .eq("user_id", user_id)\
                .eq("category", category)\
                .eq("key", key)\
                .maybe_single()\
                .execute()
            
            return result.data["value"] if result.data else None
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
            return None
    
    # ==========================================
    # CONVERSATIONS
    # ==========================================
    
    def create_conversation(self, user_id: str, alexa_session_id: Optional[str] = None) -> Conversation:
        """Start a new conversation"""
        data = {
            "user_id": user_id,
            "alexa_session_id": alexa_session_id
        }
        
        result = self.client.table("conversations").insert(data).execute()
        row = result.data[0]
        
        return Conversation(
            id=row["id"],
            user_id=user_id,
            alexa_session_id=alexa_session_id,
            started_at=row["started_at"]
        )
    
    def save_conversation(self, conversation: Conversation):
        """Save/update conversation"""
        # Update conversation record
        data = {
            "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
            "summary": conversation.summary,
            "message_count": len(conversation.messages)
        }
        
        self.client.table("conversations")\
            .update(data)\
            .eq("id", conversation.id)\
            .execute()
        
        # Save messages
        if conversation.messages:
            messages_data = [
                {
                    "conversation_id": conversation.id,
                    "role": msg.role,
                    "content": msg.content,
                    "tool_name": msg.tool_name,
                    "tool_call_id": msg.tool_call_id
                }
                for msg in conversation.messages
                if not msg.id  # Only save new messages
            ]
            
            if messages_data:
                self.client.table("messages").insert(messages_data).execute()
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation with messages"""
        try:
            conv_result = self.client.table("conversations")\
                .select("*")\
                .eq("id", conversation_id)\
                .maybe_single()\
                .execute()
            
            if not conv_result.data:
                return None
            
            row = conv_result.data
            
            # Get messages
            msg_result = self.client.table("messages")\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .order("created_at")\
                .execute()
            
            messages = [
                Message(
                    id=m["id"],
                    role=m["role"],
                    content=m["content"],
                    tool_name=m.get("tool_name"),
                    tool_call_id=m.get("tool_call_id"),
                    timestamp=m["created_at"]
                )
                for m in msg_result.data
            ]
            
            return Conversation(
                id=row["id"],
                user_id=row["user_id"],
                alexa_session_id=row.get("alexa_session_id"),
                messages=messages,
                started_at=row["started_at"],
                ended_at=row.get("ended_at"),
                summary=row.get("summary")
            )
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None
    
    def get_recent_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Conversation]:
        """Get recent conversations (without messages)"""
        try:
            result = self.client.table("conversations")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("started_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return [
                Conversation(
                    id=row["id"],
                    user_id=row["user_id"],
                    started_at=row["started_at"],
                    ended_at=row.get("ended_at"),
                    summary=row.get("summary")
                )
                for row in result.data
            ]
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            return []
    
    def get_conversation_summaries(self, user_id: str, limit: int = 5) -> List[str]:
        """Get just the summaries of recent conversations"""
        try:
            result = self.client.table("conversations")\
                .select("summary")\
                .eq("user_id", user_id)\
                .not_.is_("summary", "null")\
                .order("started_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return [row["summary"] for row in result.data if row.get("summary")]
        except Exception as e:
            logger.error(f"Error getting summaries: {e}")
            return []
    
    # ==========================================
    # ORDERS
    # ==========================================
    
    def create_order(self, order: Order) -> Order:
        """Create a new order"""
        data = {
            "user_id": order.user_id,
            "requested_by": order.requested_by,
            "order_type": order.order_type,
            "items": [item.model_dump() for item in order.items],
            "total_amount": order.total_amount,
            "platform": order.platform,
            "status": order.status.value
        }
        
        result = self.client.table("orders").insert(data).execute()
        order.id = result.data[0]["id"]
        return order
    
    def get_pending_orders(self, user_id: str) -> List[Order]:
        """Get pending orders for approval"""
        try:
            result = self.client.table("orders")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "pending")\
                .order("created_at", desc=True)\
                .execute()
            
            return [self._row_to_order(row) for row in result.data]
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []
    
    def _row_to_order(self, row: dict) -> Order:
        """Convert DB row to Order"""
        return Order(
            id=row["id"],
            user_id=row["user_id"],
            requested_by=row["requested_by"],
            approved_by=row.get("approved_by"),
            order_type=row["order_type"],
            items=[OrderItem(**item) for item in row["items"]],
            total_amount=row.get("total_amount"),
            status=OrderStatus(row["status"]),
            platform=row.get("platform"),
            rejection_reason=row.get("rejection_reason"),
            created_at=row["created_at"]
        )
    
    # ==========================================
    # REMINDERS
    # ==========================================
    
    def add_reminder(self, reminder: Reminder) -> Reminder:
        """Add a reminder"""
        data = {
            "user_id": reminder.user_id,
            "message": reminder.message,
            "remind_at": reminder.remind_at.isoformat(),
            "repeat_pattern": reminder.repeat_pattern,
            "category": reminder.category,
            "priority": reminder.priority
        }
        
        result = self.client.table("reminders").insert(data).execute()
        reminder.id = result.data[0]["id"]
        return reminder
    
    def get_upcoming_reminders(
        self,
        user_id: str,
        hours_ahead: int = 24
    ) -> List[Reminder]:
        """Get reminders due in the next N hours"""
        try:
            now = datetime.utcnow()
            until = now + timedelta(hours=hours_ahead)
            
            result = self.client.table("reminders")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .gte("remind_at", now.isoformat())\
                .lte("remind_at", until.isoformat())\
                .order("remind_at")\
                .execute()
            
            return [self._row_to_reminder(row) for row in result.data]
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []
    
    def _row_to_reminder(self, row: dict) -> Reminder:
        """Convert DB row to Reminder"""
        return Reminder(
            id=row["id"],
            user_id=row["user_id"],
            message=row["message"],
            remind_at=row["remind_at"],
            repeat_pattern=row.get("repeat_pattern"),
            is_active=row.get("is_active", True),
            category=row.get("category"),
            priority=row.get("priority", "normal")
        )
    
    # ==========================================
    # GROCERY LIST
    # ==========================================
    
    def add_to_grocery_list(self, item: GroceryItem) -> GroceryItem:
        """Add item to grocery list"""
        data = {
            "user_id": item.user_id,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "category": item.category,
            "added_by": item.added_by,
            "notes": item.notes
        }
        
        result = self.client.table("grocery_list").insert(data).execute()
        item.id = result.data[0]["id"]
        return item
    
    def get_grocery_list(self, user_id: str, include_purchased: bool = False) -> List[GroceryItem]:
        """Get grocery list"""
        try:
            query = self.client.table("grocery_list")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)
            
            if not include_purchased:
                query = query.eq("is_purchased", False)
            
            result = query.execute()
            
            return [
                GroceryItem(
                    id=row["id"],
                    user_id=row["user_id"],
                    item_name=row["item_name"],
                    quantity=row.get("quantity", 1),
                    unit=row.get("unit"),
                    category=row.get("category"),
                    added_by=row.get("added_by"),
                    is_purchased=row.get("is_purchased", False),
                    notes=row.get("notes")
                )
                for row in result.data
            ]
        except Exception as e:
            logger.error(f"Error getting grocery list: {e}")
            return []
    
    def clear_grocery_list(self, user_id: str):
        """Mark all items as purchased"""
        try:
            self.client.table("grocery_list")\
                .update({"is_purchased": True, "purchased_at": datetime.utcnow().isoformat()})\
                .eq("user_id", user_id)\
                .eq("is_purchased", False)\
                .execute()
        except Exception as e:
            logger.error(f"Error clearing grocery list: {e}")
