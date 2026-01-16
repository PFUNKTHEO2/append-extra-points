/**
 * Stripe Payment Processing - Cloud Functions
 * Handles payments, subscriptions, and webhooks for ProdigyRanking
 */

const functions = require('@google-cloud/functions-framework');
const cors = require('cors');
const Stripe = require('stripe');
const { createClient } = require('@supabase/supabase-js');

// Initialize Stripe with secret key
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_placeholder');

// Lazy-initialize Supabase (only when needed)
let _supabase = null;
function getSupabase() {
  if (!_supabase) {
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (!key) {
      console.warn('SUPABASE_SERVICE_ROLE_KEY not set - database operations will fail');
    }
    _supabase = createClient(
      process.env.SUPABASE_URL || 'https://xqkwvywcxmnfimkubtyo.supabase.co',
      key || 'placeholder-key-for-init'
    );
  }
  return _supabase;
}

// CORS middleware
const corsMiddleware = cors({ origin: true });

function withCors(handler) {
  return (req, res) => {
    corsMiddleware(req, res, () => handler(req, res));
  };
}

function errorResponse(res, statusCode, message) {
  res.set('Cache-Control', 'no-store');
  return res.status(statusCode).json({
    error: message,
    timestamp: new Date().toISOString()
  });
}

// =====================================================================
// HELPER FUNCTIONS
// =====================================================================

/**
 * Get or create a Stripe customer for a user
 */
async function getOrCreateCustomer(userId, email = null) {
  // Check if customer already exists in Supabase
  const { data: existing, error: fetchError } = await getSupabase()
    .from('stripe_customers')
    .select('stripe_customer_id')
    .eq('user_id', userId)
    .single();

  if (existing?.stripe_customer_id) {
    return existing.stripe_customer_id;
  }

  // Create new Stripe customer
  const customer = await stripe.customers.create({
    metadata: { user_id: userId },
    email: email
  });

  // Save mapping to Supabase
  const { error: insertError } = await getSupabase()
    .from('stripe_customers')
    .insert({
      user_id: userId,
      stripe_customer_id: customer.id
    });

  if (insertError) {
    console.error('Error saving customer mapping:', insertError);
  }

  return customer.id;
}

/**
 * Get user ID from Stripe customer ID
 */
async function getUserIdFromCustomer(customerId) {
  const { data, error } = await getSupabase()
    .from('stripe_customers')
    .select('user_id')
    .eq('stripe_customer_id', customerId)
    .single();

  return data?.user_id;
}

// =====================================================================
// PAYMENT INTENT ENDPOINTS
// =====================================================================

/**
 * POST /stripe/create-payment-intent
 * Create a payment intent for a one-time purchase (cards, reports)
 *
 * Body: {
 *   amount: number (cents),
 *   currency: string (default 'usd'),
 *   metadata: { product_type, product_id, ... }
 * }
 */
async function createPaymentIntent(req, res) {
  try {
    const { amount, currency = 'usd', metadata = {} } = req.body;
    const userId = req.headers['x-user-id'];

    if (!userId) {
      return errorResponse(res, 401, 'User ID required');
    }

    if (!amount || amount < 50) { // Minimum $0.50
      return errorResponse(res, 400, 'Amount must be at least 50 cents');
    }

    // Get or create Stripe customer
    const customerId = await getOrCreateCustomer(userId);

    // Create payment intent
    const paymentIntent = await stripe.paymentIntents.create({
      amount,
      currency,
      customer: customerId,
      metadata: {
        ...metadata,
        user_id: userId
      },
      automatic_payment_methods: {
        enabled: true
      }
    });

    console.log(`Created payment intent ${paymentIntent.id} for user ${userId}`);

    res.json({
      clientSecret: paymentIntent.client_secret,
      paymentIntentId: paymentIntent.id
    });
  } catch (error) {
    console.error('Error creating payment intent:', error);
    return errorResponse(res, 500, error.message);
  }
}

