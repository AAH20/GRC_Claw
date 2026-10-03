"""Tests for export module."""

from __future__ import annotations

import pytest

from recruitment_platform.export.export_service import ExportService


class TestExportService:
    """Test export service."""

    @pytest.mark.asyncio
    async def test_export_csv(self) -> None:
        """Test CSV export."""
        service = ExportService()
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        result = await service.export_to_csv(data)
        assert "name,age" in result
        assert "John,30" in result

    @pytest.mark.asyncio
    async def test_export_json(self) -> None:
        """Test JSON export."""
        service = ExportService()
        data = [{"name": "John"}]
        result = await service.export_to_json(data)
        assert '"name": "John"' in result

    @pytest.mark.asyncio
    async def test_export_xml(self) -> None:
        """Test XML export."""
        service = ExportService()
        data = [{"name": "John"}]
        result = await service.export_to_xml(data)
        assert "<records>" in result
        assert "<name>John</name>" in result

    @pytest.mark.asyncio
    async def test_export_empty_csv(self) -> None:
        """Test CSV export with empty data."""
        service = ExportService()
        result = await service.export_to_csv([])
        assert result == ""
