"""Channel policies for agent governance.

Defines channel-specific policies for different marketing channels
including social media, email, paid ads, and content platforms.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from .engine import PolicyEngine, PolicyRule, PolicyEffect


class ChannelType(str, Enum):
    """Marketing channel types."""

    EMAIL = "email"
    SOCIAL_TWITTER = "social_twitter"
    SOCIAL_LINKEDIN = "social_linkedin"
    SOCIAL_FACEBOOK = "social_facebook"
    SOCIAL_INSTAGRAM = "social_instagram"
    PAID_SEARCH = "paid_search"
    PAID_SOCIAL = "paid_social"
    DISPLAY = "display"
    CONTENT_BLOG = "content_blog"
    CONTENT_VIDEO = "content_video"
    SMS = "sms"
    PUSH = "push"


class ChannelPolicy:
    """Channel policy manager.

    Enforces channel-specific policies including posting frequency,
    content requirements, and compliance rules per channel.
    """

    DEFAULT_RULES: List[Dict[str, Any]] = [
        {
            "id": "deny-email-without-consent",
            "name": "Deny email without consent",
            "description": "Email marketing requires verified consent",
            "effect": "deny",
            "conditions": [
                {"field": "channel.type", "op": "equals", "value": "email"},
                {"field": "channel.has_consent", "op": "equals", "value": False},
            ],
            "actions": ["send", "publish"],
            "resources": ["*"],
            "priority": 100,
        },
        {
            "id": "deny-sms-without-optin",
            "name": "Deny SMS without opt-in",
            "description": "SMS marketing requires explicit opt-in",
            "effect": "deny",
            "conditions": [
                {"field": "channel.type", "op": "equals", "value": "sms"},
                {"field": "channel.has_optin", "op": "equals", "value": False},
            ],
            "actions": ["send"],
            "resources": ["*"],
            "priority": 100,
        },
        {
            "id": "obligate-ads-disclosure",
            "name": "Obligate ad disclosure",
            "description": "Paid ads require disclosure labeling",
            "effect": "obligate",
            "conditions": [
                {"field": "channel.type", "op": "in", "value": ["paid_search", "paid_social", "display"]},
            ],
            "actions": ["publish", "send"],
            "resources": ["*"],
            "priority": 90,
            "metadata": {"obligation:disclosure": "Ad disclosure label required"},
        },
        {
            "id": "deny-frequency-exceeded",
            "name": "Deny posting frequency exceeded",
            "description": "Prevent exceeding channel posting frequency limits",
            "effect": "deny",
            "conditions": [
                {"field": "channel.daily_post_count", "op": "gte", "value": 10},
            ],
            "actions": ["publish", "send"],
            "resources": ["*"],
            "priority": 85,
        },
        {
            "id": "deny-prohibited-hashtags",
            "name": "Deny prohibited hashtags",
            "description": "Block content with prohibited hashtags",
            "effect": "deny",
            "conditions": [
                {"field": "channel.has_prohibited_hashtags", "op": "equals", "value": True},
            ],
            "actions": ["publish"],
            "resources": ["*"],
            "priority": 95,
        },
        {
            "id": "allow-compliant-channel",
            "name": "Allow compliant channel action",
            "description": "Channel actions within policy are allowed",
            "effect": "allow",
            "conditions": [
                {"field": "channel.is_compliant", "op": "equals", "value": True},
            ],
            "actions": ["publish", "send"],
            "resources": ["*"],
            "priority": 10,
        },
    ]

    def __init__(self, engine: Optional[PolicyEngine] = None) -> None:
        """Initialize channel policy.

        Args:
            engine: Optional policy engine instance.
        """
        self._engine = engine or PolicyEngine()
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default channel rules."""
        for rule_data in self.DEFAULT_RULES:
            rule = PolicyRule.from_dict(rule_data)
            self._engine.add_rule(rule)

    def check_channel_action(
        self,
        agent_id: str,
        action: str,
        channel_type: ChannelType,
        channel_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check if a channel action is allowed.

        Args:
            agent_id: The agent identifier.
            action: The action (publish, send).
            channel_type: The marketing channel type.
            channel_context: Channel-specific context.

        Returns:
            Policy decision result.
        """
        ctx = channel_context or {}
        ctx["channel"] = ctx.get("channel", {})
        ctx["channel"]["type"] = channel_type.value
        ctx.setdefault("agent", {})["id"] = agent_id

        decision = self._engine.evaluate(action, "*", ctx)
        return decision.to_dict()

    def add_custom_rule(self, rule: PolicyRule) -> None:
        """Add a custom channel rule.

        Args:
            rule: The policy rule to add.
        """
        self._engine.add_rule(rule)

    @property
    def engine(self) -> PolicyEngine:
        """Get the underlying policy engine."""
        return self._engine