// =====================================================================
// SUBSCRIPTION ENDPOINTS
// =====================================================================

/**
 * POST /stripe/create-subscription
 * Create a new subscription for a user
 *
 * Body: {
 *   priceId: string (Stripe price ID like 'price_xxx')
 * }
 */
async function createSubscription(req, res) {
  try {
    const { priceId } = req.body;
    const userId = req.headers['x-user-id'];

    if (!userId) {
      return errorResponse(res, 401, 'User ID required');
    }

    if (!priceId) {
      return errorResponse(res, 400, 'priceId is required');
    }

    // Get or create customer
    const customerId = await getOrCreateCustomer(userId);

    // Check for existing active subscription
    const { data: existingSub } = await getSupabase()
      .from('subscriptions')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'active')
      .single();

    if (existingSub) {
      return errorResponse(res, 400, 'User already has an active subscription');
    }

    // Create subscription with incomplete status
    const subscription = await stripe.subscriptions.create({
      customer: customerId,
      items: [{ price: priceId }],
      payment_behavior: 'default_incomplete',
      payment_settings: {
        save_default_payment_method: 'on_subscription'
      },
      expand: ['latest_invoice.payment_intent'],
      metadata: {
        user_id: userId
      }
    });

    console.log(`Created subscription ${subscription.id} for user ${userId}`);

    res.json({
      subscriptionId: subscription.id,
      clientSecret: subscription.latest_invoice.payment_intent.client_secret,
      status: subscription.status
    });
  } catch (error) {
    console.error('Error creating subscription:', error);
    return errorResponse(res, 500, error.message);
  }
}

/**
 * POST /stripe/cancel-subscription
 * Cancel a user's subscription (at period end)
 */
async function cancelSubscription(req, res) {
  try {
    const userId = req.headers['x-user-id'];

    if (!userId) {
      return errorResponse(res, 401, 'User ID required');
    }

    // Get user's subscription from Supabase
    const { data: sub, error } = await getSupabase()
      .from('subscriptions')
      .select('stripe_subscription_id')
      .eq('user_id', userId)
      .eq('status', 'active')
      .single();

    if (error || !sub) {
      return errorResponse(res, 404, 'No active subscription found');
    }

    // Cancel at period end (user keeps access until then)
    const subscription = await stripe.subscriptions.update(
      sub.stripe_subscription_id,
      { cancel_at_period_end: true }
    );

    console.log(`Cancelled subscription ${subscription.id} for user ${userId}`);

    res.json({
      message: 'Subscription will be cancelled at period end',
      cancelAt: subscription.cancel_at,
      currentPeriodEnd: subscription.current_period_end
    });
  } catch (error) {
    console.error('Error cancelling subscription:', error);
    return errorResponse(res, 500, error.message);
  }
}

/**
 * GET /stripe/subscription-status
 * Get current subscription status for a user
 */
async function getSubscriptionStatus(req, res) {
  try {
    const userId = req.headers['x-user-id'] || req.query.user_id;

    if (!userId) {
      return errorResponse(res, 401, 'User ID required');
    }

    const { data: sub, error } = await getSupabase()
      .from('subscriptions')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    if (error || !sub) {
      return res.json({
        hasSubscription: false,
        plan: 'free',
        status: null
      });
    }

    res.json({
      hasSubscription: sub.status === 'active',
      plan: sub.plan,
      status: sub.status,
      currentPeriodEnd: sub.current_period_end,
      cancelAtPeriodEnd: sub.cancel_at_period_end
    });
  } catch (error) {
    console.error('Error getting subscription status:', error);
    return errorResponse(res, 500, error.message);
  }
}

// =====================================================================
// CUSTOMER PORTAL
// =====================================================================

/**
 * POST /stripe/create-portal-session
 * Create a Stripe Customer Portal session for managing subscriptions
 */
