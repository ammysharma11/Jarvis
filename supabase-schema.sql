-- ============================================
-- JARVIS HOME ASSISTANT - DATABASE SCHEMA
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name VARCHAR(100) NOT NULL DEFAULT 'Friend',
    role VARCHAR(20) NOT NULL DEFAULT 'adult' CHECK (role IN ('adult', 'child', 'elderly', 'maid', 'guest')),
    age INTEGER,
    voice_id VARCHAR(100),
    
    -- Preferences
    preferred_language VARCHAR(20) DEFAULT 'english',
    preferred_response_length VARCHAR(20) DEFAULT 'medium' CHECK (preferred_response_length IN ('short', 'medium', 'long')),
    
    -- Permissions
    daily_order_limit DECIMAL(10,2),
    requires_approval BOOLEAN DEFAULT false,
    can_approve_orders BOOLEAN DEFAULT false,
    
    -- Medical info (for elderly) - stored as JSON
    medical_info JSONB,
    
    -- Stats
    total_conversations INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_interaction TIMESTAMPTZ
);

-- ============================================
-- FACTS TABLE (What we learn about users)
-- ============================================
CREATE TABLE IF NOT EXISTS facts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    fact TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'other',
    importance VARCHAR(20) DEFAULT 'normal' CHECK (importance IN ('low', 'normal', 'high', 'critical')),
    source_conversation UUID,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_referenced TIMESTAMPTZ,
    reference_count INTEGER DEFAULT 0
);

-- ============================================
-- PREFERENCES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    source_conversation UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, category, key)
);

-- ============================================
-- CONVERSATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    alexa_session_id VARCHAR(255),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    summary TEXT,
    message_count INTEGER DEFAULT 0,
    platform VARCHAR(50) DEFAULT 'alexa'
);

-- ============================================
-- MESSAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    content TEXT NOT NULL,
    tool_name VARCHAR(100),
    tool_call_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ORDERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT REFERENCES users(id),
    requested_by TEXT REFERENCES users(id),
    approved_by TEXT REFERENCES users(id),
    
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('grocery', 'medicine', 'other')),
    items JSONB NOT NULL,
    total_amount DECIMAL(10,2),
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'ordered', 'delivered', 'cancelled')),
    platform VARCHAR(50),
    
    rejection_reason TEXT,
    external_order_id VARCHAR(255),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    ordered_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

-- ============================================
-- REMINDERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    remind_at TIMESTAMPTZ NOT NULL,
    
    repeat_pattern VARCHAR(50),
    repeat_until TIMESTAMPTZ,
    
    is_active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMPTZ,
    trigger_count INTEGER DEFAULT 0,
    
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'normal',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- GROCERY LIST TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS grocery_list (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1,
    unit VARCHAR(50),
    category VARCHAR(50),
    added_by TEXT REFERENCES users(id),
    is_purchased BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    purchased_at TIMESTAMPTZ
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_facts_user ON facts(user_id);
CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(user_id, category);
CREATE INDEX IF NOT EXISTS idx_facts_importance ON facts(user_id, importance);

CREATE INDEX IF NOT EXISTS idx_preferences_user ON preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_preferences_lookup ON preferences(user_id, category, key);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(alexa_session_id);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(user_id, status);

CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(user_id, remind_at) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_grocery_list_user ON grocery_list(user_id) WHERE is_purchased = false;

-- ============================================
-- ROW LEVEL SECURITY (Enabled but open for now)
-- ============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE grocery_list ENABLE ROW LEVEL SECURITY;

-- Allow all for service role (our Lambda uses service key)
CREATE POLICY "Allow all for service role" ON users FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON facts FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON preferences FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON conversations FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON orders FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON reminders FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON grocery_list FOR ALL USING (true);

-- ============================================
-- DONE!
-- ============================================
