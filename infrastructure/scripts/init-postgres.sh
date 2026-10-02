#!/usr/bin/env bash
# =============================================================================
# GRC Claw — PostgreSQL Initialization Script
# =============================================================================
# Sets up extensions, roles, and initial data for the GRC Claw database.
# This script runs after PostgreSQL is initialized with the base schema.
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

readonly DB_NAME="${POSTGRES_DB:-grc_claw}"
readonly DB_USER="${POSTGRES_USER:-grc_admin}"
readonly LOG_PREFIX="[init-postgres]"

# =============================================================================
# Logging Functions
# =============================================================================

log_info() {
    echo "${LOG_PREFIX} [INFO] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*"
}

log_warn() {
    echo "${LOG_PREFIX} [WARN] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*" >&2
}

log_error() {
    echo "${LOG_PREFIX} [ERROR] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*" >&2
}

# =============================================================================
# Utility Functions
# =============================================================================

check_postgres_available() {
    local max_attempts=30
    local attempt=1

    log_info "Waiting for PostgreSQL to be available..."

    while [[ ${attempt} -le ${max_attempts} ]]; do
        if pg_isready -U "${DB_USER}" -d "${DB_NAME}" &>/dev/null; then
            log_info "PostgreSQL is available."
            return 0
        fi
        log_warn "Attempt ${attempt}/${max_attempts}: PostgreSQL not ready. Retrying in 2s..."
        sleep 2
        ((attempt++))
    done

    log_error "PostgreSQL did not become available after ${max_attempts} attempts."
    return 1
}

execute_sql() {
    local sql="$1"
    local description="${2:-SQL execution}"

    log_info "Executing: ${description}"
    psql -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -c "${sql}"
}

# =============================================================================
# Initialization Steps
# =============================================================================

install_extensions() {
    log_info "Installing PostgreSQL extensions..."

    execute_sql "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" "uuid-ossp extension"
    execute_sql "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";" "pgcrypto extension"
    execute_sql "CREATE EXTENSION IF NOT EXISTS \"pg_stat_statements\";" "pg_stat_statements extension"
    execute_sql "CREATE EXTENSION IF NOT EXISTS \"citext\";" "citext extension"
    execute_sql "CREATE EXTENSION IF NOT EXISTS \"btree_gin\";" "btree_gin extension"
    execute_sql "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";" "pg_trgm extension"
}

create_roles() {
    log_info "Creating application roles..."

    execute_sql "
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grc_app_read') THEN
                CREATE ROLE grc_app_read LOGIN PASSWORD 'grc_read_only';
            END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grc_app_write') THEN
                CREATE ROLE grc_app_write LOGIN PASSWORD 'grc_read_write';
            END IF;
        END
        \$\$;
    " "Application roles"
}

grant_permissions() {
    log_info "Granting permissions to application roles..."

    execute_sql "
        GRANT USAGE ON SCHEMA grc_claw TO grc_app_read, grc_app_write;
        GRANT USAGE ON SCHEMA analytics TO grc_app_read, grc_app_write;
        GRANT SELECT ON ALL TABLES IN SCHEMA grc_claw TO grc_app_read;
        GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO grc_app_read;
        GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA grc_claw TO grc_app_write;
        GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO grc_app_write;
        ALTER DEFAULT PRIVILEGES IN SCHEMA grc_claw GRANT SELECT ON TABLES TO grc_app_read;
        ALTER DEFAULT PRIVILEGES IN SCHEMA grc_claw GRANT SELECT, INSERT, UPDATE ON TABLES TO grc_app_write;
    " "Role permissions"
}

create_partition_maintenance_function() {
    log_info "Creating partition maintenance function..."

    execute_sql "
        CREATE OR REPLACE FUNCTION grc_claw.create_monthly_partition(
            p_table_name TEXT,
            p_year INT,
            p_month INT
        ) RETURNS TEXT AS \$\$
        DECLARE
            partition_name TEXT;
            start_date DATE;
            end_date DATE;
            create_sql TEXT;
        BEGIN
            partition_name := p_table_name || '_' || p_year || '_' || LPAD(p_month::TEXT, 2, '0');
            start_date := make_date(p_year, p_month, 1);
            end_date := start_date + INTERVAL '1 month';

            create_sql := format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                partition_name,
                p_table_name,
                start_date,
                end_date
            );

            EXECUTE create_sql;
            RETURN partition_name;
        END;
        \$\$ LANGUAGE plpgsql;
    " "Partition maintenance function"
}

create_updated_at_trigger() {
    log_info "Creating updated_at trigger function..."

    execute_sql "
        CREATE OR REPLACE FUNCTION grc_claw.update_updated_at_column()
        RETURNS TRIGGER AS \$\$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        \$\$ LANGUAGE plpgsql;

        DO \$\$
        DECLARE
            t TEXT;
        BEGIN
            FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'grc_claw'
            LOOP
                EXECUTE format(
                    'DROP TRIGGER IF EXISTS trg_updated_at ON grc_claw.%I',
                    t
                );
                EXECUTE format(
                    'CREATE TRIGGER trg_updated_at BEFORE UPDATE ON grc_claw.%I
                     FOR EACH ROW EXECUTE FUNCTION grc_claw.update_updated_at_column()',
                    t
                );
            END LOOP;
        END
        \$\$;
    " "updated_at trigger"
}

create_audit_trigger() {
    log_info "Creating audit trigger function..."

    execute_sql "
        CREATE OR REPLACE FUNCTION audit.log_changes()
        RETURNS TRIGGER AS \$\$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO audit.log (table_name, record_id, action, old_data, performed_by)
                VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), current_user);
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO audit.log (table_name, record_id, action, old_data, new_data, performed_by)
                VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), current_user);
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO audit.log (table_name, record_id, action, new_data, performed_by)
                VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), current_user);
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        \$\$ LANGUAGE plpgsql;
    " "Audit trigger function"
}

seed_initial_data() {
    log_info "Seeding initial data..."

    execute_sql "
        INSERT INTO grc_claw.agents (name, type, status, config)
        VALUES
            ('default-agent', 'marketing', 'active', '{\"version\": \"1.0.0\"}'::jsonb)
        ON CONFLICT DO NOTHING;
    " "Initial agent seed data"
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_info "Starting PostgreSQL initialization..."

    check_postgres_available

    install_extensions
    create_roles
    grant_permissions
    create_partition_maintenance_function
    create_updated_at_trigger
    create_audit_trigger
    seed_initial_data

    log_info "PostgreSQL initialization complete."
}

main "$@"
