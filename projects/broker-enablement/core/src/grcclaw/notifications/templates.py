"""
Template engine for GRC_Claw notifications.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from .models import Notification, NotificationType, Template, TemplateVariable

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Renders notification content from templates with variable substitution.

    Supports:
    - Variable substitution: {{variable_name}}
    - Conditional blocks: {% if condition %}...{% endif %}
    - Loops: {% for item in items %}...{% endfor %}
    - Default values: {{variable_name|default("N/A")}}
    - Date formatting: {{date_var|format_date("%Y-%m-%d")}}
    - Built-in variables: {{current_date}}, {{notification_id}}, etc.
    """

    def __init__(self):
        self._templates: dict[str, Template] = {}
        self._default_templates: dict[str, Template] = {}
        self._register_default_templates()

    # ─── Template Management ─────────────────────────────────────────────────

    def register(self, template: Template) -> None:
        """Register a template."""
        self._templates[template.id] = template
        logger.info(f"Registered template: {template.name} ({template.id})")

    def unregister(self, template_id: str) -> None:
        """Remove a template."""
        self._templates.pop(template_id, None)

    def get(self, template_id: str) -> Template | None:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def get_by_name(self, name: str) -> Template | None:
        """Get a template by name."""
        for template in self._templates.values():
            if template.name == name:
                return template
        return None

    def list_templates(
        self,
        notification_type: NotificationType | None = None,
        enabled_only: bool = True,
    ) -> list[Template]:
        """List all templates, optionally filtered."""
        templates = self._templates.values()
        if enabled_only:
            templates = [t for t in templates if t.enabled]
        if notification_type:
            templates = [t for t in templates if t.notification_type == notification_type]
        return list(templates)

    # ─── Rendering ───────────────────────────────────────────────────────────

    def render(
        self,
        template: Template,
        data: dict[str, Any],
        channel: str | None = None,
    ) -> dict[str, str]:
        """
        Render a template with the given data.

        Returns a dict with 'title', 'body', and 'summary' keys.
        """
        # Merge built-in variables
        context = self._build_context(data)

        # Check for channel-specific overrides
        overrides = template.channel_overrides.get(channel, {}) if channel else {}

        title = self._render_string(
            overrides.get("title", template.title_template),
            context,
        )
        body = self._render_string(
            overrides.get("body", template.body_template),
            context,
        )
        summary = self._render_string(
            overrides.get("summary", template.summary_template),
            context,
        )

        return {
            "title": title,
            "body": body,
            "summary": summary,
        }

    def render_for_notification(
        self,
        notification: Notification,
        channel: str | None = None,
    ) -> dict[str, str]:
        """Render a notification using its assigned template."""
        if not notification.template_id:
            return {
                "title": notification.title,
                "body": notification.body,
                "summary": notification.summary,
            }

        template = self._templates.get(notification.template_id)
        if not template:
            logger.warning(f"Template not found: {notification.template_id}")
            return {
                "title": notification.title,
                "body": notification.body,
                "summary": notification.summary,
            }

        return self.render(template, notification.template_data, channel)

    def apply_to_notification(
        self,
        notification: Notification,
        channel: str | None = None,
    ) -> Notification:
        """Apply template rendering to a notification, updating its content."""
        rendered = self.render_for_notification(notification, channel)
        notification.title = rendered["title"]
        notification.body = rendered["body"]
        notification.summary = rendered["summary"]
        return notification

    # ─── Validation ──────────────────────────────────────────────────────────

    def validate_data(self, template: Template, data: dict[str, Any]) -> list[str]:
        """Validate that data satisfies the template's required variables."""
        errors = []
        for var in template.variables:
            if var.required and var.name not in data:
                if var.default is None:
                    errors.append(f"Missing required variable: {var.name}")
        return errors

    def extract_variables(self, template: Template) -> list[str]:
        """Extract all variable names referenced in a template."""
        variables = set()
        for field in [template.title_template, template.body_template, template.summary_template]:
            if field:
                variables.update(self._extract_vars_from_string(field))
        return sorted(variables)

    # ─── String Rendering ────────────────────────────────────────────────────

    def _render_string(self, template_str: str, context: dict[str, Any]) -> str:
        """Render a template string with variable substitution and control flow."""
        if not template_str:
            return ""

        result = template_str

        # Process conditional blocks: {% if condition %}...{% endif %}
        result = self._process_conditionals(result, context)

        # Process loops: {% for item in items %}...{% endfor %}
        result = self._process_loops(result, context)

        # Process variable substitution with filters: {{var|filter}}
        result = self._process_variables(result, context)

        return result.strip()

    def _process_conditionals(self, text: str, context: dict[str, Any]) -> str:
        """Process {% if condition %}...{% endif %} blocks."""
        pattern = r"\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}"

        def replace_conditional(match):
            condition_var = match.group(1)
            content = match.group(2)
            value = context.get(condition_var)
            if value:
                return content
            return ""

        prev = None
        while prev != text:
            prev = text
            text = re.sub(pattern, replace_conditional, text, flags=re.DOTALL)

        return text

    def _process_loops(self, text: str, context: dict[str, Any]) -> str:
        """Process {% for item in items %}...{% endfor %} blocks."""
        pattern = r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}"

        def replace_loop(match):
            item_name = match.group(1)
            list_name = match.group(2)
            content = match.group(3)
            items = context.get(list_name, [])
            if not isinstance(items, list):
                return ""
            results = []
            for item in items:
                loop_context = {**context, item_name: item}
                rendered = self._process_variables(content, loop_context)
                results.append(rendered)
            return "".join(results)

        prev = None
        while prev != text:
            prev = text
            text = re.sub(pattern, replace_loop, text, flags=re.DOTALL)

        return text

    def _process_variables(self, text: str, context: dict[str, Any]) -> str:
        """Process {{variable}} and {{variable|filter}} substitutions."""
        pattern = r"\{\{\s*(\w+)(?:\|(\w+)(?:\(([^)]*)\))?)?\s*\}\}"

        def replace_variable(match):
            var_name = match.group(1)
            filter_name = match.group(2)
            filter_args = match.group(3)

            value = context.get(var_name)

            if value is None:
                return ""

            if filter_name:
                value = self._apply_filter(value, filter_name, filter_args)

            return str(value)

        return re.sub(pattern, replace_variable, text)

    def _apply_filter(self, value: Any, filter_name: str, args: str | None) -> Any:
        """Apply a filter to a value."""
        if filter_name == "default":
            return value or (args or "")
        elif filter_name == "upper":
            return str(value).upper()
        elif filter_name == "lower":
            return str(value).lower()
        elif filter_name == "title":
            return str(value).title()
        elif filter_name == "format_date":
            fmt = args or "%Y-%m-%d"
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    return dt.strftime(fmt)
                except (ValueError, TypeError):
                    return str(value)
            return str(value)
        elif filter_name == "truncate":
            length = int(args) if args else 100
            s = str(value)
            return s[:length] + "..." if len(s) > length else s
        elif filter_name == "join":
            sep = args or ", "
            if isinstance(value, list):
                return sep.join(str(v) for v in value)
            return str(value)
        return value

    def _build_context(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the rendering context with built-in variables."""
        now = datetime.now(UTC)
        context = {
            **data,
            "current_date": now.strftime("%Y-%m-%d"),
            "current_datetime": now.isoformat(),
            "current_time": now.strftime("%H:%M:%S"),
            "current_year": str(now.year),
            "current_month": str(now.month),
            "current_day": str(now.day),
        }
        return context

    def _extract_vars_from_string(self, text: str) -> list[str]:
        """Extract variable names from a template string."""
        pattern = r"\{\{\s*(\w+)"
        return re.findall(pattern, text)

    # ─── Default Templates ───────────────────────────────────────────────────

    def _register_default_templates(self) -> None:
        """Register built-in default templates for common notification types."""

        # Compliance Violation Template
        self._default_templates["compliance_violation"] = Template(
            name="Compliance Violation",
            notification_type=NotificationType.COMPLIANCE_VIOLATION,
            title_template="🚨 Compliance Violation: {{framework}} — {{control_name}}",
            body_template="""A compliance violation has been detected.

**Framework:** {{framework}}
**Control:** {{control_name}} ({{control_id}})
**Severity:** {{severity}}
**Entity:** {{entity_type}} — {{entity_id}}
**Detected:** {{detected_at|format_date("%Y-%m-%d %H:%M:%S")}}

**Description:**
{{description}}

{% if evidence %}
**Evidence:**
{% for item in evidence %}
- {{item}}
{% endfor %}
{% endif %}

{% if runbook_url %}
**Runbook:** {{runbook_url}}
{% endif %}

Please review and take appropriate action.""",
            summary_template="Compliance violation: {{framework}} — {{control_name}}",
            variables=[
                TemplateVariable(name="framework", description="Compliance framework"),
                TemplateVariable(name="control_name", description="Name of the control"),
                TemplateVariable(name="control_id", description="Control identifier"),
                TemplateVariable(name="severity", description="Severity level"),
                TemplateVariable(name="entity_type", description="Type of entity"),
                TemplateVariable(name="entity_id", description="Entity identifier"),
                TemplateVariable(name="detected_at", description="Detection timestamp"),
                TemplateVariable(name="description", description="Violation description"),
                TemplateVariable(name="evidence", description="List of evidence items", required=False),
                TemplateVariable(name="runbook_url", description="Runbook URL", required=False),
            ],
        )

        # Risk Threshold Exceeded Template
        self._default_templates["risk_threshold_exceeded"] = Template(
            name="Risk Threshold Exceeded",
            notification_type=NotificationType.RISK_THRESHOLD_EXCEEDED,
            title_template="⚠️ Risk Threshold Exceeded: {{risk_name}}",
            body_template="""A risk threshold has been exceeded.

**Risk:** {{risk_name}}
**Current Value:** {{current_value}}
**Threshold:** {{threshold}}
**Exceeded By:** {{exceeded_by}}
**Entity:** {{entity_type}} — {{entity_id}}

**Recommendation:**
{{recommendation}}

{% if related_alerts %}
**Related Alerts:**
{% for alert in related_alerts %}
- {{alert}}
{% endfor %}
{% endif %}""",
            summary_template="Risk threshold exceeded: {{risk_name}} ({{current_value}} > {{threshold}})",
            variables=[
                TemplateVariable(name="risk_name", description="Name of the risk"),
                TemplateVariable(name="current_value", description="Current risk value"),
                TemplateVariable(name="threshold", description="Threshold value"),
                TemplateVariable(name="exceeded_by", description="Amount exceeded"),
                TemplateVariable(name="entity_type", description="Type of entity"),
                TemplateVariable(name="entity_id", description="Entity identifier"),
                TemplateVariable(name="recommendation", description="Recommended action"),
                TemplateVariable(name="related_alerts", description="Related alert IDs", required=False),
            ],
        )

        # Certificate Expiring Template
        self._default_templates["certificate_expiring"] = Template(
            name="Certificate Expiring",
            notification_type=NotificationType.CERTIFICATE_EXPIRING,
            title_template="📜 Certificate Expiring: {{cert_name}}",
            body_template="""A certificate is approaching expiration.

**Certificate:** {{cert_name}}
**Domain:** {{domain}}
**Expires:** {{expiry_date|format_date("%Y-%m-%d")}}
**Days Remaining:** {{days_remaining}}
**Issuer:** {{issuer}}

{% if days_remaining < 7 %}
⚠️ **URGENT:** This certificate expires in less than 7 days!
{% endif %}

Please renew this certificate before expiration to avoid service disruption.""",
            summary_template="Certificate expiring: {{cert_name}} ({{days_remaining}} days left)",
            variables=[
                TemplateVariable(name="cert_name", description="Certificate name"),
                TemplateVariable(name="domain", description="Domain name"),
                TemplateVariable(name="expiry_date", description="Expiration date"),
                TemplateVariable(name="days_remaining", description="Days until expiration"),
                TemplateVariable(name="issuer", description="Certificate issuer"),
            ],
        )

        # Daily Digest Template
        self._default_templates["daily_digest"] = Template(
            name="Daily Digest",
            notification_type=NotificationType.DAILY_DIGEST,
            title_template="📊 GRC Daily Digest — {{current_date}}",
            body_template="""**GRC Daily Digest for {{current_date}}**

**Summary:**
- Total Alerts: {{total_alerts}}
- Critical: {{critical_count}}
- High: {{high_count}}
- Medium: {{medium_count}}
- Low: {{low_count}}

**Open Items:**
{% for item in open_items %}
- {{item}}
{% endfor %}

**Recent Activity:**
{% for activity in recent_activity %}
- {{activity}}
{% endfor %}""",
            summary_template="GRC Daily Digest: {{total_alerts}} alerts, {{critical_count}} critical",
            variables=[
                TemplateVariable(name="total_alerts", description="Total alert count"),
                TemplateVariable(name="critical_count", description="Critical alert count"),
                TemplateVariable(name="high_count", description="High alert count"),
                TemplateVariable(name="medium_count", description="Medium alert count"),
                TemplateVariable(name="low_count", description="Low alert count"),
                TemplateVariable(name="open_items", description="List of open items"),
                TemplateVariable(name="recent_activity", description="List of recent activities"),
            ],
        )

        # System Health Template
        self._default_templates["system_health"] = Template(
            name="System Health",
            notification_type=NotificationType.SYSTEM_HEALTH,
            title_template="🏥 System Health: {{component_name}} — {{status}}",
            body_template="""**Component:** {{component_name}}
**Status:** {{status}}
**Last Check:** {{last_check|format_date("%Y-%m-%d %H:%M:%S")}}

{% if issues %}
**Issues Detected:**
{% for issue in issues %}
- {{issue}}
{% endfor %}
{% endif %}

{% if metrics %}
**Metrics:**
{% for metric in metrics %}
- {{metric}}
{% endfor %}
{% endif %}""",
            summary_template="System health: {{component_name}} is {{status}}",
            variables=[
                TemplateVariable(name="component_name", description="Component name"),
                TemplateVariable(name="status", description="Health status"),
                TemplateVariable(name="last_check", description="Last check timestamp"),
                TemplateVariable(name="issues", description="List of issues", required=False),
                TemplateVariable(name="metrics", description="List of metrics", required=False),
            ],
        )

        # Register all default templates
        for template in self._default_templates.values():
            self._templates[template.id] = template

    def get_default_template(self, notification_type: NotificationType) -> Template | None:
        """Get the default template for a notification type."""
        return self._default_templates.get(notification_type.value)
