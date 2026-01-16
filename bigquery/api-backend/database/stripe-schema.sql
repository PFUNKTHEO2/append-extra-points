-- ============================================================
-- Stripe Payment Tables for ProdigyRanking
-- ============================================================
-- Run this in Supabase SQL Editor to set up payment tracking.
--
-- Tables:
-- 1. stripe_customers - User to Stripe customer ID mapping
-- 2. subscriptions - Subscription status tracking
-- 3. purchases - One-time purchases (reports, unlocks)
-- 4. card_orders - Physical trading card orders
-- ============================================================

-- ============================================================
-- 1. STRIPE CUSTOMERS TABLE
-- ============================================================
-- Maps Supabase user IDs to Stripe customer IDs

CREATE TABLE IF NOT EXISTS stripe_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    stripe_customer_id TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_stripe_customers_user_id
ON stripe_customers (user_id);

CREATE INDEX IF NOT EXISTS idx_stripe_customers_stripe_id
ON stripe_customers (stripe_customer_id);

-- ============================================================
-- 2. SUBSCRIPTIONS TABLE
-- ============================================================
-- Tracks user subscription status

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    status TEXT NOT NULL DEFAULT 'inactive', -- active, canceled, past_due, trialing, incomplete
    plan TEXT NOT NULL DEFAULT 'free', -- free, pro, elite
    price_id TEXT, -- Stripe price ID
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMPTZ,
    trial_start TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