async function createPortalSession(req, res) {
  try {
    const userId = req.headers['x-user-id'];
    const { returnUrl } = req.body;

    if (!userId) {
      return errorResponse(res, 401, 'User ID required');
    }

    // Get customer ID
    const { data: customer } = await getSupabase()
      .from('stripe_customers')
      .select('stripe_customer_id')
      .eq('user_id', userId)
      .single();

    if (!customer) {
      return errorResponse(res, 404, 'No customer found');
    }

    // Create portal session
    const session = await stripe.billingPortal.sessions.create({
      customer: customer.stripe_customer_id,
      return_url: returnUrl || 'https://theprodigychain.com/account'
    });

    res.json({ url: session.url });
  } catch (error) {
    console.error('Error creating portal session:', error);
    return errorResponse(res, 500, error.message);
  }
}

// =====================================================================
// PRODUCTS/PRICES
// =====================================================================

/**
 * GET /stripe/products
 * Get available products and prices
 */
async function getProducts(req, res) {
  try {
    // Fetch active products with their prices
    const products = await stripe.products.list({
      active: true,
      expand: ['data.default_price']
    });

    const prices = await stripe.prices.list({
      active: true,
      limit: 100
    });

    // Format response
    const formattedProducts = products.data.map(product => ({
      id: product.id,
      name: product.name,
      description: product.description,
      images: product.images,
      metadata: product.metadata,
      defaultPrice: product.default_price ? {
        id: product.default_price.id,
        amount: product.default_price.unit_amount,
        currency: product.default_price.currency,
        interval: product.default_price.recurring?.interval
      } : null,
      prices: prices.data
        .filter(p => p.product === product.id)
        .map(p => ({
          id: p.id,
          amount: p.unit_amount,
          currency: p.currency,
          interval: p.recurring?.interval
        }))
    }));

    res.set('Cache-Control', 'public, max-age=300'); // Cache 5 min
    res.json({ products: formattedProducts });
  } catch (error) {
    console.error('Error fetching products:', error);
    return errorResponse(res, 500, error.message);
  }
}

// =====================================================================
// WEBHOOK HANDLER
// =====================================================================

/**
 * POST /stripe/webhook
 * Handle Stripe webhook events
 */
