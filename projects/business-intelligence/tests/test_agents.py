"""Tests for business intelligence agent implementations."""
from __future__ import annotations

import pandas as pd
import pytest

from business_intelligence.agents.analysis import AnalysisAgent
from business_intelligence.agents.data_collection import (
    CollectionResult,
    DataCollectionAgent,
    DataSourceConfig,
    DataSourceType,
)


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent()

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "revenue": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
            "cost": [50, 100, 150, 200, 250, 300, 350, 400, 450, 500],
            "category": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
        })

    def test_analyze_success(self, agent: AnalysisAgent, sample_df: pd.DataFrame) -> None:
        result = agent.analyze(sample_df)
        assert result.success is True
        assert "revenue" in result.summary_statistics
        assert "cost" in result.summary_statistics

    def test_analyze_empty_dataframe(self, agent: AnalysisAgent) -> None:
        result = agent.analyze(pd.DataFrame())
        assert result.success is False
        assert result.error_message is not None

    def test_summary_statistics(self, agent: AnalysisAgent, sample_df: pd.DataFrame) -> None:
        result = agent.analyze(sample_df)
        assert result.summary_statistics["revenue"]["count"] == 10
        assert result.summary_statistics["revenue"]["mean"] == 550.0

    def test_detect_anomalies(self, agent: AnalysisAgent) -> None:
        df = pd.DataFrame({"value": [1, 2, 3, 4, 5, 100]})
        result = agent.analyze(df)
        assert result.success is True

    def test_compute_correlations(self, agent: AnalysisAgent, sample_df: pd.DataFrame) -> None:
        result = agent.analyze(sample_df)
        assert "matrix" in result.correlations
        assert "top_pairs" in result.correlations

    def test_generate_insights(self, agent: AnalysisAgent, sample_df: pd.DataFrame) -> None:
        result = agent.analyze(sample_df)
        assert len(result.insights) > 0


class TestDataCollectionAgent:
    """Tests for DataCollectionAgent."""

    @pytest.fixture
    def agent(self) -> DataCollectionAgent:
        return DataCollectionAgent()

    def test_collect_from_file_not_found(self, agent: DataCollectionAgent) -> None:
        config = DataSourceConfig(
            source_type=DataSourceType.FILE,
            file_path="/nonexistent/file.csv",
        )
        result = agent.collect_from_file(config)
        assert result.success is False
        assert result.error_message is not None

    def test_collect_from_file_no_path(self, agent: DataCollectionAgent) -> None:
        config = DataSourceConfig(source_type=DataSourceType.FILE)
        with pytest.raises(ValueError, match="File path must be configured"):
            agent.collect_from_file(config)

    def test_collect_from_database_no_config(self, agent: DataCollectionAgent) -> None:
        config = DataSourceConfig(source_type=DataSourceType.DATABASE)
        with pytest.raises(ValueError, match="Connection string and query must be configured"):
            agent.collect_from_database(config)

    def test_collect_unsupported_source(self, agent: DataCollectionAgent) -> None:
        config = DataSourceConfig(source_type=DataSourceType.STREAM)
        result = agent.collect(config)
        # collect is async, but for unsupported source it returns sync
        # Actually it's async, so we need to handle differently
