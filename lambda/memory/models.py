"""Pydantic models for memory system"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADULT = "adult"
    CHILD = "child"
    ELDERLY = "elderly"
    MAID = "maid"
    GUEST = "guest"


class Importance(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class OrderStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Message(BaseModel):
    """Single conversation message"""
    id: Optional[str] = None
    role: str  # user, assistant, tool, system
    content: str
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    """A conversation session"""
    id: Optional[str] = None
    user_id: str
    alexa_session_id: Optional[str] = None
    messages: List[Message] = []
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None


class UserFact(BaseModel):
    """A fact learned about a user"""
    id: Optional[str] = None
    user_id: str
    fact: str
    category: str  # food, health, habit, preference, family, work, other
    importance: Importance = Importance.NORMAL
    source_conversation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_referenced: Optional[datetime] = None
    reference_count: int = 0


class UserPreference(BaseModel):
    """A user preference"""
    id: Optional[str] = None
    user_id: str
    category: str
    key: str
    value: str
    confidence: float = 1.0
    source_conversation: Optional[str] = None


class MedicalInfo(BaseModel):
    """Medical information for elderly users"""
    medicines: List[Dict[str, Any]] = []  # {name, dosage, timing, notes}
    allergies: List[str] = []
    conditions: List[str] = []
    emergency_contacts: List[Dict[str, str]] = []  # {name, phone, relation}
    doctor_info: Optional[Dict[str, str]] = None  # {name, phone, hospital}


class UserProfile(BaseModel):
    """Complete user profile"""
    id: str
    name: str
    role: UserRole = UserRole.ADULT
    age: Optional[int] = None
    voice_id: Optional[str] = None
    
    # Preferences
    preferred_language: str = "english"
    preferred_response_length: str = "medium"
    
    # Permissions
    daily_order_limit: Optional[float] = None
    requires_approval: bool = False
    can_approve_orders: bool = False
    
    # Medical (for elderly)
    medical_info: Optional[MedicalInfo] = None
    
    # Stats
    total_conversations: int = 0
    created_at: Optional[datetime] = None
    last_interaction: Optional[datetime] = None


class OrderItem(BaseModel):
    """Single item in an order"""
    name: str
    quantity: float = 1
    unit: Optional[str] = None  # kg, pieces, packets
    estimated_price: Optional[float] = None
    notes: Optional[str] = None


class Order(BaseModel):
    """An order request"""
    id: Optional[str] = None
    user_id: str
    requested_by: str
    approved_by: Optional[str] = None
    order_type: str  # grocery, medicine, other
    items: List[OrderItem]
    total_amount: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    platform: Optional[str] = None  # zepto, blinkit, pharmeasy
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Reminder(BaseModel):
    """A reminder"""
    id: Optional[str] = None
    user_id: str
    message: str
    remind_at: datetime
    repeat_pattern: Optional[str] = None  # daily, weekly, monthly
    is_active: bool = True
    category: Optional[str] = None  # medicine, task, event
    priority: str = "normal"


class GroceryItem(BaseModel):
    """Item in grocery list"""
    id: Optional[str] = None
    user_id: str
    item_name: str
    quantity: float = 1
    unit: Optional[str] = None
    category: Optional[str] = None
    added_by: Optional[str] = None
    is_purchased: bool = False
    notes: Optional[str] = None