async function handleWebhook(req, res) {
  const sig = req.headers['stripe-signature'];
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  let event;

  try {
    // Verify webhook signature
    if (webhookSecret) {
      event = stripe.webhooks.constructEvent(
        req.rawBody || req.body,
        sig,
        webhookSecret
      );
    } else {
      // In test mode without signature verification
      event = req.body;
      console.warn('Webhook signature verification disabled - test mode only!');
    }
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  console.log(`Received webhook: ${event.type}`);

  try {
    switch (event.type) {
      case 'payment_intent.succeeded':
        await handlePaymentSuccess(event.data.object);
        break;

      case 'payment_intent.payment_failed':
        await handlePaymentFailed(event.data.object);
        break;

      case 'customer.subscription.created':
      case 'customer.subscription.updated':
        await handleSubscriptionUpdate(event.data.object);
        break;

      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(event.data.object);
        break;

      case 'invoice.paid':
        await handleInvoicePaid(event.data.object);
        break;

      case 'invoice.payment_failed':
        await handleInvoiceFailed(event.data.object);
        break;

      case 'checkout.session.completed':
        await handleCheckoutSessionCompleted(event.data.object);
        break;

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    res.json({ received: true });
  } catch (error) {
    console.error('Error processing webhook:', error);
    return res.status(500).json({ error: error.message });
  }
}

// =====================================================================
// WEBHOOK EVENT HANDLERS
// =====================================================================

async function handlePaymentSuccess(paymentIntent) {
  console.log(`Payment succeeded: ${paymentIntent.id}`);

  const userId = paymentIntent.metadata?.user_id;
  const productType = paymentIntent.metadata?.product_type;
  const productId = paymentIntent.metadata?.product_id;

  if (!userId) {
    console.warn('Payment without user_id in metadata');
    return;
  }

  // Record purchase in Supabase
  if (productType) {
    const { error } = await getSupabase()
      .from('purchases')
      .upsert({
        user_id: userId,
        stripe_payment_intent_id: paymentIntent.id,
        product_type: productType,
        product_id: productId,
        amount: paymentIntent.amount,
        status: 'completed'
      }, {
        onConflict: 'stripe_payment_intent_id'
      });

    if (error) {
      console.error('Error recording purchase:', error);
    }
  }

  // Handle card orders
  if (productType === 'card_order') {
    const { error } = await getSupabase()
      .from('card_orders')
      .update({ status: 'paid', updated_at: new Date().toISOString() })
      .eq('stripe_payment_intent_id', paymentIntent.id);

    if (error) {
      console.error('Error updating card order:', error);
    }
  }
}

async function handlePaymentFailed(paymentIntent) {
  console.log(`Payment failed: ${paymentIntent.id}`);

  const { error } = await getSupabase()
    .from('purchases')
    .update({ status: 'failed' })
    .eq('stripe_payment_intent_id', paymentIntent.id);

  if (error) {
    console.error('Error updating failed payment:', error);
  }
}

async function handleCheckoutSessionCompleted(session) {
  console.log(`Checkout session completed: ${session.id}`);

  const productType = session.metadata?.product_type;
  const playerId = session.metadata?.player_id;
  const playerName = session.metadata?.player_name;
  const userId = session.metadata?.user_id;

  // Only process card orders
  if (productType !== 'card_order') {
    console.log(`Checkout session ${session.id} is not a card order, skipping`);
    return;
  }

  // Get line items for order details
  const lineItems = await stripe.checkout.sessions.listLineItems(session.id);

  // Calculate total cards from line items
  let totalCards = 0;
  for (const item of lineItems.data) {
    // 5-pack or 10-pack - extract quantity from product name or use quantity
    const quantity = item.quantity || 1;
    const productName = item.description || '';
    if (productName.includes('10')) {
      totalCards += quantity * 10;
    } else if (productName.includes('5')) {
      totalCards += quantity * 5;
    }
  }

  // Get shipping details
  const shipping = session.shipping_details || session.customer_details;

  // Record the card order in Supabase
  const { error } = await getSupabase()
    .from('card_orders')
    .insert({
      stripe_checkout_session_id: session.id,
      stripe_payment_intent_id: session.payment_intent,
      user_id: userId || null,
      player_id: playerId ? parseInt(playerId) : null,
      player_name: playerName || null,
      total_cards: totalCards,
      total: session.amount_total,
      currency: session.currency,
      status: 'paid',
      shipping_name: shipping?.name || null,
      shipping_address: shipping?.address || null,
      shipping_email: session.customer_details?.email || null,
      paid_at: new Date().toISOString()
    });

  if (error) {
    console.error('Error recording card order:', error);
  } else {
    console.log(`Card order recorded: ${totalCards} cards for player ${playerName} (${playerId})`);
  }
}

async function handleSubscriptionUpdate(subscription) {
  console.log(`Subscription update: ${subscription.id} - ${subscription.status}`);

  const userId = await getUserIdFromCustomer(subscription.customer);

  if (!userId) {
    console.warn('Subscription update without user mapping:', subscription.customer);
    return;
  }

  // Determine plan from price ID
  let plan = 'pro'; // default
  const priceId = subscription.items?.data[0]?.price?.id;
  if (priceId?.includes('elite')) {
    plan = 'elite';
  }

  const { error } = await getSupabase()
    .from('subscriptions')
    .upsert({
      user_id: userId,
      stripe_subscription_id: subscription.id,
      status: subscription.status,
      plan: plan,
      current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
      cancel_at_period_end: subscription.cancel_at_period_end,
      updated_at: new Date().toISOString()
    }, {
      onConflict: 'stripe_subscription_id'
    });

  if (error) {
    console.error('Error updating subscription:', error);
  }
}

async function handleSubscriptionDeleted(subscription) {
  console.log(`Subscription deleted: ${subscription.id}`);

  const { error } = await getSupabase()
    .from('subscriptions')
    .update({
      status: 'canceled',
      updated_at: new Date().toISOString()
    })
    .eq('stripe_subscription_id', subscription.id);

  if (error) {
    console.error('Error marking subscription deleted:', error);
  }
}

async function handleInvoicePaid(invoice) {
  console.log(`Invoice paid: ${invoice.id}`);
  // Subscription renewals are handled via subscription.updated webhook
}

async function handleInvoiceFailed(invoice) {
  console.log(`Invoice failed: ${invoice.id}`);

  if (invoice.subscription) {
    const { error } = await getSupabase()
      .from('subscriptions')
      .update({
        status: 'past_due',
        updated_at: new Date().toISOString()
      })
      .eq('stripe_subscription_id', invoice.subscription);

    if (error) {
      console.error('Error updating subscription status:', error);
    }
  }
}

// =====================================================================
// CHECKOUT SESSION FOR CARD ORDERS
// =====================================================================

/**
 * POST /stripe/create-card-checkout
 * Create a Stripe Checkout Session for physical card orders
 *
 * Body: {
 *   lineItems: [{ priceId: string, quantity: number }],
 *   playerId: number,
 *   playerName: string,
 *   successUrl: string,
 *   cancelUrl: string
 * }
 */
async function createCardCheckout(req, res) {
  try {
    const { lineItems, playerId, playerName, successUrl, cancelUrl } = req.body;
    const userId = req.headers['x-user-id'];

    if (!lineItems || lineItems.length === 0) {
      return errorResponse(res, 400, 'lineItems required');
    }

    // Get or create customer if user is logged in
    let customerId = null;
    if (userId) {
      customerId = await getOrCreateCustomer(userId);
    }

    // Create checkout session
    const sessionConfig = {
      mode: 'payment',
      line_items: lineItems.map(item => ({
        price: item.priceId,
        quantity: item.quantity,
      })),
      shipping_address_collection: {
        allowed_countries: ['US', 'CA', 'GB', 'DE', 'FR', 'AU', 'SE', 'FI', 'NO', 'DK', 'CZ', 'SK', 'CH', 'AT'],
      },
      success_url: successUrl || 'https://theprodigychain.com/checkout/success?session_id={CHECKOUT_SESSION_ID}',
      cancel_url: cancelUrl || 'https://theprodigychain.com',
      metadata: {
        product_type: 'card_order',
        player_id: playerId?.toString() || '',
        player_name: playerName || '',
        user_id: userId || '',
      },
    };

    // Add customer if logged in
    if (customerId) {
      sessionConfig.customer = customerId;
    }

    const session = await stripe.checkout.sessions.create(sessionConfig);

    console.log(`Created checkout session ${session.id} for card order`);

    res.json({
      sessionId: session.id,
      url: session.url
    });
  } catch (error) {
    console.error('Error creating card checkout:', error);
    return errorResponse(res, 500, error.message);
  }
}

// =====================================================================
// REGISTER HTTP FUNCTIONS
// =====================================================================

functions.http('stripeCreateCardCheckout', withCors(createCardCheckout));
functions.http('stripeCreatePaymentIntent', withCors(createPaymentIntent));
functions.http('stripeCreateSubscription', withCors(createSubscription));
functions.http('stripeCancelSubscription', withCors(cancelSubscription));
functions.http('stripeSubscriptionStatus', withCors(getSubscriptionStatus));
functions.http('stripeCreatePortalSession', withCors(createPortalSession));
functions.http('stripeProducts', withCors(getProducts));
functions.http('stripeWebhook', handleWebhook); // No CORS for webhook

// Export for index.js import
module.exports = {
  createCardCheckout,
  createPaymentIntent,
  createSubscription,
  cancelSubscription,
  getSubscriptionStatus,
  createPortalSession,
  getProducts,
  handleWebhook
};
