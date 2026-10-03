"""Initial schema for UGC Marketplace

Revision ID: 0001
Revises:
Create Date: 2024-12-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Create immutable wrappers for functions used in generated columns.
    # PostgreSQL's to_tsvector(regconfig, text) and array_to_string are STABLE,
    # not IMMUTABLE, so they cannot be used in a generated column directly.
    op.execute("""
        CREATE OR REPLACE FUNCTION immutable_to_tsvector_english(text)
        RETURNS tsvector AS
        $$ SELECT to_tsvector('english'::regconfig, $1) $$
        LANGUAGE sql IMMUTABLE
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION immutable_array_to_string(text[], text)
        RETURNS text AS
        $$ SELECT array_to_string($1, $2) $$
        LANGUAGE sql IMMUTABLE
    """)

    # =========================================================================
    # creators
    # =========================================================================
    op.create_table(
        "creators",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("website_url", sa.Text(), nullable=True),
        sa.Column(
            "social_links",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "verification_status",
            sa.String(length=20),
            server_default="unverified",
            nullable=False,
        ),
        sa.Column(
            "reputation_score",
            sa.Numeric(precision=5, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "total_earnings",
            sa.Numeric(precision=15, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("total_sales", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
        sa.CheckConstraint(
            "verification_status IN ('unverified', 'pending', 'verified', 'suspended')",
            name="creators_verification_check",
        ),
        sa.CheckConstraint(
            "reputation_score >= 0.00 AND reputation_score <= 100.00",
            name="creators_reputation_check",
        ),
        sa.CheckConstraint("total_earnings >= 0.00", name="creators_earnings_check"),
        sa.CheckConstraint("total_sales >= 0", name="creators_sales_check"),
    )
    op.create_index(
        "idx_creators_verification_status", "creators", ["verification_status"]
    )
    op.create_index("idx_creators_is_active", "creators", ["is_active"])
    op.create_index(
        "idx_creators_reputation_score",
        "creators",
        ["reputation_score"],
        postgresql_using="btree",
        postgresql_ops={"reputation_score": "DESC"},
    )
    op.create_index(
        "idx_creators_social_links_gin",
        "creators",
        ["social_links"],
        postgresql_using="gin",
    )

    # =========================================================================
    # content
    # =========================================================================
    op.create_table(
        "content",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column(
            "media_urls",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "tags", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=20), server_default="draft", nullable=False
        ),
        sa.Column(
            "is_nsfw", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("like_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(immutable_to_tsvector_english(coalesce(title, '')), 'A') || "
                "setweight(immutable_to_tsvector_english(coalesce(description, '')), 'B') || "
                "setweight(immutable_to_tsvector_english(coalesce(immutable_array_to_string(tags, ' '), '')), 'C')",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["creators.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived', 'removed')",
            name="content_status_check",
        ),
        sa.CheckConstraint("view_count >= 0", name="content_view_count_check"),
        sa.CheckConstraint("like_count >= 0", name="content_like_count_check"),
    )
    op.create_index("idx_content_creator_id", "content", ["creator_id"])
    op.create_index("idx_content_status", "content", ["status"])
    op.create_index("idx_content_content_type", "content", ["content_type"])
    op.create_index("idx_content_is_nsfw", "content", ["is_nsfw"])
    op.create_index("idx_content_tags_gin", "content", ["tags"], postgresql_using="gin")
    op.create_index(
        "idx_content_metadata_gin", "content", ["metadata"], postgresql_using="gin"
    )
    op.create_index(
        "idx_content_search_vector",
        "content",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_content_created_at",
        "content",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )

    # =========================================================================
    # listings
    # =========================================================================
    op.create_table(
        "listings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), server_default="USD", nullable=False
        ),
        sa.Column("license_type", sa.String(length=50), nullable=False),
        sa.Column(
            "usage_rights",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("sales_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["creators.id"], ondelete="CASCADE"),
        sa.CheckConstraint("price >= 0.00", name="listings_price_check"),
        sa.CheckConstraint("sales_count >= 0", name="listings_sales_check"),
    )
    op.create_index("idx_listings_content_id", "listings", ["content_id"])
    op.create_index("idx_listings_creator_id", "listings", ["creator_id"])
    op.create_index("idx_listings_is_active", "listings", ["is_active"])
    op.create_index("idx_listings_price", "listings", ["price"])
    op.create_index("idx_listings_license_type", "listings", ["license_type"])
    op.create_index(
        "idx_listings_usage_rights_gin",
        "listings",
        ["usage_rights"],
        postgresql_using="gin",
    )

    # =========================================================================
    # transactions
    # =========================================================================
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), server_default="USD", nullable=False
        ),
        sa.Column("platform_fee", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("seller_earnings", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column(
            "payment_status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["buyer_id"], ["creators.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["creators.id"]),
        sa.CheckConstraint("amount >= 0.00", name="transactions_amount_check"),
        sa.CheckConstraint("platform_fee >= 0.00", name="transactions_fee_check"),
        sa.CheckConstraint(
            "seller_earnings >= 0.00", name="transactions_earnings_check"
        ),
        sa.CheckConstraint(
            "payment_status IN ('pending', 'completed', 'failed', 'refunded', 'disputed')",
            name="transactions_status_check",
        ),
        sa.CheckConstraint(
            "buyer_id != seller_id", name="transactions_buyer_seller_check"
        ),
    )
    op.create_index("idx_transactions_listing_id", "transactions", ["listing_id"])
    op.create_index("idx_transactions_buyer_id", "transactions", ["buyer_id"])
    op.create_index("idx_transactions_seller_id", "transactions", ["seller_id"])
    op.create_index("idx_transactions_status", "transactions", ["payment_status"])
    op.create_index(
        "idx_transactions_created_at",
        "transactions",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_transactions_metadata_gin",
        "transactions",
        ["metadata"],
        postgresql_using="gin",
    )

    # =========================================================================
    # licenses
    # =========================================================================
    op.create_table(
        "licenses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("licensee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("licensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_type", sa.String(length=50), nullable=False),
        sa.Column(
            "usage_scope",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["transactions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["licensee_id"], ["creators.id"]),
        sa.ForeignKeyConstraint(["licensor_id"], ["creators.id"]),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"]),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="licenses_validity_check",
        ),
    )
    op.create_index("idx_licenses_transaction_id", "licenses", ["transaction_id"])
    op.create_index("idx_licenses_licensee_id", "licenses", ["licensee_id"])
    op.create_index("idx_licenses_licensor_id", "licenses", ["licensor_id"])
    op.create_index("idx_licenses_content_id", "licenses", ["content_id"])
    op.create_index("idx_licenses_is_active", "licenses", ["is_active"])
    op.create_index("idx_licenses_valid_until", "licenses", ["valid_until"])
    op.create_index(
        "idx_licenses_usage_scope_gin",
        "licenses",
        ["usage_scope"],
        postgresql_using="gin",
    )

    # =========================================================================
    # moderation_actions
    # =========================================================================
    op.create_table(
        "moderation_actions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("moderator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["moderator_id"], ["creators.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "action_type IN ('approve', 'reject', 'flag', 'remove', 'restore', 'warn', 'suspend', 'ban')",
            name="moderation_action_check",
        ),
    )
    op.create_index("idx_moderation_content_id", "moderation_actions", ["content_id"])
    op.create_index("idx_moderation_listing_id", "moderation_actions", ["listing_id"])
    op.create_index(
        "idx_moderation_moderator_id", "moderation_actions", ["moderator_id"]
    )
    op.create_index("idx_moderation_action_type", "moderation_actions", ["action_type"])
    op.create_index(
        "idx_moderation_created_at",
        "moderation_actions",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_moderation_details_gin",
        "moderation_actions",
        ["details"],
        postgresql_using="gin",
    )

    # =========================================================================
    # quality_scores
    # =========================================================================
    op.create_table(
        "quality_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("technical_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("aesthetic_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("engagement_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("originality_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("scoring_model", sa.String(length=100), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "overall_score >= 0.000 AND overall_score <= 1.000",
            name="quality_overall_check",
        ),
        sa.CheckConstraint(
            "technical_score IS NULL OR (technical_score >= 0.000 AND technical_score <= 1.000)",
            name="quality_technical_check",
        ),
        sa.CheckConstraint(
            "aesthetic_score IS NULL OR (aesthetic_score >= 0.000 AND aesthetic_score <= 1.000)",
            name="quality_aesthetic_check",
        ),
        sa.CheckConstraint(
            "engagement_score IS NULL OR (engagement_score >= 0.000 AND engagement_score <= 1.000)",
            name="quality_engagement_check",
        ),
        sa.CheckConstraint(
            "originality_score IS NULL OR (originality_score >= 0.000 AND originality_score <= 1.000)",
            name="quality_originality_check",
        ),
    )
    op.create_index("idx_quality_content_id", "quality_scores", ["content_id"])
    op.create_index(
        "idx_quality_overall_score",
        "quality_scores",
        ["overall_score"],
        postgresql_using="btree",
        postgresql_ops={"overall_score": "DESC"},
    )
    op.create_index("idx_quality_scoring_model", "quality_scores", ["scoring_model"])
    op.create_index(
        "idx_quality_details_gin", "quality_scores", ["details"], postgresql_using="gin"
    )

    # =========================================================================
    # fraud_reports
    # =========================================================================
    op.create_table(
        "fraud_reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reported_content_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reported_listing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reported_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=20), server_default="open", nullable=False
        ),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reporter_id"], ["creators.id"]),
        sa.ForeignKeyConstraint(
            ["reported_content_id"], ["content.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["reported_listing_id"], ["listings.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["reported_user_id"], ["creators.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["resolved_by"], ["creators.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('open', 'investigating', 'resolved', 'dismissed', 'escalated')",
            name="fraud_status_check",
        ),
        sa.CheckConstraint(
            "report_type IN ('copyright', 'fraud', 'spam', 'impersonation', 'prohibited_content', 'other')",
            name="fraud_type_check",
        ),
    )
    op.create_index("idx_fraud_reporter_id", "fraud_reports", ["reporter_id"])
    op.create_index("idx_fraud_content_id", "fraud_reports", ["reported_content_id"])
    op.create_index("idx_fraud_listing_id", "fraud_reports", ["reported_listing_id"])
    op.create_index("idx_fraud_reported_user_id", "fraud_reports", ["reported_user_id"])
    op.create_index("idx_fraud_status", "fraud_reports", ["status"])
    op.create_index("idx_fraud_report_type", "fraud_reports", ["report_type"])
    op.create_index(
        "idx_fraud_created_at",
        "fraud_reports",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_fraud_evidence_gin", "fraud_reports", ["evidence"], postgresql_using="gin"
    )

    # =========================================================================
    # analytics_events (Partitioned)
    # =========================================================================
    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column(
            "event_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", "created_at"),
        sa.ForeignKeyConstraint(["user_id"], ["creators.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="SET NULL"),
        postgresql_partition_by="RANGE (created_at)",
    )
    op.create_index("idx_analytics_event_type", "analytics_events", ["event_type"])
    op.create_index("idx_analytics_user_id", "analytics_events", ["user_id"])
    op.create_index("idx_analytics_content_id", "analytics_events", ["content_id"])
    op.create_index("idx_analytics_listing_id", "analytics_events", ["listing_id"])
    op.create_index(
        "idx_analytics_created_at",
        "analytics_events",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_analytics_event_data_gin",
        "analytics_events",
        ["event_data"],
        postgresql_using="gin",
    )

    # Create partitions
    op.execute("""
        CREATE TABLE analytics_events_2024_q4 PARTITION OF analytics_events
        FOR VALUES FROM ('2024-10-01') TO ('2025-01-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2025_q1 PARTITION OF analytics_events
        FOR VALUES FROM ('2025-01-01') TO ('2025-04-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2025_q2 PARTITION OF analytics_events
        FOR VALUES FROM ('2025-04-01') TO ('2025-07-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_default PARTITION OF analytics_events DEFAULT
    """)

    # =========================================================================
    # audit_log
    # =========================================================================
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("table_name", sa.String(length=100), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["changed_by"], ["creators.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "action IN ('INSERT', 'UPDATE', 'DELETE')", name="audit_action_check"
        ),
    )
    op.create_index("idx_audit_table_name", "audit_log", ["table_name"])
    op.create_index("idx_audit_record_id", "audit_log", ["record_id"])
    op.create_index("idx_audit_changed_by", "audit_log", ["changed_by"])
    op.create_index(
        "idx_audit_changed_at",
        "audit_log",
        ["changed_at"],
        postgresql_using="btree",
        postgresql_ops={"changed_at": "DESC"},
    )
    op.create_index(
        "idx_audit_old_values_gin", "audit_log", ["old_values"], postgresql_using="gin"
    )
    op.create_index(
        "idx_audit_new_values_gin", "audit_log", ["new_values"], postgresql_using="gin"
    )

    # =========================================================================
    # Functions and Triggers
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trg_creators_updated_at
            BEFORE UPDATE ON creators
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_content_updated_at
            BEFORE UPDATE ON content
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_listings_updated_at
            BEFORE UPDATE ON listings
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_transactions_updated_at
            BEFORE UPDATE ON transactions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_licenses_updated_at
            BEFORE UPDATE ON licenses
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_fraud_reports_updated_at
            BEFORE UPDATE ON fraud_reports
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

    # Audit trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_func()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO audit_log (table_name, record_id, action, old_values, changed_by)
                VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), NULL);
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by)
                VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), NULL);
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO audit_log (table_name, record_id, action, new_values, changed_by)
                VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), NULL);
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_creators
            AFTER INSERT OR UPDATE OR DELETE ON creators
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_content
            AFTER INSERT OR UPDATE OR DELETE ON content
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_listings
            AFTER INSERT OR UPDATE OR DELETE ON listings
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_transactions
            AFTER INSERT OR UPDATE OR DELETE ON transactions
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)

    # =========================================================================
    # Views
    # =========================================================================
    op.execute("""
        CREATE VIEW v_creator_summary AS
        SELECT
            c.id,
            c.username,
            c.display_name,
            c.verification_status,
            c.reputation_score,
            c.total_earnings,
            c.total_sales,
            COUNT(DISTINCT ct.id)  AS content_count,
            COUNT(DISTINCT l.id)   AS listing_count,
            c.created_at
        FROM creators c
        LEFT JOIN content ct ON ct.creator_id = c.id AND ct.status = 'published'
        LEFT JOIN listings l ON l.creator_id = c.id AND l.is_active = true
        GROUP BY c.id
    """)

    op.execute("""
        CREATE VIEW v_content_detail AS
        SELECT
            ct.id,
            ct.title,
            ct.content_type,
            ct.status,
            ct.tags,
            ct.view_count,
            ct.like_count,
            ct.created_at,
            c.id          AS creator_id,
            c.username    AS creator_username,
            c.display_name AS creator_display_name,
            c.avatar_url  AS creator_avatar_url,
            qs.overall_score AS quality_score
        FROM content ct
        JOIN creators c ON c.id = ct.creator_id
        LEFT JOIN quality_scores qs ON qs.content_id = ct.id
    """)

    op.execute("""
        CREATE VIEW v_transaction_summary AS
        SELECT
            t.id,
            t.amount,
            t.currency,
            t.platform_fee,
            t.seller_earnings,
            t.payment_status,
            t.created_at,
            l.title       AS listing_title,
            buyer.username  AS buyer_username,
            seller.username AS seller_username
        FROM transactions t
        JOIN listings l ON l.id = t.listing_id
        JOIN creators buyer ON buyer.id = t.buyer_id
        JOIN creators seller ON seller.id = t.seller_id
    """)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS v_transaction_summary")
    op.execute("DROP VIEW IF EXISTS v_content_detail")
    op.execute("DROP VIEW IF EXISTS v_creator_summary")

    # Drop audit triggers
    op.execute("DROP TRIGGER IF EXISTS trg_audit_transactions ON transactions")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_listings ON listings")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_content ON content")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_creators ON creators")

    # Drop updated_at triggers
    op.execute("DROP TRIGGER IF EXISTS trg_fraud_reports_updated_at ON fraud_reports")
    op.execute("DROP TRIGGER IF EXISTS trg_licenses_updated_at ON licenses")
    op.execute("DROP TRIGGER IF EXISTS trg_transactions_updated_at ON transactions")
    op.execute("DROP TRIGGER IF EXISTS trg_listings_updated_at ON listings")
    op.execute("DROP TRIGGER IF EXISTS trg_content_updated_at ON content")
    op.execute("DROP TRIGGER IF EXISTS trg_creators_updated_at ON creators")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_func")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column")
    op.execute("DROP FUNCTION IF EXISTS immutable_to_tsvector_english")
    op.execute("DROP FUNCTION IF EXISTS immutable_array_to_string")

    # Drop partitions
    op.execute("DROP TABLE IF EXISTS analytics_events_default")
    op.execute("DROP TABLE IF EXISTS analytics_events_2025_q2")
    op.execute("DROP TABLE IF EXISTS analytics_events_2025_q1")
    op.execute("DROP TABLE IF EXISTS analytics_events_2024_q4")

    # Drop tables (order matters for FK constraints)
    op.drop_table("audit_log")
    op.drop_table("analytics_events")
    op.drop_table("fraud_reports")
    op.drop_table("quality_scores")
    op.drop_table("moderation_actions")
    op.drop_table("licenses")
    op.drop_table("transactions")
    op.drop_table("listings")
    op.drop_table("content")
    op.drop_table("creators")
