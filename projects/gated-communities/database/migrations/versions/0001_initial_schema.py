"""Initial schema for gated communities

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')

    # Create enum types
    op.execute("""
        CREATE TYPE community_visibility AS ENUM ('public', 'private', 'hidden')
    """)
    op.execute("""
        CREATE TYPE community_status AS ENUM ('active', 'archived', 'suspended', 'deleted')
    """)
    op.execute("""
        CREATE TYPE tier_billing_period AS ENUM ('monthly', 'quarterly', 'yearly', 'lifetime')
    """)
    op.execute("""
        CREATE TYPE member_role AS ENUM ('owner', 'admin', 'moderator', 'member', 'guest')
    """)
    op.execute("""
        CREATE TYPE member_status AS ENUM ('active', 'invited', 'banned', 'suspended', 'removed')
    """)
    op.execute("""
        CREATE TYPE content_type AS ENUM ('post', 'comment', 'reply', 'poll', 'event', 'media')
    """)
    op.execute("""
        CREATE TYPE content_status AS ENUM ('draft', 'published', 'edited', 'archived', 'deleted', 'flagged')
    """)
    op.execute("""
        CREATE TYPE moderation_action_type AS ENUM (
            'warn', 'mute', 'unmute', 'ban', 'unban', 'content_remove',
            'content_restore', 'tier_change', 'role_change', 'note'
        )
    """)
    op.execute("""
        CREATE TYPE moderation_action_status AS ENUM ('pending', 'applied', 'reversed', 'expired')
    """)
    op.execute("""
        CREATE TYPE escalation_priority AS ENUM ('low', 'medium', 'high', 'critical')
    """)
    op.execute("""
        CREATE TYPE escalation_status AS ENUM ('open', 'investigating', 'resolved', 'dismissed', 'escalated')
    """)
    op.execute("""
        CREATE TYPE escalation_category AS ENUM (
            'harassment', 'spam', 'hate_speech', 'misinformation',
            'privacy_violation', 'illegal_content', 'other'
        )
    """)
    op.execute("""
        CREATE TYPE compliance_report_type AS ENUM (
            'gdpr_access', 'gdpr_deletion', 'gdpr_portability',
            'dmca', 'csam', 'law_enforcement', 'internal_audit'
        )
    """)
    op.execute("""
        CREATE TYPE compliance_report_status AS ENUM ('pending', 'in_review', 'fulfilled', 'rejected', 'appealed')
    """)
    op.execute("""
        CREATE TYPE analytics_event_type AS ENUM (
            'page_view', 'content_view', 'content_like', 'content_share',
            'member_join', 'member_leave', 'tier_subscribe', 'tier_cancel',
            'search_query', 'notification_sent', 'notification_click'
        )
    """)
    op.execute("""
        CREATE TYPE audit_action AS ENUM ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'GRANT', 'REVOKE')
    """)

    # Create communities table
    op.create_table(
        'communities',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('banner_url', sa.Text(), nullable=True),
        sa.Column('visibility', sa.Enum('public', 'private', 'hidden', name='community_visibility'), server_default='private', nullable=False),
        sa.Column('status', sa.Enum('active', 'archived', 'suspended', 'deleted', name='community_status'), server_default='active', nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('member_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('content_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('char_length(trim(name)) > 0', name='chk_communities_name_not_empty'),
        sa.CheckConstraint('member_count >= 0', name='chk_communities_member_count'),
        sa.CheckConstraint('content_count >= 0', name='chk_communities_content_count'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_communities_slug')
    )
    op.create_index('idx_communities_slug', 'communities', ['slug'])
    op.create_index('idx_communities_visibility', 'communities', ['visibility'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_communities_status', 'communities', ['status'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_communities_created_by', 'communities', ['created_by'])
    op.create_index('idx_communities_metadata_gin', 'communities', ['metadata'], postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    op.create_index('idx_communities_settings_gin', 'communities', ['settings'], postgresql_using='gin', postgresql_ops={'settings': 'jsonb_path_ops'})

    # Create tiers table
    op.create_table(
        'tiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('community_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('price_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('billing_period', sa.Enum('monthly', 'quarterly', 'yearly', 'lifetime', name='tier_billing_period'), server_default='monthly', nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('benefits', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('subscriber_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('char_length(trim(name)) > 0', name='chk_tiers_name_not_empty'),
        sa.CheckConstraint('price_cents >= 0', name='chk_tiers_price_cents'),
        sa.CheckConstraint('subscriber_count >= 0', name='chk_tiers_subscriber_count'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('community_id', 'slug', name='uq_tiers_community_slug')
    )
    op.create_index('idx_tiers_community_id', 'tiers', ['community_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_tiers_is_public', 'tiers', ['is_public'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_tiers_is_active', 'tiers', ['is_active'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_tiers_benefits_gin', 'tiers', ['benefits'], postgresql_using='gin', postgresql_ops={'benefits': 'jsonb_path_ops'})

    # Create members table
    op.create_table(
        'members',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('community_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role', sa.Enum('owner', 'admin', 'moderator', 'member', 'guest', name='member_role'), server_default='member', nullable=False),
        sa.Column('status', sa.Enum('active', 'invited', 'banned', 'suspended', 'removed', name='member_status'), server_default='invited', nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), server_default='', nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('banned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('banned_reason', sa.Text(), nullable=True),
        sa.Column('tier_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_prefs', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('display_name IS NULL OR char_length(trim(display_name)) > 0', name='chk_members_display_name'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tier_id'], ['tiers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('community_id', 'user_id', name='uq_members_community_user')
    )
    op.create_index('idx_members_community_id', 'members', ['community_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_members_user_id', 'members', ['user_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_members_tier_id', 'members', ['tier_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_members_role', 'members', ['role'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_members_status', 'members', ['status'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_members_last_active', 'members', ['last_active_at'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_members_metadata_gin', 'members', ['metadata'], postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    op.create_index('idx_members_notification_prefs_gin', 'members', ['notification_prefs'], postgresql_using='gin', postgresql_ops={'notification_prefs': 'jsonb_path_ops'})

    # Create content table
    op.create_table(
        'content',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('community_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content_type', sa.Enum('post', 'comment', 'reply', 'poll', 'event', 'media', name='content_type'), server_default='post', nullable=False),
        sa.Column('status', sa.Enum('draft', 'published', 'edited', 'archived', 'deleted', 'flagged', name='content_status'), server_default='draft', nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('body', sa.Text(), server_default='', nullable=False),
        sa.Column('body_rendered', sa.Text(), server_default='', nullable=False),
        sa.Column('media_urls', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('like_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('comment_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('share_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_pinned', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_locked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('title IS NULL OR char_length(trim(title)) > 0', name='chk_content_title'),
        sa.CheckConstraint('like_count >= 0', name='chk_content_like_count'),
        sa.CheckConstraint('comment_count >= 0', name='chk_content_comment_count'),
        sa.CheckConstraint('share_count >= 0', name='chk_content_share_count'),
        sa.CheckConstraint('view_count >= 0', name='chk_content_view_count'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['content.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_content_community_id', 'content', ['community_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_content_author_id', 'content', ['author_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_content_parent_id', 'content', ['parent_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_content_type', 'content', ['content_type'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_content_status', 'content', ['status'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_content_published_at', 'content', ['published_at'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_content_is_pinned', 'content', ['is_pinned', 'published_at'], postgresql_where=sa.text('deleted_at IS NULL AND is_pinned = true'))
    op.create_index('idx_content_tags_gin', 'content', ['tags'], postgresql_using='gin', postgresql_ops={'tags': 'jsonb_path_ops'})
    op.create_index('idx_content_metadata_gin', 'content', ['metadata'], postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    op.create_index('idx_content_media_urls_gin', 'content', ['media_urls'], postgresql_using='gin', postgresql_ops={'media_urls': 'jsonb_path_ops'})

    # Create moderation_actions table
    op.create_table(
        'moderation_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('community_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_member_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.Enum('warn', 'mute', 'unmute', 'ban', 'unban', 'content_remove', 'content_restore', 'tier_change', 'role_change', 'note', name='moderation_action_type'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'applied', 'reversed', 'expired', name='moderation_action_status'), server_default='pending', nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('applied_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reversed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reversal_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('char_length(trim(reason)) > 0', name='chk_moderation_reason_not_empty'),
        sa.CheckConstraint('duration_hours IS NULL OR duration_hours > 0', name='chk_moderation_duration_hours'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_member_id'], ['members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_content_id'], ['content.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['applied_by'], ['members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reversed_by'], ['members.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_moderation_community_id', 'moderation_actions', ['community_id'])
    op.create_index('idx_moderation_target_member', 'moderation_actions', ['target_member_id'])
    op.create_index('idx_moderation_target_content', 'moderation_actions', ['target_content_id'])
    op.create_index('idx_moderation_action_type', 'moderation_actions', ['action_type'])
    op.create_index('idx_moderation_status', 'moderation_actions', ['status'])
    op.create_index('idx_moderation_applied_by', 'moderation_actions', ['applied_by'])
    op.create_index('idx_moderation_expires_at', 'moderation_actions', ['expires_at'], postgresql_where=sa.text('expires_at IS NOT NULL'))
    op.create_index('idx_moderation_details_gin', 'moderation_actions', ['details'], postgresql_using='gin', postgresql_ops={'details': 'jsonb_path_ops'})

    # Create reputation_scores table
    op.create_table(
        'reputation_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('community_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('member_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_earned', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_deducted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('breakdown', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('last_event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('total_earned >= 0', name='chk_reputation_total_earned'),
        sa.CheckConstraint('total_deducted >= 0', name='chk_reputation_total_deducted'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('community_id', 'member_id', name='uq_reputation_community_member')
    )
    op.create_index('idx_reputation_community_id', 'reputation_scores', ['community_id'])
    op.create_index('idx_reputation_member_id', 'reputation_scores', ['member_id'])
    op.create_index('idx_reputation_score', 'reputation_scores', ['score'], postgresql_using='btree', postgresql_ops={'score': 'DESC'})
    op.create_index('idx_reputation_breakdown_gin', 'reputation_scores', ['breakdown'], postgresql_using='gin', postgresql_ops={'breakdown': 'jsonb_path_ops'})

    # Create escalations table
    op.create_table(
        'escalations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('community_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_member_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category', sa.Enum('harassment', 'spam', 'hate_speech', 'misinformation', 'privacy_violation', 'illegal_content', 'other', name='escalation_category'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='escalation_priority'), server_default='medium', nullable=False),
        sa.Column('status', sa.Enum('open', 'investigating', 'resolved', 'dismissed', 'escalated', name='escalation_status'), server_default='open', nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('char_length(trim(subject)) > 0', name='chk_escalations_subject_not_empty'),
        sa.CheckConstraint('char_length(trim(description)) > 0', name='chk_escalations_description_not_empty'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reporter_id'], ['members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_member_id'], ['members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_content_id'], ['content.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by'], ['members.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_escalations_community_id', 'escalations', ['community_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_reporter', 'escalations', ['reporter_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_target_member', 'escalations', ['target_member_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_target_content', 'escalations', ['target_content_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_category', 'escalations', ['category'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_priority', 'escalations', ['priority'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_status', 'escalations', ['status'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_assigned_to', 'escalations', ['assigned_to'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_escalations_due_at', 'escalations', ['due_at'], postgresql_where=sa.text('deleted_at IS NULL AND due_at IS NOT NULL'))
    op.create_index('idx_escalations_metadata_gin', 'escalations', ['metadata'], postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})

    # Create compliance_reports table
    op.create_table(
        'compliance_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('community_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('report_type', sa.Enum('gdpr_access', 'gdpr_deletion', 'gdpr_portability', 'dmca', 'csam', 'law_enforcement', 'internal_audit', name='compliance_report_type'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_review', 'fulfilled', 'rejected', 'appealed', name='compliance_report_status'), server_default='pending', nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_urls', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('external_ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('char_length(trim(subject)) > 0', name='chk_compliance_subject_not_empty'),
        sa.CheckConstraint('char_length(trim(description)) > 0', name='chk_compliance_description_not_empty'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reporter_id'], ['members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['members.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_compliance_community_id', 'compliance_reports', ['community_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_compliance_reporter', 'compliance_reports', ['reporter_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_compliance_report_type', 'compliance_reports', ['report_type'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_compliance_status', 'compliance_reports', ['status'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_compliance_reviewed_by', 'compliance_reports', ['reviewed_by'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_compliance_external_ref', 'compliance_reports', ['external_ref'], postgresql_where=sa.text('external_ref IS NOT NULL'))
    op.create_index('idx_compliance_evidence_gin', 'compliance_reports', ['evidence_urls'], postgresql_using='gin', postgresql_ops={'evidence_urls': 'jsonb_path_ops'})
    op.create_index('idx_compliance_metadata_gin', 'compliance_reports', ['metadata'], postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})

    # Create analytics_events partitioned table
    op.execute("""
        CREATE TABLE analytics_events (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            community_id UUID NOT NULL,
            user_id UUID,
            session_id VARCHAR(255),
            event_type analytics_event_type NOT NULL,
            event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            ip_address INET,
            user_agent TEXT,
            referrer_url TEXT,
            page_url TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)

    # Create partitions
    op.execute("""
        CREATE TABLE analytics_events_2026_10 PARTITION OF analytics_events
        FOR VALUES FROM ('2026-10-01') TO ('2026-11-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2026_11 PARTITION OF analytics_events
        FOR VALUES FROM ('2026-11-01') TO ('2026-12-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2026_12 PARTITION OF analytics_events
        FOR VALUES FROM ('2026-12-01') TO ('2027-01-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_01 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-01-01') TO ('2027-02-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_02 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-02-01') TO ('2027-03-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_03 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-03-01') TO ('2027-04-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_04 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-04-01') TO ('2027-05-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_05 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-05-01') TO ('2027-06-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_06 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-06-01') TO ('2027-07-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_07 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-07-01') TO ('2027-08-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_08 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-08-01') TO ('2027-09-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_09 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-09-01') TO ('2027-10-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_10 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-10-01') TO ('2027-11-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_11 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-11-01') TO ('2027-12-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_2027_12 PARTITION OF analytics_events
        FOR VALUES FROM ('2027-12-01') TO ('2028-01-01')
    """)
    op.execute("""
        CREATE TABLE analytics_events_default PARTITION OF analytics_events DEFAULT
    """)

    # Create indexes on partitioned table
    op.create_index('idx_analytics_community_id', 'analytics_events', ['community_id'])
    op.create_index('idx_analytics_user_id', 'analytics_events', ['user_id'])
    op.create_index('idx_analytics_event_type', 'analytics_events', ['event_type'])
    op.create_index('idx_analytics_created_at', 'analytics_events', ['created_at'])
    op.create_index('idx_analytics_session_id', 'analytics_events', ['session_id'])
    op.create_index('idx_analytics_event_data_gin', 'analytics_events', ['event_data'], postgresql_using='gin', postgresql_ops={'event_data': 'jsonb_path_ops'})
    op.create_index('idx_analytics_community_event', 'analytics_events', ['community_id', 'event_type', 'created_at'])

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('table_name', sa.String(length=128), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Enum('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'GRANT', 'REVOKE', name='audit_action'), nullable=False),
        sa.Column('old_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('performed_by_type', sa.String(length=50), server_default='user', nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('request_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_table_name', 'audit_log', ['table_name'])
    op.create_index('idx_audit_record_id', 'audit_log', ['record_id'])
    op.create_index('idx_audit_action', 'audit_log', ['action'])
    op.create_index('idx_audit_performed_by', 'audit_log', ['performed_by'])
    op.create_index('idx_audit_created_at', 'audit_log', ['created_at'])
    op.create_index('idx_audit_table_record', 'audit_log', ['table_name', 'record_id'])
    op.create_index('idx_audit_old_data_gin', 'audit_log', ['old_data'], postgresql_using='gin', postgresql_ops={'old_data': 'jsonb_path_ops'})
    op.create_index('idx_audit_new_data_gin', 'audit_log', ['new_data'], postgresql_using='gin', postgresql_ops={'new_data': 'jsonb_path_ops'})

    # Create update_updated_at function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Create triggers for updated_at
    op.execute("""
        CREATE TRIGGER trg_communities_updated_at
            BEFORE UPDATE ON communities
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_tiers_updated_at
            BEFORE UPDATE ON tiers
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_members_updated_at
            BEFORE UPDATE ON members
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_content_updated_at
            BEFORE UPDATE ON content
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_moderation_actions_updated_at
            BEFORE UPDATE ON moderation_actions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_reputation_scores_updated_at
            BEFORE UPDATE ON reputation_scores
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_escalations_updated_at
            BEFORE UPDATE ON escalations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    op.execute("""
        CREATE TRIGGER trg_compliance_reports_updated_at
            BEFORE UPDATE ON compliance_reports
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

    # Create audit trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_func()
        RETURNS TRIGGER AS $$
        DECLARE
            v_old_data JSONB;
            v_new_data JSONB;
            v_changed_fields JSONB;
            v_record_id UUID;
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                v_old_data = to_jsonb(OLD);
                v_new_data = NULL;
                v_changed_fields = NULL;
                v_record_id = OLD.id;
            ELSIF (TG_OP = 'INSERT') THEN
                v_old_data = NULL;
                v_new_data = to_jsonb(NEW);
                v_changed_fields = NULL;
                v_record_id = NEW.id;
            ELSIF (TG_OP = 'UPDATE') THEN
                v_old_data = to_jsonb(OLD);
                v_new_data = to_jsonb(NEW);
                v_changed_fields = (
                    SELECT jsonb_agg(key)
                    FROM jsonb_each(v_new_data) AS n(key, value)
                    WHERE v_old_data->key IS DISTINCT FROM n.value
                );
                v_record_id = NEW.id;
            END IF;

            INSERT INTO audit_log (
                table_name, record_id, action, old_data, new_data,
                changed_fields, performed_by, performed_by_type
            ) VALUES (
                TG_TABLE_NAME, v_record_id, TG_OP, v_old_data, v_new_data,
                v_changed_fields, NULL, 'system'
            );

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql
    """)

    # Create audit triggers
    op.execute("""
        CREATE TRIGGER trg_audit_communities
            AFTER INSERT OR UPDATE OR DELETE ON communities
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_members
            AFTER INSERT OR UPDATE OR DELETE ON members
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_content
            AFTER INSERT OR UPDATE OR DELETE ON content
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_moderation_actions
            AFTER INSERT OR UPDATE OR DELETE ON moderation_actions
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_escalations
            AFTER INSERT OR UPDATE OR DELETE ON escalations
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_compliance_reports
            AFTER INSERT OR UPDATE OR DELETE ON compliance_reports
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()
    """)

    # Create views
    op.execute("""
        CREATE OR REPLACE VIEW v_community_summary AS
        SELECT
            c.id,
            c.slug,
            c.name,
            c.visibility,
            c.status,
            c.member_count,
            c.content_count,
            c.created_at,
            COUNT(DISTINCT m.id) FILTER (WHERE m.status = 'active') AS active_members,
            COUNT(DISTINCT t.id) FILTER (WHERE t.is_active = true) AS active_tiers,
            COUNT(DISTINCT ct.id) FILTER (WHERE ct.status = 'published') AS published_content
        FROM communities c
        LEFT JOIN members m ON m.community_id = c.id AND m.deleted_at IS NULL
        LEFT JOIN tiers t ON t.community_id = c.id AND t.deleted_at IS NULL
        LEFT JOIN content ct ON ct.community_id = c.id AND ct.deleted_at IS NULL
        WHERE c.deleted_at IS NULL
        GROUP BY c.id
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_member_detail AS
        SELECT
            m.id,
            m.community_id,
            c.slug AS community_slug,
            c.name AS community_name,
            m.user_id,
            m.role,
            m.status,
            m.display_name,
            m.bio,
            m.joined_at,
            m.last_active_at,
            m.tier_id,
            t.name AS tier_name,
            m.tier_expires_at,
            rs.score AS reputation_score,
            m.created_at
        FROM members m
        JOIN communities c ON c.id = m.community_id
        LEFT JOIN tiers t ON t.id = m.tier_id
        LEFT JOIN reputation_scores rs ON rs.member_id = m.id AND rs.community_id = m.community_id
        WHERE m.deleted_at IS NULL
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_content_detail AS
        SELECT
            ct.id,
            ct.community_id,
            c.slug AS community_slug,
            ct.author_id,
            m.display_name AS author_name,
            ct.content_type,
            ct.status,
            ct.title,
            ct.body,
            ct.tags,
            ct.like_count,
            ct.comment_count,
            ct.share_count,
            ct.view_count,
            ct.is_pinned,
            ct.published_at,
            ct.created_at
        FROM content ct
        JOIN communities c ON c.id = ct.community_id
        JOIN members m ON m.id = ct.author_id
        WHERE ct.deleted_at IS NULL
    """)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS v_content_detail")
    op.execute("DROP VIEW IF EXISTS v_member_detail")
    op.execute("DROP VIEW IF EXISTS v_community_summary")

    # Drop audit triggers
    op.execute("DROP TRIGGER IF EXISTS trg_audit_compliance_reports ON compliance_reports")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_escalations ON escalations")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_moderation_actions ON moderation_actions")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_content ON content")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_members ON members")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_communities ON communities")

    # Drop audit function
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_func()")

    # Drop updated_at triggers
    op.execute("DROP TRIGGER IF EXISTS trg_compliance_reports_updated_at ON compliance_reports")
    op.execute("DROP TRIGGER IF EXISTS trg_escalations_updated_at ON escalations")
    op.execute("DROP TRIGGER IF EXISTS trg_reputation_scores_updated_at ON reputation_scores")
    op.execute("DROP TRIGGER IF EXISTS trg_moderation_actions_updated_at ON moderation_actions")
    op.execute("DROP TRIGGER IF EXISTS trg_content_updated_at ON content")
    op.execute("DROP TRIGGER IF EXISTS trg_members_updated_at ON members")
    op.execute("DROP TRIGGER IF EXISTS trg_tiers_updated_at ON tiers")
    op.execute("DROP TRIGGER IF EXISTS trg_communities_updated_at ON communities")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop audit_log table
    op.drop_table('audit_log')

    # Drop analytics_events partitions
    op.execute("DROP TABLE IF EXISTS analytics_events_default")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_12")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_11")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_10")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_09")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_08")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_07")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_06")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_05")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_04")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_03")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_02")
    op.execute("DROP TABLE IF EXISTS analytics_events_2027_01")
    op.execute("DROP TABLE IF EXISTS analytics_events_2026_12")
    op.execute("DROP TABLE IF EXISTS analytics_events_2026_11")
    op.execute("DROP TABLE IF EXISTS analytics_events_2026_10")
    op.execute("DROP TABLE IF EXISTS analytics_events")

    # Drop compliance_reports table
    op.drop_table('compliance_reports')

    # Drop escalations table
    op.drop_table('escalations')

    # Drop reputation_scores table
    op.drop_table('reputation_scores')

    # Drop moderation_actions table
    op.drop_table('moderation_actions')

    # Drop content table
    op.drop_table('content')

    # Drop members table
    op.drop_table('members')

    # Drop tiers table
    op.drop_table('tiers')

    # Drop communities table
    op.drop_table('communities')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS audit_action")
    op.execute("DROP TYPE IF EXISTS analytics_event_type")
    op.execute("DROP TYPE IF EXISTS compliance_report_status")
    op.execute("DROP TYPE IF EXISTS compliance_report_type")
    op.execute("DROP TYPE IF EXISTS escalation_category")
    op.execute("DROP TYPE IF EXISTS escalation_status")
    op.execute("DROP TYPE IF EXISTS escalation_priority")
    op.execute("DROP TYPE IF EXISTS moderation_action_status")
    op.execute("DROP TYPE IF EXISTS moderation_action_type")
    op.execute("DROP TYPE IF EXISTS content_status")
    op.execute("DROP TYPE IF EXISTS content_type")
    op.execute("DROP TYPE IF EXISTS member_status")
    op.execute("DROP TYPE IF EXISTS member_role")
    op.execute("DROP TYPE IF EXISTS tier_billing_period")
    op.execute("DROP TYPE IF EXISTS community_status")
    op.execute("DROP TYPE IF EXISTS community_visibility")
