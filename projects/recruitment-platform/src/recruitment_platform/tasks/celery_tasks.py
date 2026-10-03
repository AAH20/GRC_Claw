"""Celery tasks for background processing."""

from __future__ import annotations

import logging
from typing import Any

from celery import Celery

from recruitment_platform.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "recruitment_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def parse_resume_task(self, resume_text: str) -> dict[str, Any]:
    """Background task to parse a resume."""
    try:
        from recruitment_platform.agents.resume_parser.resume_parser_agent import \
            ResumeParserAgent

        agent = ResumeParserAgent()
        # Note: In production, use async_to_sync or run in event loop
        import asyncio

        result = asyncio.run(agent.process({"text": resume_text}))
        return {"success": True, "data": result}
    except Exception as exc:
        logger.error(f"Resume parsing failed: {exc}")
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(bind=True, max_retries=3)
def match_candidates_task(
    self,
    candidates: list[dict[str, Any]],
    job_requirements: dict[str, Any],
) -> dict[str, Any]:
    """Background task to match candidates."""
    try:
        from recruitment_platform.agents.candidate_matcher.bias_aware_ranker import \
            BiasAwareRanker

        agent = BiasAwareRanker()
        import asyncio

        result = asyncio.run(
            agent.process(
                {"candidates": candidates, "job_requirements": job_requirements}
            )
        )
        return {"success": True, "data": result}
    except Exception as exc:
        logger.error(f"Candidate matching failed: {exc}")
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(bind=True, max_retries=3)
def send_notification_task(
    self,
    notification_type: str,
    recipient: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Background task to send notifications."""
    try:
        logger.info(f"Sending {notification_type} notification to {recipient}")
        # Implementation would integrate with email/SMS/push services
        return {"success": True, "message": f"Notification sent to {recipient}"}
    except Exception as exc:
        logger.error(f"Notification failed: {exc}")
        raise self.retry(exc=exc, countdown=300) from exc


@celery_app.task(bind=True, max_retries=3)
def generate_analytics_report_task(
    self,
    report_type: str,
    date_range: dict[str, str],
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Background task to generate analytics reports."""
    try:
        logger.info(f"Generating {report_type} report for {date_range}")
        # Implementation would generate and store reports
        return {"success": True, "report_type": report_type, "status": "completed"}
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        raise self.retry(exc=exc, countdown=300) from exc


@celery_app.task(bind=True, max_retries=3)
def sync_ats_data_task(self, ats_config: dict[str, Any]) -> dict[str, Any]:
    """Background task to sync data with external ATS."""
    try:
        logger.info("Syncing ATS data")
        # Implementation would sync with ATS
        return {"success": True, "synced_records": 0}
    except Exception as exc:
        logger.error(f"ATS sync failed: {exc}")
        raise self.retry(exc=exc, countdown=600) from exc


@celery_app.task(bind=True, max_retries=3)
def cleanup_old_data_task(self, days_to_keep: int = 90) -> dict[str, Any]:
    """Background task to clean up old data."""
    try:
        logger.info(f"Cleaning up data older than {days_to_keep} days")
        # Implementation would clean up old records
        return {"success": True, "deleted_records": 0}
    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        raise self.retry(exc=exc, countdown=3600) from exc