ON subscriptions (user_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_status
ON subscriptions (status);

CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_id
ON subscriptions (stripe_subscription_id);

-- ============================================================
-- 3. PURCHASES TABLE
-- ============================================================
-- Tracks one-time purchases (player reports, unlocks, etc.)

CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    stripe_payment_intent_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    product_type TEXT NOT NULL, -- player_report, tournament_analysis, draft_guide, player_unlock
    product_id TEXT, -- player_id, tournament_id, etc.
    product_name TEXT,
    amount INTEGER NOT NULL, -- cents
    currency TEXT DEFAULT 'usd',
    status TEXT DEFAULT 'pending', -- pending, completed, failed, refunded
    metadata JSONB DEFAULT '{}',
    completed_at TIMESTAMPTZ,
    refunded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_purchases_user_id
ON purchases (user_id);

CREATE INDEX IF NOT EXISTS idx_purchases_status
ON purchases (status);

CREATE INDEX IF NOT EXISTS idx_purchases_product_type
ON purchases (product_type);

CREATE INDEX IF NOT EXISTS idx_purchases_payment_intent
ON purchases (stripe_payment_intent_id);

-- ============================================================
-- 4. CARD ORDERS TABLE
-- ============================================================
-- Tracks physical trading card orders

CREATE TABLE IF NOT EXISTS card_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    stripe_checkout_session_id TEXT UNIQUE,
    stripe_payment_intent_id TEXT,
    stripe_customer_id TEXT,

    -- Order status
    status TEXT DEFAULT 'pending', -- pending, paid, processing, printing, shipped, delivered, canceled

    -- Player info (for card personalization)
    player_id INTEGER,
    player_name TEXT,
    total_cards INTEGER DEFAULT 0,

    -- Shipping info
    shipping_name TEXT,
    shipping_address JSONB, -- {line1, line2, city, state, postal_code, country}
    shipping_email TEXT,
    shipping_phone TEXT,

    -- Order items
    items JSONB NOT NULL DEFAULT '[]', -- [{card_id, player_id, quantity, unit_price, rarity}]

    -- Pricing (all in cents)
    subtotal INTEGER NOT NULL DEFAULT 0,
    shipping_cost INTEGER DEFAULT 0,
    tax INTEGER DEFAULT 0,
    discount INTEGER DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    currency TEXT DEFAULT 'usd',

    -- Fulfillment
    tracking_number TEXT,
    tracking_carrier TEXT, -- usps, ups, fedex
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,

    -- Notes
    customer_notes TEXT,
    internal_notes TEXT,

    -- Timestamps
    paid_at TIMESTAMPTZ,
    canceled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_card_orders_user_id
ON card_orders (user_id);

CREATE INDEX IF NOT EXISTS idx_card_orders_status
ON card_orders (status);

CREATE INDEX IF NOT EXISTS idx_card_orders_payment_intent
ON card_orders (stripe_payment_intent_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE stripe_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_orders ENABLE ROW LEVEL SECURITY;

-- stripe_customers: Users can only view their own customer record
CREATE POLICY "Users can view own stripe customer" ON stripe_customers
    FOR SELECT USING (auth.uid() = user_id);

-- subscriptions: Users can view their own subscriptions
CREATE POLICY "Users can view own subscriptions" ON subscriptions
    FOR SELECT USING (auth.uid() = user_id);

-- purchases: Users can view their own purchases
CREATE POLICY "Users can view own purchases" ON purchases
    FOR SELECT USING (auth.uid() = user_id);

-- card_orders: Users can view their own orders
CREATE POLICY "Users can view own card orders" ON card_orders
    FOR SELECT USING (auth.uid() = user_id);

-- Service role has full access (for webhook handlers)
CREATE POLICY "Service role full access stripe_customers" ON stripe_customers
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access subscriptions" ON subscriptions
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access purchases" ON purchases
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access card_orders" ON card_orders
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_stripe_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for all tables
CREATE TRIGGER update_stripe_customers_updated_at
    BEFORE UPDATE ON stripe_customers
    FOR EACH ROW EXECUTE FUNCTION update_stripe_updated_at();

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_stripe_updated_at();

CREATE TRIGGER update_purchases_updated_at
    BEFORE UPDATE ON purchases
    FOR EACH ROW EXECUTE FUNCTION update_stripe_updated_at();

CREATE TRIGGER update_card_orders_updated_at
    BEFORE UPDATE ON card_orders
    FOR EACH ROW EXECUTE FUNCTION update_stripe_updated_at();

-- ============================================================
-- HELPER VIEWS
-- ============================================================

-- View for checking if a user has an active subscription
CREATE OR REPLACE VIEW user_subscription_status AS
SELECT
    user_id,
    plan,
    status,
    current_period_end,
    cancel_at_period_end,
    CASE
        WHEN status = 'active' AND current_period_end > NOW() THEN true
        WHEN status = 'trialing' AND trial_end > NOW() THEN true
        ELSE false
    END as is_active
FROM subscriptions
WHERE status IN ('active', 'trialing', 'past_due');

-- View for user's purchase history
CREATE OR REPLACE VIEW user_purchase_history AS
SELECT
    user_id,
    product_type,
    product_id,
    product_name,
    amount,
    status,
    completed_at,
    created_at
FROM purchases
WHERE status = 'completed'
ORDER BY completed_at DESC;

-- ============================================================
-- GRANTS
-- ============================================================

-- Anonymous users (not logged in) have no access
-- Authenticated users can read their own data (via RLS policies)
GRANT SELECT ON stripe_customers TO authenticated;
GRANT SELECT ON subscriptions TO authenticated;
GRANT SELECT ON purchases TO authenticated;
GRANT SELECT ON card_orders TO authenticated;

-- Grant access to views
GRANT SELECT ON user_subscription_status TO authenticated;
GRANT SELECT ON user_purchase_history TO authenticated;

-- Service role has full access
GRANT ALL ON stripe_customers TO service_role;
GRANT ALL ON subscriptions TO service_role;
GRANT ALL ON purchases TO service_role;
GRANT ALL ON card_orders TO service_role;

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE stripe_customers IS 'Maps Supabase users to Stripe customer IDs';
COMMENT ON TABLE subscriptions IS 'Tracks subscription status for premium features';
COMMENT ON TABLE purchases IS 'One-time purchases (player reports, unlocks)';
COMMENT ON TABLE card_orders IS 'Physical trading card orders';

COMMENT ON COLUMN subscriptions.plan IS 'free, pro ($9.99/mo), or elite ($24.99/mo)';
COMMENT ON COLUMN purchases.amount IS 'Amount in cents (e.g., 499 = $4.99)';
COMMENT ON COLUMN card_orders.items IS 'Array of {card_id, player_id, quantity, unit_price, rarity}';
