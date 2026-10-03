"""Tests for Alembic migrations.

Tests cover:
- Upgrade from base to head
- Downgrade from head to base
- Schema consistency with models
- Individual migration validation
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/gated_communities"
ALEMBIC_INI = "migrations/alembic.ini"


@pytest.fixture(scope="module")
def engine():
    """Create a database engine for testing."""
    eng = create_engine(DATABASE_URL)
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def alembic_config():
    """Create Alembic configuration."""
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    return cfg


class TestUpgrade:
    """Test alembic upgrade head."""

    def test_upgrade_head(self, alembic_config):
        """Test that upgrade head runs without errors."""
        command.upgrade(alembic_config, "head")

    def test_alembic_version_table_exists(self, engine):
        """Test that alembic_version table is created after upgrade."""
        inspector = inspect(engine)
        assert "alembic_version" in inspector.get_table_names()

    def test_alembic_version_is_head(self, engine):
        """Test that the current version is at head."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            assert version == "0001_initial_schema"


class TestDowngrade:
    """Test alembic downgrade base."""

    def test_downgrade_base(self, alembic_config):
        """Test that downgrade base runs without errors."""
        command.downgrade(alembic_config, "base")

    def test_all_tables_dropped(self, engine):
        """Test that all tables are dropped after downgrade."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = [
            "communities",
            "tiers",
            "members",
            "content",
            "moderation_actions",
            "reputation_scores",
            "escalations",
            "compliance_reports",
            "analytics_events",
            "audit_log",
        ]
        for table in expected_tables:
            assert table not in tables, f"Table {table} should be dropped"

    def test_all_types_dropped(self, engine):
        """Test that all enum types are dropped after downgrade."""
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT typname FROM pg_type WHERE typtype = 'e'")
            )
            types = {row[0] for row in result}
            expected_types = {
                "community_visibility",
                "community_status",
                "tier_billing_period",
                "member_role",
                "member_status",
                "content_type",
                "content_status",
                "moderation_action_type",
                "moderation_action_status",
                "escalation_priority",
                "escalation_status",
                "escalation_category",
                "compliance_report_type",
                "compliance_report_status",
                "analytics_event_type",
                "audit_action",
            }
            for t in expected_types:
                assert t not in types, f"Type {t} should be dropped"


class TestSchemaConsistency:
    """Test that the schema matches expected models."""

    def test_communities_table_exists(self, engine):
        """Test communities table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("communities")}
        expected = {
            "id",
            "slug",
            "name",
            "description",
            "avatar_url",
            "banner_url",
            "visibility",
            "status",
            "settings",
            "metadata",
            "member_count",
            "content_count",
            "created_by",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert expected.issubset(columns)

    def test_tiers_table_exists(self, engine):
        """Test tiers table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("tiers")}
        expected = {
            "id",
            "community_id",
            "slug",
            "name",
            "description",
            "price_cents",
            "currency",
            "billing_period",
            "is_public",
            "is_active",
            "sort_order",
            "benefits",
            "metadata",
            "subscriber_count",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert expected.issubset(columns)

    def test_members_table_exists(self, engine):
        """Test members table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("members")}
        expected = {
            "id",
            "community_id",
            "user_id",
            "tier_id",
            "role",
            "status",
            "display_name",
            "bio",
            "avatar_url",
            "joined_at",
            "invited_at",
            "banned_at",
            "banned_reason",
            "tier_expires_at",
            "last_active_at",
            "notification_prefs",
            "metadata",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert expected.issubset(columns)

    def test_content_table_exists(self, engine):
        """Test content table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("content")}
        expected = {
            "id",
            "community_id",
            "author_id",
            "parent_id",
            "content_type",
            "status",
            "title",
            "body",
            "body_rendered",
            "media_urls",
            "tags",
            "metadata",
            "like_count",
            "comment_count",
            "share_count",
            "view_count",
            "is_pinned",
            "is_locked",
            "published_at",
            "edited_at",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert expected.issubset(columns)

    def test_moderation_actions_table_exists(self, engine):
        """Test moderation_actions table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("moderation_actions")}
        expected = {
            "id",
            "community_id",
            "target_member_id",
            "target_content_id",
            "action_type",
            "status",
            "reason",
            "details",
            "duration_hours",
            "expires_at",
            "applied_by",
            "applied_at",
            "reversed_by",
            "reversed_at",
            "reversal_reason",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(columns)

    def test_reputation_scores_table_exists(self, engine):
        """Test reputation_scores table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("reputation_scores")}
        expected = {
            "id",
            "community_id",
            "member_id",
            "score",
            "total_earned",
            "total_deducted",
            "breakdown",
            "last_event_at",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(columns)

    def test_escalations_table_exists(self, engine):
        """Test escalations table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("escalations")}
        expected = {
            "id",
            "community_id",
            "reporter_id",
            "target_member_id",
            "target_content_id",
            "category",
            "priority",
            "status",
            "subject",
            "description",
            "resolution_notes",
            "assigned_to",
            "resolved_by",
            "resolved_at",
            "due_at",
            "metadata",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert expected.issubset(columns)

    def test_compliance_reports_table_exists(self, engine):
        """Test compliance_reports table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("compliance_reports")}
        expected = {
            "id",
            "community_id",
            "reporter_id",
            "report_type",
            "status",
            "subject",
            "description",
            "evidence_urls",
            "metadata",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "external_ref",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert expected.issubset(columns)

    def test_audit_log_table_exists(self, engine):
        """Test audit_log table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("audit_log")}
        expected = {
            "id",
            "table_name",
            "record_id",
            "action",
            "old_data",
            "new_data",
            "changed_fields",
            "performed_by",
            "performed_by_type",
            "ip_address",
            "user_agent",
            "session_id",
            "request_id",
            "created_at",
        }
        assert expected.issubset(columns)

    def test_analytics_events_table_exists(self, engine):
        """Test analytics_events table has correct columns."""
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("analytics_events")}
        expected = {
            "id",
            "community_id",
            "user_id",
            "session_id",
            "event_type",
            "event_data",
            "ip_address",
            "user_agent",
            "referrer_url",
            "page_url",
            "created_at",
        }
        assert expected.issubset(columns)

    def test_foreign_keys_exist(self, engine):
        """Test that all foreign keys are created."""
        inspector = inspect(engine)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tc.constraint_name, tc.table_name, kcu.column_name,
                       ccu.table_name AS foreign_table_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
            """))
            fks = {(row[1], row[2]) for row in result}
            expected_fks = {
                ("tiers", "community_id"),
                ("members", "community_id"),
                ("members", "tier_id"),
                ("content", "community_id"),
                ("content", "author_id"),
                ("content", "parent_id"),
                ("moderation_actions", "community_id"),
                ("moderation_actions", "target_member_id"),
                ("moderation_actions", "target_content_id"),
                ("moderation_actions", "applied_by"),
                ("moderation_actions", "reversed_by"),
                ("reputation_scores", "community_id"),
                ("reputation_scores", "member_id"),
                ("escalations", "community_id"),
                ("escalations", "reporter_id"),
                ("escalations", "target_member_id"),
                ("escalations", "target_content_id"),
                ("escalations", "assigned_to"),
                ("escalations", "resolved_by"),
                ("compliance_reports", "community_id"),
                ("compliance_reports", "reporter_id"),
                ("compliance_reports", "reviewed_by"),
            }
            assert expected_fks.issubset(fks)

    def test_indexes_exist(self, engine):
        """Test that all indexes are created."""
        inspector = inspect(engine)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename, indexname FROM pg_indexes
                WHERE schemaname = 'public'
            """))
            indexes = {(row[0], row[1]) for row in result}
            expected_indexes = {
                ("communities", "idx_communities_slug"),
                ("communities", "idx_communities_visibility"),
                ("communities", "idx_communities_status"),
                ("communities", "idx_communities_created_by"),
                ("tiers", "idx_tiers_community_id"),
                ("members", "idx_members_community_id"),
                ("members", "idx_members_user_id"),
                ("content", "idx_content_community_id"),
                ("content", "idx_content_author_id"),
                ("moderation_actions", "idx_moderation_community_id"),
                ("reputation_scores", "idx_reputation_community_id"),
                ("escalations", "idx_escalations_community_id"),
                ("compliance_reports", "idx_compliance_community_id"),
                ("audit_log", "idx_audit_table_name"),
                ("analytics_events", "idx_analytics_community_id"),
            }
            assert expected_indexes.issubset(indexes)

    def test_enum_types_exist(self, engine):
        """Test that all enum types are created."""
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT typname FROM pg_type WHERE typtype = 'e'")
            )
            types = {row[0] for row in result}
            expected_types = {
                "community_visibility",
                "community_status",
                "tier_billing_period",
                "member_role",
                "member_status",
                "content_type",
                "content_status",
                "moderation_action_type",
                "moderation_action_status",
                "escalation_priority",
                "escalation_status",
                "escalation_category",
                "compliance_report_type",
                "compliance_report_status",
                "analytics_event_type",
                "audit_action",
            }
            assert expected_types.issubset(types)

    def test_extensions_enabled(self, engine):
        """Test that required extensions are enabled."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT extname FROM pg_extension"))
            extensions = {row[0] for row in result}
            expected = {"pgcrypto", "uuid-ossp", "pg_trgm", "btree_gin"}
            assert expected.issubset(extensions)

    def test_views_exist(self, engine):
        """Test that views are created."""
        inspector = inspect(engine)
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT viewname FROM pg_views WHERE schemaname = 'public'")
            )
            views = {row[0] for row in result}
            expected = {"v_community_summary", "v_member_detail", "v_content_detail"}
            assert expected.issubset(views)

    def test_triggers_exist(self, engine):
        """Test that triggers are created."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT trigger_name FROM information_schema.triggers
                WHERE trigger_schema = 'public'
            """))
            triggers = {row[0] for row in result}
            expected_triggers = {
                "trg_communities_updated_at",
                "trg_tiers_updated_at",
                "trg_members_updated_at",
                "trg_content_updated_at",
                "trg_moderation_actions_updated_at",
                "trg_reputation_scores_updated_at",
                "trg_escalations_updated_at",
                "trg_compliance_reports_updated_at",
                "trg_audit_communities",
                "trg_audit_members",
                "trg_audit_content",
                "trg_audit_moderation_actions",
                "trg_audit_escalations",
                "trg_audit_compliance_reports",
            }
            assert expected_triggers.issubset(triggers)

    def test_functions_exist(self, engine):
        """Test that functions are created."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT routine_name FROM information_schema.routines
                WHERE routine_schema = 'public'
            """))
            functions = {row[0] for row in result}
            expected = {"update_updated_at_column", "audit_trigger_func"}
            assert expected.issubset(functions)

    def test_unique_constraints_exist(self, engine):
        """Test that unique constraints are created."""
        inspector = inspect(engine)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tc.constraint_name, tc.table_name
                FROM information_schema.table_constraints tc
                WHERE tc.constraint_type = 'UNIQUE' AND tc.table_schema = 'public'
            """))
            constraints = {(row[1], row[0]) for row in result}
            expected = {
                ("communities", "uq_communities_slug"),
                ("tiers", "uq_tiers_community_slug"),
                ("members", "uq_members_community_user"),
                ("reputation_scores", "uq_reputation_community_member"),
            }
            assert expected.issubset(constraints)

    def test_check_constraints_exist(self, engine):
        """Test that check constraints are created."""
        inspector = inspect(engine)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT conname FROM pg_constraint
                WHERE contype = 'c' AND connamespace = 'public'::regnamespace
            """))
            constraints = {row[0] for row in result}
            expected = {
                "chk_communities_name_not_empty",
                "chk_communities_member_count",
                "chk_communities_content_count",
                "chk_tiers_name_not_empty",
                "chk_tiers_price_cents",
                "chk_tiers_subscriber_count",
                "chk_members_display_name",
                "chk_content_title",
                "chk_content_like_count",
                "chk_content_comment_count",
                "chk_content_share_count",
                "chk_content_view_count",
                "chk_moderation_reason_not_empty",
                "chk_moderation_duration_hours",
                "chk_reputation_total_earned",
                "chk_reputation_total_deducted",
                "chk_escalations_subject_not_empty",
                "chk_escalations_description_not_empty",
                "chk_compliance_subject_not_empty",
                "chk_compliance_description_not_empty",
            }
            assert expected.issubset(constraints)


class TestMigrationValidation:
    """Test migration file validation."""

    def test_migration_file_exists(self):
        """Test that migration file exists."""
        import os

        migration_path = "migrations/versions/0001_initial_schema.py"
        assert os.path.exists(migration_path)

    def test_migration_has_revision_id(self):
        """Test that migration has correct revision ID."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "migration", "migrations/versions/0001_initial_schema.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.revision == "0001_initial_schema"

    def test_migration_has_down_revision(self):
        """Test that migration has correct down_revision."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "migration", "migrations/versions/0001_initial_schema.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.down_revision is None

    def test_migration_has_upgrade_function(self):
        """Test that migration has upgrade function."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "migration", "migrations/versions/0001_initial_schema.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "upgrade")
        assert callable(mod.upgrade)

    def test_migration_has_downgrade_function(self):
        """Test that migration has downgrade function."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "migration", "migrations/versions/0001_initial_schema.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "downgrade")
        assert callable(mod.downgrade)

    def test_migration_creates_all_tables(self):
        """Test that migration creates all expected tables."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "migration", "migrations/versions/0001_initial_schema.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Check that upgrade function references all tables
        import inspect

        source = inspect.getsource(mod.upgrade)
        expected_tables = [
            "communities",
            "tiers",
            "members",
            "content",
            "moderation_actions",
            "reputation_scores",
            "escalations",
            "compliance_reports",
            "analytics_events",
            "audit_log",
        ]
        for table in expected_tables:
            assert (
                f"'{table}'" in source or f'"{table}"' in source
            ), f"Table {table} not found in migration"

    def test_migration_drops_all_tables(self):
        """Test that migration drops all expected tables in downgrade."""
        import importlib.util
        import inspect

        spec = importlib.util.spec_from_file_location(
            "migration", "migrations/versions/0001_initial_schema.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        source = inspect.getsource(mod.downgrade)
        expected_tables = [
            "communities",
            "tiers",
            "members",
            "content",
            "moderation_actions",
            "reputation_scores",
            "escalations",
            "compliance_reports",
            "analytics_events",
            "audit_log",
        ]
        for table in expected_tables:
            assert (
                f"'{table}'" in source or f'"{table}"' in source
            ), f"Table {table} not found in downgrade migration"
