"""Tests for video marketing agents."""

from __future__ import annotations

import pytest

from video_marketing.agents.analytics import (
    AnalyticsAgent,
    AnalyticsError,
    CampaignAnalytics,
    MetricType,
    TimeRange,
    VideoAnalytics,
)
from video_marketing.agents.distribution import (
    Distribution,
    DistributionAgent,
    DistributionError,
    DistributionStatus,
    Platform,
    VideoVisibility,
)
from video_marketing.agents.editing import (
    EditingAgent,
    EditingError,
    EditingProject,
    EditingStatus,
    ExportFormat,
    Resolution,
)
from video_marketing.agents.production import (
    Production,
    ProductionAgent,
    ProductionError,
    ProductionStatus,
    ShotType,
)
from video_marketing.agents.script_generation import (
    ScriptFormat,
    ScriptGenerationAgent,
    ScriptGenerationError,
    Tone,
    VideoScript,
)


# ---------------------------------------------------------------------------
# Script Generation Agent Tests
# ---------------------------------------------------------------------------


class TestScriptGenerationAgent:
    """Tests for ScriptGenerationAgent."""

    @pytest.fixture
    def agent(self) -> ScriptGenerationAgent:
        return ScriptGenerationAgent()

    @pytest.mark.asyncio
    async def test_generate_script_basic(self, agent: ScriptGenerationAgent) -> None:
        script = await agent.generate_script(
            topic="AI in Marketing",
            format=ScriptFormat.TALKING_HEAD,
            tone=Tone.PROFESSIONAL,
            target_duration=120.0,
        )
        assert isinstance(script, VideoScript)
        assert script.title
        assert len(script.sections) > 0
        assert script.total_duration > 0
        assert script.word_count > 0

    @pytest.mark.asyncio
    async def test_generate_script_with_keywords(self, agent: ScriptGenerationAgent) -> None:
        script = await agent.generate_script(
            topic="Python Tutorial",
            keywords=["python", "tutorial", "programming"],
            target_duration=60.0,
        )
        assert "python" in script.keywords
        assert "tutorial" in script.keywords

    @pytest.mark.asyncio
    async def test_generate_script_empty_topic_raises(self, agent: ScriptGenerationAgent) -> None:
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            await agent.generate_script(topic="")

    @pytest.mark.asyncio
    async def test_generate_script_invalid_duration_raises(
        self, agent: ScriptGenerationAgent
    ) -> None:
        with pytest.raises(ValueError, match="Target duration must be positive"):
            await agent.generate_script(topic="Test", target_duration=-10)

    @pytest.mark.asyncio
    async def test_generate_script_all_formats(self, agent: ScriptGenerationAgent) -> None:
        for fmt in ScriptFormat:
            script = await agent.generate_script(topic="Test Topic", format=fmt)
            assert script.format == fmt

    @pytest.mark.asyncio
    async def test_generate_script_all_tones(self, agent: ScriptGenerationAgent) -> None:
        for tone in Tone:
            script = await agent.generate_script(topic="Test Topic", tone=tone)
            assert script.tone == tone

    @pytest.mark.asyncio
    async def test_refine_script(self, agent: ScriptGenerationAgent) -> None:
        script = await agent.generate_script(topic="Test Topic")
        refined = agent.refine_script(script, "Make it more engaging")
        assert refined.metadata.get("refined") is True
        assert refined.metadata.get("feedback") == "Make it more engaging"

    @pytest.mark.asyncio
    async def test_estimate_production_time(self, agent: ScriptGenerationAgent) -> None:
        script = await agent.generate_script(topic="Test", target_duration=120.0)
        estimates = agent.estimate_production_time(script)
        assert "pre_production_hours" in estimates
        assert "filming_hours" in estimates
        assert "editing_hours" in estimates
        assert "post_production_hours" in estimates
        assert "total_hours" in estimates
        assert estimates["total_hours"] > 0

    @pytest.mark.asyncio
    async def test_script_to_dict(self, agent: ScriptGenerationAgent) -> None:
        script = await agent.generate_script(topic="Test Topic")
        data = script.to_dict()
        assert "title" in data
        assert "format" in data
        assert "tone" in data
        assert "sections" in data
        assert "total_duration_seconds" in data
        assert "word_count" in data


