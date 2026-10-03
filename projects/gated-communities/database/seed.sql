-- =============================================================================
-- Gated Communities — Seed Data
-- =============================================================================
-- Sample data for development and testing.
-- Run after schema.sql: psql -d gated_communities -f seed.sql
-- =============================================================================

BEGIN;

-- =============================================================================
-- COMMUNITIES
-- =============================================================================

INSERT INTO communities (id, slug, name, description, visibility, status, settings, metadata, created_by)
VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'tech-innovators', 'Tech Innovators',
     'A community for technology enthusiasts and innovators to share ideas and collaborate.',
     'public', 'active',
     '{"features": {"blog": true, "events": true, "polls": true}, "permissions": {"can_post": "member", "can_comment": "member"}}',
     '{"category": "technology", "tags": ["tech", "innovation", "startups"]}',
     'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),

    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'creative-writers', 'Creative Writers',
     'A private community for writers to share their work and get feedback.',
     'private', 'active',
     '{"features": {"blog": true, "workshops": true}, "permissions": {"can_post": "member", "can_comment": "member"}}',
     '{"category": "writing", "tags": ["writing", "fiction", "poetry"]}',
     'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'),

    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'crypto-traders', 'Crypto Traders',
     'Hidden community for cryptocurrency traders to discuss strategies and market trends.',
     'hidden', 'active',
     '{"features": {"blog": true, "signals": true, "alerts": true}, "permissions": {"can_post": "tier2", "can_comment": "member"}}',
     '{"category": "finance", "tags": ["crypto", "trading", "defi"]}',
     'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33');

-- =============================================================================
-- TIERS
-- =============================================================================

INSERT INTO tiers (id, community_id, slug, name, description, price_cents, currency, billing_period, is_public, is_active, sort_order, benefits, metadata)
VALUES
    -- Tech Innovators tiers
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'free', 'Free',
     'Basic access to the community', 0, 'USD', 'monthly', true, true, 0,
     '["Access to public posts", "Comment on posts"]', '{"color": "#6b7280"}'),

    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'pro', 'Pro',
     'Full access with premium features', 2900, 'USD', 'monthly', true, true, 1,
     '["All free benefits", "Access to premium content", "Priority support", "Monthly AMA sessions"]', '{"color": "#3b82f6"}'),

    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'enterprise', 'Enterprise',
     'For teams and organizations', 9900, 'USD', 'monthly', true, true, 2,
     '["All Pro benefits", "Team management", "Custom branding", "Dedicated support", "API access"]', '{"color": "#8b5cf6"}'),

    -- Creative Writers tiers
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'free', 'Free',
     'Basic access to the community', 0, 'USD', 'monthly', true, true, 0,
     '["Access to public posts", "Comment on posts"]', '{"color": "#6b7280"}'),

    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'premium', 'Premium',
     'Full access with writing workshops', 1900, 'USD', 'monthly', true, true, 1,
     '["All free benefits", "Weekly writing workshops", "Peer review sessions", "Writing prompts"]', '{"color": "#ec4899"}'),

    -- Crypto Traders tiers
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'free', 'Free',
     'Basic access to the community', 0, 'USD', 'monthly', true, true, 0,
     '["Access to public posts", "Comment on posts"]', '{"color": "#6b7280"}'),

    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'signals', 'Signals',
     'Trading signals and market analysis', 4900, 'USD', 'monthly', true, true, 1,
     '["All free benefits", "Daily trading signals", "Market analysis reports", "Discord access"]', '{"color": "#f59e0b"}'),

    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'vip', 'VIP',
     'Premium signals and 1-on-1 mentoring', 19900, 'USD', 'monthly', true, true, 2,
     '["All Signals benefits", "1-on-1 mentoring", "Custom alerts", "Portfolio review"]', '{"color": "#ef4444"}');

-- =============================================================================
-- MEMBERS
-- =============================================================================

