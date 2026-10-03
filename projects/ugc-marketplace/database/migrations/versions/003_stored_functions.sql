-- =============================================================================
-- Stored Procedures / Functions for UGC Marketplace
-- Complex operations that benefit from server-side execution
-- =============================================================================

-- 1. Process a refund: update transaction, reverse earnings, deactivate license
CREATE OR REPLACE FUNCTION fn_process_refund(p_transaction_id UUID, p_reason TEXT)
RETURNS TABLE (
    transaction_id UUID,
    refunded_amount NUMERIC,
    seller_adjusted NUMERIC
) AS $$
DECLARE
    v_seller_id UUID;
    v_seller_earnings NUMERIC;
    v_listing_id UUID;
BEGIN
    -- Lock the transaction row
    SELECT t.seller_id, t.seller_earnings, t.listing_id
    INTO v_seller_id, v_seller_earnings, v_listing_id
    FROM transactions t
    WHERE t.id = p_transaction_id AND t.payment_status = 'completed'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transaction % not found or not completed', p_transaction_id;
    END IF;

    -- Update transaction status
    UPDATE transactions
    SET payment_status = 'refunded',
        updated_at = now(),
        metadata = metadata || jsonb_build_object('refund_reason', p_reason, 'refunded_at', now())
    WHERE id = p_transaction_id;

    -- Reverse seller earnings
    UPDATE creators
    SET total_earnings = total_earnings - v_seller_earnings,
        total_sales = total_sales - 1
    WHERE id = v_seller_id;

    -- Decrement listing sales count
    UPDATE listings
    SET sales_count = GREATEST(sales_count - 1, 0)
    WHERE id = v_listing_id;

    -- Deactivate associated licenses
    UPDATE licenses
    SET is_active = false, updated_at = now()
    WHERE transaction_id = p_transaction_id AND is_active = true;

    RETURN QUERY SELECT p_transaction_id, v_seller_earnings, v_seller_earnings;
END;
$$ LANGUAGE plpgsql;

-- 2. Search content with ranking and pagination
CREATE OR REPLACE FUNCTION fn_search_content(
    p_query TEXT,
    p_content_type VARCHAR(50) DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(255),
    content_type VARCHAR(50),
    creator_username VARCHAR(50),
    quality_score NUMERIC,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ct.id,
        ct.title,
        ct.content_type,
        c.username,
        qs.overall_score,
        ts_rank(ct.search_vector, plainto_tsquery('english', p_query)) AS rank
    FROM content ct
    JOIN creators c ON c.id = ct.creator_id
    LEFT JOIN quality_scores qs ON qs.content_id = ct.id
    WHERE ct.status = 'published'
      AND ct.is_nsfw = false
      AND ct.search_vector @@ plainto_tsquery('english', p_query)
      AND (p_content_type IS NULL OR ct.content_type = p_content_type)
    ORDER BY rank DESC, ct.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 3. Get creator dashboard stats
CREATE OR REPLACE FUNCTION fn_creator_dashboard(p_creator_id UUID)
RETURNS TABLE (
    total_earnings NUMERIC,
    total_sales INTEGER,
    active_listings INTEGER,
    published_content INTEGER,
    avg_quality_score NUMERIC,
    open_reports INTEGER,
    recent_transactions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.total_earnings,
        c.total_sales,
        (SELECT COUNT(*) FROM listings l WHERE l.creator_id = p_creator_id AND l.is_active = true)::INTEGER,
        (SELECT COUNT(*) FROM content ct WHERE ct.creator_id = p_creator_id AND ct.status = 'published')::INTEGER,
        (SELECT ROUND(AVG(qs.overall_score), 3) FROM quality_scores qs
         JOIN content ct ON ct.id = qs.content_id WHERE ct.creator_id = p_creator_id),
        (SELECT COUNT(*) FROM fraud_reports fr WHERE fr.reported_user_id = p_creator_id AND fr.status = 'open')::INTEGER,
        (SELECT COALESCE(jsonb_agg(t ORDER BY t.created_at DESC), '[]'::jsonb)
         FROM (
             SELECT t.id, t.amount, t.payment_status, t.created_at, l.title AS listing_title
             FROM transactions t
             JOIN listings l ON l.id = t.listing_id
             WHERE t.seller_id = p_creator_id
             ORDER BY t.created_at DESC
             LIMIT 5
         ) t)
    FROM creators c
    WHERE c.id = p_creator_id;
END;
$$ LANGUAGE plpgsql;

-- 4. Bulk update content status with audit logging
CREATE OR REPLACE FUNCTION fn_bulk_update_content_status(
    p_content_ids UUID[],
    p_new_status VARCHAR(20),
    p_moderator_id UUID
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE content
    SET status = p_new_status, updated_at = now()
    WHERE id = ANY(p_content_ids)
      AND status != p_new_status;

    GET DIAGNOSTICS v_count = ROW_COUNT;

    -- Log moderation action
    INSERT INTO moderation_actions (content_id, moderator_id, action_type, reason)
    SELECT unnest(p_content_ids), p_moderator_id,
           CASE p_new_status
               WHEN 'published' THEN 'approve'
               WHEN 'archived' THEN 'remove'
               ELSE 'flag'
           END,
           'Bulk status update to ' || p_new_status;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- 5. Refresh all materialized views (call from scheduled job)
CREATE OR REPLACE FUNCTION fn_refresh_materialized_views()
RETURNS TABLE (view_name TEXT, refreshed_at TIMESTAMPTZ) AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_creator_leaderboard;
    RETURN QUERY SELECT 'mv_creator_leaderboard'::TEXT, now();

    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_content_performance;
    RETURN QUERY SELECT 'mv_content_performance'::TEXT, now();

    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales;
    RETURN QUERY SELECT 'mv_daily_sales'::TEXT, now();

    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_license_status;
    RETURN QUERY SELECT 'mv_license_status'::TEXT, now();

    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_moderation_queue;
    RETURN QUERY SELECT 'mv_moderation_queue'::TEXT, now();
END;
$$ LANGUAGE plpgsql;