# ---------------------------------------------------------------------------
# Production Agent Tests
# ---------------------------------------------------------------------------


class TestProductionAgent:
    """Tests for ProductionAgent."""

    @pytest.fixture
    def agent(self) -> ProductionAgent:
        return ProductionAgent()

    @pytest.mark.asyncio
    async def test_create_production(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(
            title="Test Production",
            script_id="script-123",
            location="Studio A",
            budget=5000.0,
        )
        assert isinstance(production, Production)
        assert production.title == "Test Production"
        assert production.script_id == "script-123"
        assert production.status == ProductionStatus.PENDING
        assert production.budget == 5000.0

    @pytest.mark.asyncio
    async def test_create_production_empty_title_raises(
        self, agent: ProductionAgent
    ) -> None:
        with pytest.raises(ProductionError, match="Production title is required"):
            await agent.create_production(title="")

    @pytest.mark.asyncio
    async def test_get_production(self, agent: ProductionAgent) -> None:
        created = await agent.create_production(title="Test")
        fetched = await agent.get_production(created.id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_production_not_found(self, agent: ProductionAgent) -> None:
        with pytest.raises(ProductionError, match="not found"):
            await agent.get_production("nonexistent-id")

    @pytest.mark.asyncio
    async def test_update_status(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(title="Test")
        updated = await agent.update_status(production.id, ProductionStatus.PRE_PRODUCTION)
        assert updated.status == ProductionStatus.PRE_PRODUCTION

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(title="Test")
        with pytest.raises(ProductionError, match="Invalid status transition"):
            await agent.update_status(production.id, ProductionStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_add_shot(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(title="Test")
        shot = await agent.add_shot(
            production_id=production.id,
            shot_type=ShotType.MEDIUM,
            description="Opening shot",
            duration_seconds=10.0,
        )
        assert shot.description == "Opening shot"
        assert shot.completed is False

    @pytest.mark.asyncio
    async def test_mark_shot_complete(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(title="Test")
        shot = await agent.add_shot(
            production_id=production.id,
            shot_type=ShotType.WIDE,
            description="Test shot",
        )
        completed = await agent.mark_shot_complete(production.id, shot.id, best_take=2)
        assert completed.completed is True
        assert completed.takes == 1
        assert completed.best_take == 2

    @pytest.mark.asyncio
    async def test_completion_percentage(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(title="Test")
        assert production.completion_percentage == 0.0

        shot1 = await agent.add_shot(production.id, ShotType.WIDE, "Shot 1")
        await agent.add_shot(production.id, ShotType.MEDIUM, "Shot 2")
        await agent.mark_shot_complete(production.id, shot1.id)

        updated = await agent.get_production(production.id)
        assert updated.completion_percentage == 50.0

    @pytest.mark.asyncio
    async def test_budget_tracking(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(title="Test", budget=1000.0)
        assert production.is_over_budget is False

        updated = await agent.update_budget(production.id, 1500.0)
        assert updated.is_over_budget is True

    @pytest.mark.asyncio
    async def test_list_productions(self, agent: ProductionAgent) -> None:
        await agent.create_production(title="Prod 1")
        await agent.create_production(title="Prod 2")
        productions = await agent.list_productions()
        assert len(productions) == 2

    @pytest.mark.asyncio
    async def test_generate_shot_list(self, agent: ProductionAgent) -> None:
        production = await agent.create_production(title="Test")
        await agent.add_shot(production.id, ShotType.WIDE, "Shot 1", duration_seconds=5.0)
        await agent.add_shot(production.id, ShotType.CLOSE_UP, "Shot 2", duration_seconds=3.0)

        shot_list = await agent.generate_shot_list(production.id)
        assert len(shot_list) == 2
        assert shot_list[0]["shot_number"] == 1
        assert shot_list[1]["shot_number"] == 2


# ---------------------------------------------------------------------------
# Editing Agent Tests
# ---------------------------------------------------------------------------


class TestEditingAgent:
    """Tests for EditingAgent."""

    @pytest.fixture
    def agent(self) -> EditingAgent:
        return EditingAgent()

    @pytest.mark.asyncio
    async def test_create_project(self, agent: EditingAgent) -> None:
        project = await agent.create_project(
            title="Test Edit",
            production_id="prod-123",
            editor="Editor A",
        )
        assert isinstance(project, EditingProject)
        assert project.title == "Test Edit"
        assert project.status == EditingStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_project_empty_title_raises(self, agent: EditingAgent) -> None:
        with pytest.raises(EditingError, match="title is required"):
            await agent.create_project(title="")

    @pytest.mark.asyncio
    async def test_update_status(self, agent: EditingAgent) -> None:
        project = await agent.create_project(title="Test")
        updated = await agent.update_status(project.id, EditingStatus.INGESTING)
        assert updated.status == EditingStatus.INGESTING

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, agent: EditingAgent) -> None:
        project = await agent.create_project(title="Test")
        with pytest.raises(EditingError, match="Invalid status transition"):
            await agent.update_status(project.id, EditingStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_add_edit_decision(self, agent: EditingAgent) -> None:
        project = await agent.create_project(title="Test")
        decision = await agent.add_edit_decision(
            project_id=project.id,
            timestamp=10.5,
            duration=5.0,
            edit_type="cut",
            description="Cut to b-roll",
        )
        assert decision.edit_type == "cut"
        assert decision.timestamp == 10.5

    @pytest.mark.asyncio
    async def test_add_export_preset(self, agent: EditingAgent) -> None:
        project = await agent.create_project(title="Test")
        preset = await agent.add_export_preset(
            project_id=project.id,
            name="YouTube 1080p",
            format=ExportFormat.MP4_H264,
            resolution=Resolution.FHD_1080P,
            fps=30.0,
        )
        assert preset.name == "YouTube 1080p"
        assert preset.format == ExportFormat.MP4_H264

    @pytest.mark.asyncio
    async def test_add_export(self, agent: EditingAgent) -> None:
        project = await agent.create_project(title="Test")
        preset = await agent.add_export_preset(project.id, "Test Preset")
        export = await agent.add_export(
            project_id=project.id,
            preset_id=preset.id,
            output_url="https://example.com/video.mp4",
            file_size_bytes=1024000,
        )
        assert export["output_url"] == "https://example.com/video.mp4"
        assert export["file_size_bytes"] == 1024000

    @pytest.mark.asyncio
    async def test_generate_edl(self, agent: EditingAgent) -> None:
        project = await agent.create_project(title="Test")
        await agent.add_edit_decision(project.id, 0.0, 5.0, "cut", "Cut 1")
        await agent.add_edit_decision(project.id, 5.0, 3.0, "transition", "Fade")

        edl = await agent.generate_edl(project.id)
        assert len(edl) == 2
        assert edl[0]["event_number"] == 1
        assert edl[1]["event_number"] == 2

    @pytest.mark.asyncio
    async def test_list_projects(self, agent: EditingAgent) -> None:
        await agent.create_project(title="Edit 1")
        await agent.create_project(title="Edit 2")
        projects = await agent.list_projects()
        assert len(projects) == 2


# ---------------------------------------------------------------------------
# Distribution Agent Tests
# ---------------------------------------------------------------------------


class TestDistributionAgent:
    """Tests for DistributionAgent."""

    @pytest.fixture
    def agent(self) -> DistributionAgent:
        return DistributionAgent()

    @pytest.mark.asyncio
    async def test_distribute_to_platforms(self, agent: DistributionAgent) -> None:
        distributions = await agent.distribute(
            video_id="video-123",
            platforms=[Platform.YOUTUBE, Platform.TIKTOK],
            title="Test Video",
        )
        assert len(distributions) == 2
        assert all(isinstance(d, Distribution) for d in distributions)

    @pytest.mark.asyncio
    async def test_distribute_empty_video_id_raises(self, agent: DistributionAgent) -> None:
        with pytest.raises(DistributionError, match="Video ID is required"):
            await agent.distribute(video_id="", platforms=[Platform.YOUTUBE])

    @pytest.mark.asyncio
    async def test_distribute_no_platforms_raises(self, agent: DistributionAgent) -> None:
        with pytest.raises(DistributionError, match="At least one platform"):
            await agent.distribute(video_id="video-123", platforms=[])

    @pytest.mark.asyncio
    async def test_update_status(self, agent: DistributionAgent) -> None:
        distributions = await agent.distribute(
            video_id="video-123",
            platforms=[Platform.YOUTUBE],
        )
        dist_id = distributions[0].id
        updated = await agent.update_status(
            dist_id,
            DistributionStatus.PUBLISHED,
            platform_video_id="yt-123",
            platform_url="https://youtube.com/watch?v=yt-123",
        )
        assert updated.status == DistributionStatus.PUBLISHED
        assert updated.is_published is True
        assert updated.platform_video_id == "yt-123"

    @pytest.mark.asyncio
    async def test_retry_failed_distribution(self, agent: DistributionAgent) -> None:
        distributions = await agent.distribute(
            video_id="video-123",
            platforms=[Platform.YOUTUBE],
        )
        dist_id = distributions[0].id
        await agent.update_status(dist_id, DistributionStatus.FAILED, error_message="Timeout")

        retried = await agent.retry(dist_id)
        assert retried.status == DistributionStatus.PENDING
        assert retried.error_message == ""

    @pytest.mark.asyncio
    async def test_retry_exceeds_max_retries(self, agent: DistributionAgent) -> None:
        distributions = await agent.distribute(
            video_id="video-123",
            platforms=[Platform.YOUTUBE],
        )
        dist_id = distributions[0].id

        for _ in range(3):
            await agent.update_status(dist_id, DistributionStatus.FAILED, error_message="Error")
            try:
                await agent.retry(dist_id)
            except DistributionError:
                pass

        await agent.update_status(dist_id, DistributionStatus.FAILED, error_message="Error")
        with pytest.raises(DistributionError, match="cannot be retried"):
            await agent.retry(dist_id)

    @pytest.mark.asyncio
    async def test_list_distributions(self, agent: DistributionAgent) -> None:
        await agent.distribute(video_id="v1", platforms=[Platform.YOUTUBE])
        await agent.distribute(video_id="v2", platforms=[Platform.TIKTOK])

        all_dists = await agent.list_distributions()
        assert len(all_dists) == 2

        v1_dists = await agent.list_distributions(video_id="v1")
        assert len(v1_dists) == 1

    @pytest.mark.asyncio
    async def test_get_platform_stats(self, agent: DistributionAgent) -> None:
        distributions = await agent.distribute(
            video_id="video-123",
            platforms=[Platform.YOUTUBE, Platform.TIKTOK],
        )
        await agent.update_status(distributions[0].id, DistributionStatus.PUBLISHED)

        stats = await agent.get_platform_stats("video-123")
        assert stats["total_platforms"] == 2
        assert stats["published"] == 1
        assert "youtube" in stats["platforms"]
        assert "tiktok" in stats["platforms"]

    @pytest.mark.asyncio
    async def test_configure_platform(self, agent: DistributionAgent) -> None:
        from video_marketing.agents.distribution import PlatformConfig

        config = PlatformConfig(
            platform=Platform.YOUTUBE,
            enabled=True,
            api_key="test-key",
        )
        agent.configure_platform(config)


# ---------------------------------------------------------------------------
# Analytics Agent Tests
# ---------------------------------------------------------------------------


class TestAnalyticsAgent:
    """Tests for AnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> AnalyticsAgent:
        return AnalyticsAgent()

    @pytest.mark.asyncio
    async def test_record_video_analytics(self, agent: AnalyticsAgent) -> None:
        analytics = VideoAnalytics(
            video_id="video-123",
            platform="youtube",
            views=1000,
            likes=50,
            comments=10,
            shares=5,
        )
        recorded = await agent.record_video_analytics(analytics)
        assert recorded.video_id == "video-123"
        assert recorded.views == 1000

    @pytest.mark.asyncio
    async def test_record_analytics_empty_video_id_raises(
        self, agent: AnalyticsAgent
    ) -> None:
        analytics = VideoAnalytics(video_id="")
        with pytest.raises(AnalyticsError, match="Video ID is required"):
            await agent.record_video_analytics(analytics)

    @pytest.mark.asyncio
    async def test_get_video_analytics(self, agent: AnalyticsAgent) -> None:
        analytics = VideoAnalytics(video_id="video-123", platform="youtube", views=500)
        await agent.record_video_analytics(analytics)

        fetched = await agent.get_video_analytics("video-123", "youtube")
        assert fetched.views == 500

    @pytest.mark.asyncio
    async def test_get_video_analytics_not_found(self, agent: AnalyticsAgent) -> None:
        with pytest.raises(AnalyticsError, match="not found"):
            await agent.get_video_analytics("nonexistent", "youtube")

    @pytest.mark.asyncio
    async def test_record_metric(self, agent: AnalyticsAgent) -> None:
        point = await agent.record_metric(
            video_id="video-123",
            metric_type=MetricType.VIEWS,
            value=100.0,
            platform="youtube",
        )
        assert point.value == 100.0
        assert point.metric_type == MetricType.VIEWS

    @pytest.mark.asyncio
    async def test_get_metrics(self, agent: AnalyticsAgent) -> None:
        await agent.record_metric("video-123", MetricType.VIEWS, 100.0, "youtube")
        await agent.record_metric("video-123", MetricType.VIEWS, 200.0, "youtube")
        await agent.record_metric("video-123", MetricType.LIKES, 10.0, "youtube")

        views = await agent.get_metrics("video-123", MetricType.VIEWS, "youtube")
        assert len(views) == 2

        likes = await agent.get_metrics("video-123", MetricType.LIKES, "youtube")
        assert len(likes) == 1

    @pytest.mark.asyncio
    async def test_aggregate_campaign(self, agent: AnalyticsAgent) -> None:
        await agent.record_video_analytics(
            VideoAnalytics(video_id="v1", platform="youtube", views=1000, likes=50)
        )
        await agent.record_video_analytics(
            VideoAnalytics(video_id="v2", platform="tiktok", views=2000, likes=100)
        )

        campaign = await agent.aggregate_campaign(
            campaign_id="campaign-1",
            video_ids=["v1", "v2"],
        )
        assert isinstance(campaign, CampaignAnalytics)
        assert campaign.total_views == 3000
        assert campaign.total_likes == 150

    @pytest.mark.asyncio
    async def test_aggregate_campaign_empty_videos_raises(
        self, agent: AnalyticsAgent
    ) -> None:
        with pytest.raises(AnalyticsError, match="At least one video ID"):
            await agent.aggregate_campaign(campaign_id="c1", video_ids=[])

    @pytest.mark.asyncio
    async def test_generate_report(self, agent: AnalyticsAgent) -> None:
        await agent.record_metric("video-123", MetricType.VIEWS, 1000.0, "youtube")
        await agent.record_metric("video-123", MetricType.LIKES, 50.0, "youtube")

        report = await agent.generate_report("video-123", TimeRange.LAST_7_DAYS)
        assert report["video_id"] == "video-123"
        assert report["time_range"] == "7d"
        assert "summary" in report
        assert "insights" in report
        assert "recommendations" in report

    @pytest.mark.asyncio
    async def test_compare_videos(self, agent: AnalyticsAgent) -> None:
        await agent.record_video_analytics(
            VideoAnalytics(video_id="v1", platform="youtube", views=1000)
        )
        await agent.record_video_analytics(
            VideoAnalytics(video_id="v2", platform="youtube", views=2000)
        )

        comparison = await agent.compare_videos(["v1", "v2"], MetricType.VIEWS)
        assert comparison["metric"] == "views"
        assert len(comparison["videos"]) == 2
        assert comparison["videos"][0]["video_id"] == "v2"

    @pytest.mark.asyncio
    async def test_engagement_rate_calculation(self) -> None:
        analytics = VideoAnalytics(
            video_id="v1",
            views=1000,
            likes=50,
            comments=10,
            shares=5,
        )
        # engagement_rate = (50 + 10 + 5) / 1000 * 100 = 6.5%
        assert analytics.engagement_rate == pytest.approx(6.5)

    @pytest.mark.asyncio
    async def test_engagement_rate_zero_views(self) -> None:
        analytics = VideoAnalytics(video_id="v1", views=0, likes=0, comments=0, shares=0)
        assert analytics.engagement_rate == 0.0