INSERT INTO members (id, community_id, user_id, tier_id, role, status, display_name, bio, joined_at, last_active_at, notification_prefs, metadata)
VALUES
    -- Tech Innovators members
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'owner', 'active', 'Alice Johnson', 'Tech enthusiast and startup founder', '2025-01-15 10:00:00+00', '2026-10-01 14:30:00+00', '{"email": true, "push": true, "digest": "weekly"}', '{"location": "San Francisco", "company": "TechCorp"}'),

    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'admin', 'active', 'Bob Smith', 'Software engineer and AI researcher', '2025-02-01 09:00:00+00', '2026-10-02 11:00:00+00', '{"email": true, "push": true, "digest": "daily"}', '{"location": "New York", "company": "AI Labs"}'),

    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'member', 'active', 'Carol Davis', 'Product manager', '2025-03-10 14:00:00+00', '2026-09-30 16:45:00+00', '{"email": true, "push": false, "digest": "weekly"}', '{"location": "London", "company": "ProductCo"}'),

    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'member', 'active', 'David Wilson', 'Frontend developer', '2025-04-20 11:00:00+00', '2026-10-01 09:15:00+00', '{"email": true, "push": true, "digest": "daily"}', '{"location": "Berlin", "company": "WebDev Inc"}'),

    -- Creative Writers members
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'owner', 'active', 'Eve Martinez', 'Novelist and writing coach', '2025-01-20 08:00:00+00', '2026-10-02 10:00:00+00', '{"email": true, "push": true, "digest": "weekly"}', '{"location": "Madrid", "published_works": 3}'),

    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'member', 'active', 'Frank Brown', 'Poet and freelance writer', '2025-02-15 13:00:00+00', '2026-09-28 15:30:00+00', '{"email": true, "push": false, "digest": "monthly"}', '{"location": "Paris", "published_works": 1}'),

    -- Crypto Traders members
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'owner', 'active', 'Grace Lee', 'Crypto trader and analyst', '2025-01-10 07:00:00+00', '2026-10-02 12:00:00+00', '{"email": true, "push": true, "digest": "daily"}', '{"location": "Singapore", "trading_experience": "5 years"}'),

    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'moderator', 'active', 'Henry Kim', 'DeFi researcher', '2025-02-05 10:00:00+00', '2026-10-01 08:00:00+00', '{"email": true, "push": true, "digest": "daily"}', '{"location": "Seoul", "trading_experience": "3 years"}');

-- =============================================================================
-- CONTENT
-- =============================================================================

INSERT INTO content (id, community_id, author_id, parent_id, content_type, status, title, body, body_rendered, media_urls, tags, metadata, like_count, comment_count, share_count, view_count, is_pinned, published_at)
VALUES
    -- Tech Innovators content
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', NULL, 'post', 'published',
     'Welcome to Tech Innovators!',
     'Welcome to our community! This is a space for tech enthusiasts to share ideas, discuss innovations, and collaborate on exciting projects. Feel free to introduce yourself and share what you are working on.',
     '<p>Welcome to our community! This is a space for tech enthusiasts to share ideas, discuss innovations, and collaborate on exciting projects. Feel free to introduce yourself and share what you are working on.</p>',
     '[]', '["welcome", "announcement"]', '{"featured": true}', 15, 3, 2, 150, true, '2025-01-15 10:00:00+00'),

    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', NULL, 'post', 'published',
     'The Future of AI in Software Development',
     'AI is rapidly transforming how we write, test, and deploy software. In this post, I want to share my thoughts on where we are headed and what developers should focus on to stay relevant.',
     '<p>AI is rapidly transforming how we write, test, and deploy software. In this post, I want to share my thoughts on where we are headed and what developers should focus on to stay relevant.</p>',
     '["https://example.com/images/ai-future.jpg"]', '["ai", "software-development", "future"]', '{"reading_time": 5}', 42, 8, 12, 890, false, '2025-06-20 14:00:00+00'),

    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'comment', 'published',
     NULL,
     'Great insights! I think AI will augment developers rather than replace them. The key is to learn how to work alongside these tools effectively.',
     '<p>Great insights! I think AI will augment developers rather than replace them. The key is to learn how to work alongside these tools effectively.</p>',
     '[]', '[]', '{}', 5, 0, 0, 45, false, '2025-06-20 15:30:00+00'),

    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'comment', 'published',
     NULL,
     'I agree with Carol. The developers who embrace AI tools will be far more productive than those who ignore them.',
     '<p>I agree with Carol. The developers who embrace AI tools will be far more productive than those who ignore them.</p>',
     '[]', '[]', '{}', 3, 0, 0, 32, false, '2025-06-20 16:00:00+00'),

    -- Creative Writers content
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', NULL, 'post', 'published',
     'Writing Prompt: The Last Library',
     'Imagine a world where all digital information has been lost. The last physical library stands as the sole repository of human knowledge. Write a story about someone who discovers this library.',
     '<p>Imagine a world where all digital information has been lost. The last physical library stands as the sole repository of human knowledge. Write a story about someone who discovers this library.</p>',
     '[]', '["writing-prompt", "fiction", "creative-writing"]', '{"prompt_type": "fiction", "difficulty": "intermediate"}', 28, 12, 5, 420, true, '2025-03-01 09:00:00+00'),

    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'reply', 'published',
     NULL,
     'Here is my attempt at the prompt. The dust motes danced in the shaft of light as Emma pushed open the heavy oak door...',
     '<p>Here is my attempt at the prompt. The dust motes danced in the shaft of light as Emma pushed open the heavy oak door...</p>',
     '[]', '[]', '{}', 8, 2, 1, 67, false, '2025-03-02 14:00:00+00'),

    -- Crypto Traders content
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', NULL, 'post', 'published',
     'Market Analysis: Bitcoin Q4 2026 Outlook',
     'As we enter Q4 2026, Bitcoin is showing strong bullish signals. Key resistance levels to watch include $150K and $175K. On-chain metrics suggest accumulation by long-term holders.',
     '<p>As we enter Q4 2026, Bitcoin is showing strong bullish signals. Key resistance levels to watch include $150K and $175K. On-chain metrics suggest accumulation by long-term holders.</p>',
     '["https://example.com/images/btc-chart.png"]', '["bitcoin", "market-analysis", "trading"]', '{"signal": "bullish", "timeframe": "Q4 2026"}', 67, 15, 23, 1200, true, '2026-10-01 08:00:00+00'),

    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'comment', 'published',
     NULL,
     'Great analysis! I am also watching the $150K level closely. The funding rates suggest we might see a short squeeze if we break through.',
     '<p>Great analysis! I am also watching the $150K level closely. The funding rates suggest we might see a short squeeze if we break through.</p>',
     '[]', '[]', '{}', 12, 0, 0, 89, false, '2026-10-01 09:30:00+00');

