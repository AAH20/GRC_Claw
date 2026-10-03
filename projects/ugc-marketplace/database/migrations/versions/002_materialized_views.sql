-- =============================================================================
-- Materialized Views for UGC Marketplace
-- Pre-computed aggregations for common read-heavy queries.
-- Refresh strategy: REFRESH MATERIALIZED VIEW CONCURRENTLY (requires unique index)
-- =============================================================================

-- 1. Creator Leaderboard: top creators ranked by earnings, sales, and reputation
CREATE MATERIALIZED VIEW mv_creator_leaderboard AS
SELECT
    c.id,
    c.username,
    c.display_name,
    c.avatar_url,
    c.verification_status,
    c.reputation_score,
    c.total_earnings,
    c.total_sales,
    COUNT(DISTINCT ct.id) FILTER (WHERE ct.status = 'published') AS published_content_count,
    COUNT(DISTINCT l.id) FILTER (WHERE l.is_active = true)       AS active_listing_count,
    RANK() OVER (ORDER BY c.total_earnings DESC)                  AS earnings_rank,
    RANK() OVER (ORDER BY c.reputation_score DESC)                AS reputation_rank
FROM creators c
LEFT JOIN content ct  ON ct.creator_id = c.id
LEFT JOIN listings l ON l.creator_id = c.id
WHERE c.is_active = true
GROUP BY c.id;

CREATE UNIQUE INDEX idx_mv_creator_leaderboard_id ON mv_creator_leaderboard (id);
CREATE INDEX idx_mv_creator_leaderboard_earnings ON mv_creator_leaderboard (earnings_rank);
CREATE INDEX idx_mv_creator_leaderboard_reputation ON mv_creator_leaderboard (reputation_rank);

-- 2. Content Performance: aggregated engagement metrics per content item
CREATE MATERIALIZED VIEW mv_content_performance AS
SELECT
    ct.id,
    ct.title,
    ct.content_type,
    ct.status,
    ct.creator_id,
    c.username AS creator_username,
    ct.view_count,
    ct.like_count,
    ROUND(ct.like_count::NUMERIC / NULLIF(ct.view_count, 0), 4) AS engagement_rate,
    COUNT(DISTINCT l.id)              AS listing_count,
    COALESCE(SUM(l.sales_count), 0)   AS total_sales,
    qs.overall_score                  AS quality_score,
    ct.created_at
FROM content ct
JOIN creators c       ON c.id = ct.creator_id
LEFT JOIN listings l  ON l.content_id = ct.id
LEFT JOIN quality_scores qs ON qs.content_id = ct.id
GROUP BY ct.id, c.username, qs.overall_score;

CREATE UNIQUE INDEX idx_mv_content_performance_id ON mv_content_performance (id);
CREATE INDEX idx_mv_content_performance_engagement ON mv_content_performance (engagement_rate DESC);
CREATE INDEX idx_mv_content_performance_quality ON mv_content_performance (quality_score DESC);

-- 3. Daily Sales Summary: transaction aggregates per day
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT
    DATE_TRUNC('day', t.created_at) AS sale_date,
    COUNT(*)                        AS transaction_count,
    SUM(t.amount)                   AS total_amount,
    SUM(t.platform_fee)             AS total_fees,
    SUM(t.seller_earnings)          AS total_seller_earnings,
    COUNT(DISTINCT t.seller_id)     AS unique_sellers,
    COUNT(DISTINCT t.buyer_id)      AS unique_buyers,
    t.currency
FROM transactions t
WHERE t.payment_status = 'completed'
GROUP BY DATE_TRUNC('day', t.created_at), t.currency;

CREATE UNIQUE INDEX idx_mv_daily_sales_date_currency ON mv_daily_sales (sale_date, currency);
CREATE INDEX idx_mv_daily_sales_date ON mv_daily_sales (sale_date DESC);

-- 4. License Status Overview: active, expiring soon, and expired licenses
CREATE MATERIALIZED VIEW mv_license_status AS
SELECT
    l.id,
    l.license_type,
    l.valid_from,
    l.valid_until,
    l.is_active,
    CASE
        WHEN l.valid_until IS NULL THEN 'perpetual'
        WHEN l.valid_until < now() THEN 'expired'
        WHEN l.valid_until < now() + INTERVAL '30 days' THEN 'expiring_soon'
        ELSE 'active'
    END AS status_category,
    c.title AS content_title,
    creator.username AS licensor_username,
    licensee.username AS licensee_username
FROM licenses l
JOIN content c      ON c.id = l.content_id
JOIN creators creator ON creator.id = l.licensor_id
JOIN creators licensee ON licensee.id = l.licensee_id;

CREATE UNIQUE INDEX idx_mv_license_status_id ON mv_license_status (id);
CREATE INDEX idx_mv_license_status_category ON mv_license_status (status_category);
CREATE INDEX idx_mv_license_status_expiry ON mv_license_status (valid_until);

-- 5. Moderation Queue: items flagged or reported needing review
CREATE MATERIALIZED VIEW mv_moderation_queue AS
SELECT
    fr.id,
    fr.report_type,
    fr.status,
    fr.description,
    fr.created_at,
    reporter.username AS reporter_username,
    reported_user.username AS reported_username,
    ct.title AS content_title,
    l.title AS listing_title,
    ma.action_type AS last_moderation_action,
    ma.created_at AS last_action_at
FROM fraud_reports fr
JOIN creators reporter ON reporter.id = fr.reporter_id
LEFT JOIN creators reported_user ON reported_user.id = fr.reported_user_id
LEFT JOIN content ct ON ct.id = fr.reported_content_id
LEFT JOIN listings l ON l.id = fr.reported_listing_id
LEFT JOIN LATERAL (
    SELECT action_type, created_at
    FROM moderation_actions ma
    WHERE ma.content_id = fr.reported_content_id OR ma.listing_id = fr.reported_listing_id
    ORDER BY created_at DESC
    LIMIT 1
) ma ON true
WHERE fr.status IN ('open', 'investigating', 'escalated');

CREATE UNIQUE INDEX idx_mv_moderation_queue_id ON mv_moderation_queue (id);
CREATE INDEX idx_mv_moderation_queue_status ON mv_moderation_queue (status);
CREATE INDEX idx_mv_moderation_queue_created ON mv_moderation_queue (created_at DESC);
