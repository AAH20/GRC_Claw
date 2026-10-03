-- =============================================================================
-- Additional Audit Triggers for UGC Marketplace
-- Extends audit coverage to licenses, moderation_actions, quality_scores,
-- and fraud_reports tables. Also enhances the audit function to capture
-- the current user from a session variable.
-- =============================================================================

-- Enhanced audit function: captures changed_by from app.current_user_id session var
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_by UUID;
BEGIN
    BEGIN
        v_changed_by := current_setting('app.current_user_id', true)::UUID;
    EXCEPTION WHEN OTHERS THEN
        v_changed_by := NULL;
    END;

    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, changed_by)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), v_changed_by);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), v_changed_by);
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (table_name, record_id, action, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), v_changed_by);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Audit trigger for licenses
CREATE TRIGGER trg_audit_licenses
    AFTER INSERT OR UPDATE OR DELETE ON licenses
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Audit trigger for moderation_actions
CREATE TRIGGER trg_audit_moderation_actions
    AFTER INSERT OR UPDATE OR DELETE ON moderation_actions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Audit trigger for quality_scores
CREATE TRIGGER trg_audit_quality_scores
    AFTER INSERT OR UPDATE OR DELETE ON quality_scores
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Audit trigger for fraud_reports
CREATE TRIGGER trg_audit_fraud_reports
    AFTER INSERT OR UPDATE OR DELETE ON fraud_reports
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Trigger to prevent self-transactions at database level (defense in depth)
CREATE OR REPLACE FUNCTION fn_prevent_self_transaction()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.buyer_id = NEW.seller_id THEN
        RAISE EXCEPTION 'Buyer and seller cannot be the same user';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_self_transaction
    BEFORE INSERT OR UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION fn_prevent_self_transaction();

-- Trigger to auto-update listing sales_count when a transaction is completed
CREATE OR REPLACE FUNCTION fn_increment_listing_sales()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.payment_status = 'completed' AND (OLD IS NULL OR OLD.payment_status != 'completed') THEN
        UPDATE listings SET sales_count = sales_count + 1 WHERE id = NEW.listing_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_increment_listing_sales
    AFTER INSERT OR UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION fn_increment_listing_sales();

-- Trigger to auto-update creator total_earnings and total_sales on completed transaction
CREATE OR REPLACE FUNCTION fn_update_creator_earnings()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.payment_status = 'completed' AND (OLD IS NULL OR OLD.payment_status != 'completed') THEN
        UPDATE creators
        SET total_earnings = total_earnings + NEW.seller_earnings,
            total_sales = total_sales + 1
        WHERE id = NEW.seller_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_creator_earnings
    AFTER INSERT OR UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION fn_update_creator_earnings();