-- =============================================================================
-- MODERATION ACTIONS
-- =============================================================================

INSERT INTO moderation_actions (id, community_id, target_member_id, target_content_id, action_type, status, reason, details, duration_hours, expires_at, applied_by, applied_at)
VALUES
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', NULL, 'warn', 'applied',
     'First warning: Please keep discussions respectful and on-topic.',
     '{"rule_violated": "conduct", "severity": "low"}',
     NULL, NULL, 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '2025-07-15 10:00:00+00'),

    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', NULL, 'mute', 'applied',
     'Muted for 24 hours due to repeated off-topic posts.',
     '{"rule_violated": "spam", "severity": "medium", "previous_warnings": 1}',
     24, '2025-07-16 10:00:00+00', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '2025-07-15 10:00:00+00'),

    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', NULL, 'note', 'applied',
     'Positive note: Frank has been an excellent community member. Keep up the great work!',
     '{"note_type": "positive", "category": "contribution"}',
     NULL, NULL, 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', '2025-04-01 09:00:00+00');

-- =============================================================================
-- REPUTATION SCORES
-- =============================================================================

INSERT INTO reputation_scores (id, community_id, member_id, score, total_earned, total_deducted, breakdown, last_event_at)
VALUES
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 1250, 1300, 50,
     '{"posts": 500, "comments": 300, "likes_received": 400, "warnings": -50}', '2026-10-01 14:30:00+00'),

    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 980, 1000, 20,
     '{"posts": 400, "comments": 250, "likes_received": 300, "warnings": -20}', '2026-10-02 11:00:00+00'),

    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 450, 500, 50,
     '{"posts": 200, "comments": 150, "likes_received": 100, "warnings": -50}', '2026-09-30 16:45:00+00'),

    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 320, 400, 80,
     '{"posts": 150, "comments": 100, "likes_received": 50, "warnings": -80}', '2026-10-01 09:15:00+00'),

    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 890, 900, 10,
     '{"posts": 350, "comments": 200, "likes_received": 300, "warnings": -10}', '2026-10-02 10:00:00+00'),

    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 210, 250, 40,
     '{"posts": 100, "comments": 80, "likes_received": 50, "Warnings": -40}', '2026-09-28 15:30:00+00'),

    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 1500, 1550, 50,
     '{"posts": 600, "comments": 400, "likes_received": 500, "Warnings": -50}', '2026-10-02 12:00:00+00'),

    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 750, 800, 50,
     '{"posts": 300, "comments": 200, "likes_received": 250, "Warnings": -50}', '2026-10-01 08:00:00+00');

