-- Migration: Add Stripe Checkout support to card_orders table
-- Run this in Supabase SQL Editor

-- Add new columns for Stripe Checkout sessions
ALTER TABLE card_orders
  ADD COLUMN IF NOT EXISTS stripe_checkout_session_id TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS player_id INTEGER,
  ADD COLUMN IF NOT EXISTS player_name TEXT,
  ADD COLUMN IF NOT EXISTS total_cards INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS currency TEXT DEFAULT 'usd';

-- Make payment_intent_id non-unique (Checkout sessions have their own unique ID)
-- Drop the unique constraint if it exists
ALTER TABLE card_orders
  DROP CONSTRAINT IF EXISTS card_orders_stripe_payment_intent_id_key;

-- Create index for checkout session lookups
CREATE INDEX IF NOT EXISTS idx_card_orders_checkout_session
  ON card_orders (stripe_checkout_session_id);

-- Create index for player lookups
CREATE INDEX IF NOT EXISTS idx_card_orders_player_id
  ON card_orders (player_id);

-- Comment on new columns
COMMENT ON COLUMN card_orders.stripe_checkout_session_id IS 'Stripe Checkout Session ID for the order';
COMMENT ON COLUMN card_orders.player_id IS 'Player ID for card personalization';
COMMENT ON COLUMN card_orders.player_name IS 'Player name for card personalization';
COMMENT ON COLUMN card_orders.total_cards IS 'Total number of cards in the order';
COMMENT ON COLUMN card_orders.currency IS 'Currency code (e.g., usd)';