-- =============================================================================
-- ESCALATIONS
-- =============================================================================

INSERT INTO escalations (id, community_id, reporter_id, target_member_id, target_content_id, category, priority, status, subject, description, assigned_to, due_at, metadata)
VALUES
    ('20eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', NULL,
     'harassment', 'medium', 'investigating',
     'Harassment complaint against David Wilson',
     'David has been making inappropriate comments towards other members. Multiple complaints have been received.',
     'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '2026-10-05 00:00:00+00',
     '{"complaint_count": 3, "witnesses": ["c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"]}'),

    ('20eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', NULL, 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21',
     'spam', 'low', 'open',
     'Spam content detected',
     'A post has been flagged as potential spam. It contains multiple external links and promotional content.',
     NULL, '2026-10-04 00:00:00+00',
     '{"flagged_by": "auto_moderation", "confidence": 0.85}');

-- =============================================================================
-- COMPLIANCE REPORTS
-- =============================================================================

INSERT INTO compliance_reports (id, community_id, reporter_id, report_type, status, subject, description, evidence_urls, metadata, external_ref, reviewed_at)
VALUES
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'gdpr_access', 'pending',
     'GDPR Data Access Request',
     'User requests access to all personal data stored in the community platform.',
     '[]', '{"request_date": "2026-10-01", "user_email": "user@example.com"}', 'GDPR-2026-001', NULL),

    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', NULL, 'dmca', 'in_review',
     'DMCA Takedown Notice',
     'Copyright infringement claim regarding content posted in the community.',
     '["https://example.com/evidence1.pdf", "https://example.com/evidence2.pdf"]',
     '{"claimant": "Copyright Holder Inc", "original_work": "https://original-work.com"}', 'DMCA-2026-042',
     '2026-10-02 10:00:00+00');

-- =============================================================================
-- ANALYTICS EVENTS
-- =============================================================================

INSERT INTO analytics_events (id, community_id, user_id, session_id, event_type, event_data, ip_address, user_agent, page_url, created_at)
VALUES
    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'sess_abc123', 'page_view',
     '{"page": "/community/tech-innovators", "referrer": "https://google.com"}', '192.168.1.100', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '/community/tech-innovators', '2026-10-01 14:30:00+00'),

    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'sess_abc123', 'content_view',
     '{"content_id": "e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12", "content_type": "post"}', '192.168.1.100', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '/community/tech-innovators/post/ai-future', '2026-10-01 14:31:00+00'),

    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'sess_abc123', 'content_like',
     '{"content_id": "e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"}', '192.168.1.100', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '/community/tech-innovators/post/ai-future', '2026-10-01 14:32:00+00'),

    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'sess_def456', 'page_view',
     '{"page": "/community/tech-innovators", "referrer": "https://twitter.com"}', '192.168.1.101', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '/community/tech-innovators', '2026-10-02 11:00:00+00'),

    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'sess_def456', 'search_query',
     '{"query": "AI development", "results_count": 15}', '192.168.1.101', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '/community/tech-innovators/search', '2026-10-02 11:01:00+00'),

    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'sess_ghi789', 'page_view',
     '{"page": "/community/creative-writers", "referrer": "https://google.com"}', '192.168.1.102', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '/community/creative-writers', '2026-10-02 10:00:00+00'),

    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'sess_jkl012', 'page_view',
     '{"page": "/community/crypto-traders", "referrer": "https://google.com"}', '192.168.1.103', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '/community/crypto-traders', '2026-10-01 08:00:00+00'),

    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'sess_jkl012', 'content_view',
     '{"content_id": "e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31", "content_type": "post"}', '192.168.1.103', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '/community/crypto-traders/post/btc-analysis', '2026-10-01 08:01:00+00');

-- =============================================================================
-- UPDATE COMMUNITY COUNTERS
-- =============================================================================

UPDATE communities SET member_count = (
    SELECT COUNT(*) FROM members WHERE community_id = communities.id AND deleted_at IS NULL
);

UPDATE communities SET content_count = (
    SELECT COUNT(*) FROM content WHERE community_id = communities.id AND deleted_at IS NULL
);

UPDATE tiers SET subscriber_count = (
    SELECT COUNT(*) FROM members WHERE tier_id = tiers.id AND deleted_at IS NULL
);

COMMIT;
