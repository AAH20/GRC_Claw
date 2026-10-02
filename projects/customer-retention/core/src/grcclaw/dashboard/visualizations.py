"""
Visualization components for GRC_Claw governance dashboard.

Provides chart rendering, heatmap generation, trend visualization,
gauge displays, table formatting, and sparkline generation.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Optional
from collections import defaultdict

from .models import (
    ChartType,
    WidgetType,
    AlertLevel,
    TrendDirection,
    ComplianceStatus,
    RiskLevel,
)


class VisualizationEngine:
    """
    Central visualization engine that orchestrates all rendering components.
    Provides a unified interface for generating visual representations
    of governance data.
    """

    def __init__(self):
        self.chart_renderer = ChartRenderer()
        self.heatmap_renderer = HeatmapRenderer()
        self.trend_renderer = TrendRenderer()
        self.gauge_renderer = GaugeRenderer()
        self.table_renderer = TableRenderer()
        self.sparkline_renderer = SparklineRenderer()

    def render(self, viz_type: str, data: dict[str, Any], config: Optional[dict] = None) -> dict[str, Any]:
        """Route rendering to the appropriate component."""
        config = config or {}
        renderers = {
            "chart": self.chart_renderer.render,
            "heatmap": self.heatmap_renderer.render,
            "trend": self.trend_renderer.render,
            "gauge": self.gauge_renderer.render,
            "table": self.table_renderer.render,
            "sparkline": self.sparkline_renderer.render,
        }
        renderer = renderers.get(viz_type)
        if renderer is None:
            return {"error": f"Unknown visualization type: {viz_type}"}
        return renderer(data, config)

    def render_all(self, dashboard_data: dict[str, Any]) -> dict[str, Any]:
        """Render all visualizations for a dashboard."""
        results = {}
        for viz_type in ["chart", "heatmap", "trend", "gauge", "table", "sparkline"]:
            results[viz_type] = self.render(viz_type, dashboard_data)
        return results


class ChartRenderer:
    """
    Renders chart data for various chart types.
    Produces data structures compatible with popular charting libraries
    (Chart.js, D3.js, Recharts, etc.).
    """

    def render(self, data: dict[str, Any], config: Optional[dict] = None) -> dict[str, Any]:
        """Render chart data based on chart type."""
        config = config or {}
        chart_type = ChartType(config.get("chart_type", "line"))

        renderers = {
            ChartType.LINE: self._render_line,
            ChartType.BAR: self._render_bar,
            ChartType.PIE: self._render_pie,
            ChartType.DOUGHNUT: self._render_doughnut,
            ChartType.AREA: self._render_area,
            ChartType.SCATTER: self._render_scatter,
            ChartType.RADAR: self._render_radar,
            ChartType.BUBBLE: self._render_bubble,
            ChartType.FUNNEL: self._render_funnel,
        }

        renderer = renderers.get(chart_type, self._render_line)
        return renderer(data, config)

    def _render_line(self, data: dict, config: dict) -> dict:
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        return {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": ds.get("label", ""),
                        "data": ds.get("data", []),
                        "borderColor": ds.get("color", "#3b82f6"),
                        "backgroundColor": ds.get("color", "#3b82f6") + "20",
                        "fill": config.get("fill_area", False),
                        "tension": 0.4 if config.get("smooth_lines", True) else 0,
                    }
                    for ds in datasets
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "legend": {"display": config.get("show_legend", True)},
                    "tooltip": {"enabled": config.get("show_tooltips", True)},
                },
                "scales": {
                    "x": {"display": True, "grid": {"display": config.get("show_grid", True)}},
                    "y": {
                        "display": True,
                        "min": config.get("y_axis_min"),
                        "max": config.get("y_axis_max"),
                        "grid": {"display": config.get("show_grid", True)},
                    },
                },
            },
        }

    def _render_bar(self, data: dict, config: dict) -> dict:
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": ds.get("label", ""),
                        "data": ds.get("data", []),
                        "backgroundColor": ds.get("color", "#3b82f6"),
                        "borderRadius": 4,
                    }
                    for ds in datasets
                ],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {"legend": {"display": config.get("show_legend", True)}},
                "scales": {
                    "x": {"stacked": config.get("stacked", False)},
                    "y": {"stacked": config.get("stacked", False)},
                },
            },
        }

    def _render_pie(self, data: dict, config: dict) -> dict:
        return {
            "type": "pie",
            "data": {
                "labels": data.get("labels", []),
                "datasets": [{
                    "data": data.get("values", []),
                    "backgroundColor": data.get("colors", self._default_palette()),
                }],
            },
            "options": {
                "responsive": True,
                "plugins": {"legend": {"position": "right"}},
            },
        }

    def _render_doughnut(self, data: dict, config: dict) -> dict:
        result = self._render_pie(data, config)
        result["type"] = "doughnut"
        result["options"]["cutout"] = "60%"
        return result

    def _render_area(self, data: dict, config: dict) -> dict:
        result = self._render_line(data, {**config, "fill_area": True})
        result["type"] = "line"
        for ds in result["data"]["datasets"]:
            ds["fill"] = True
        return result

    def _render_scatter(self, data: dict, config: dict) -> dict:
        datasets = data.get("datasets", [])
        return {
            "type": "scatter",
            "data": {
                "datasets": [
                    {
                        "label": ds.get("label", ""),
                        "data": [
                            {"x": x, "y": y}
                            for x, y in zip(ds.get("x_data", []), ds.get("y_data", []))
                        ],
                        "backgroundColor": ds.get("color", "#3b82f6"),
                    }
                    for ds in datasets
                ],
            },
            "options": {"responsive": True, "maintainAspectRatio": False},
        }

    def _render_radar(self, data: dict, config: dict) -> dict:
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        return {
            "type": "radar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": ds.get("label", ""),
                        "data": ds.get("data", []),
                        "borderColor": ds.get("color", "#3b82f6"),
                        "backgroundColor": ds.get("color", "#3b82f6") + "30",
                    }
                    for ds in datasets
                ],
            },
            "options": {"responsive": True, "maintainAspectRatio": False},
        }

    def _render_bubble(self, data: dict, config: dict) -> dict:
        datasets = data.get("datasets", [])
        return {
            "type": "bubble",
            "data": {
                "datasets": [
                    {
                        "label": ds.get("label", ""),
                        "data": [
                            {"x": x, "y": y, "r": r}
                            for x, y, r in zip(
                                ds.get("x_data", []),
                                ds.get("y_data", []),
                                ds.get("sizes", []),
                            )
                        ],
                        "backgroundColor": ds.get("color", "#3b82f6") + "80",
                    }
                    for ds in datasets
                ],
            },
            "options": {"responsive": True, "maintainAspectRatio": False},
        }

    def _render_funnel(self, data: dict, config: dict) -> dict:
        labels = data.get("labels", [])
        values = data.get("values", [])
        colors = data.get("colors", self._default_palette())
        total = values[0] if values else 1
        stages = []
        for i, (label, value) in enumerate(zip(labels, values)):
            stages.append({
                "label": label,
                "value": value,
                "pct": round(value / total * 100, 1) if total else 0,
                "color": colors[i % len(colors)],
            })
        return {"type": "funnel", "stages": stages}

    @staticmethod
    def _default_palette() -> list[str]:
        return [
            "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
            "#06b6d4", "#ec4899", "#f97316", "#14b8a6", "#6366f1",
        ]


class HeatmapRenderer:
    """
    Renders heatmap data for risk matrices, compliance grids,
    and domain-category cross-references.
    """

    def render(self, data: dict[str, Any], config: Optional[dict] = None) -> dict[str, Any]:
        """Render heatmap data."""
        config = config or {}
        domains = data.get("domains", [])
        categories = data.get("categories", [])
        matrix = data.get("matrix", [])
        max_value = data.get("max_value", 10)

        # Normalize values to 0-1 range for color mapping
        normalized = []
        for row in matrix:
            norm_row = {"domain": row["domain"], "categories": {}}
            for cat, value in row.get("categories", {}).items():
                norm_row["categories"][cat] = {
                    "value": value,
                    "normalized": round(value / max_value, 3) if max_value else 0,
                    "color": self._value_to_color(value, max_value),
                }
            normalized.append(norm_row)

        return {
            "type": "heatmap",
            "domains": domains,
            "categories": categories,
            "matrix": normalized,
            "max_value": max_value,
            "color_scale": self._generate_color_scale(),
        }

    def _value_to_color(self, value: int, max_value: int) -> str:
        """Map a value to a color on a red-yellow-green scale."""
        if max_value == 0:
            return "#22c55e"
        ratio = value / max_value
        if ratio <= 0.25:
            return "#22c55e"  # Green
        elif ratio <= 0.5:
            return "#84cc16"  # Light green
        elif ratio <= 0.75:
            return "#f59e0b"  # Yellow/Orange
        else:
            return "#ef4444"  # Red

    def _generate_color_scale(self) -> list[dict]:
        """Generate a color scale legend."""
        return [
            {"value": 0, "color": "#22c55e", "label": "Low"},
            {"value": 25, "color": "#84cc16", "label": "Moderate"},
            {"value": 50, "color": "#f59e0b", "label": "Elevated"},
            {"value": 75, "color": "#f97316", "label": "High"},
            {"value": 100, "color": "#ef4444", "label": "Critical"},
        ]


class TrendRenderer:
    """
    Renders trend lines, sparklines, and trend indicators.
    """

    def render(self, data: dict[str, Any], config: Optional[dict] = None) -> dict[str, Any]:
        """Render trend visualization data."""
        config = config or {}
        values = data.get("values", [])
        labels = data.get("labels", [])

        if not values:
            return {"type": "trend", "error": "No data points provided"}

        # Calculate trend statistics
        first_val = values[0]
        last_val = values[-1]
        change = last_val - first_val
        change_pct = (change / first_val * 100) if first_val != 0 else 0

        if change_pct > 5:
            direction = TrendDirection.UP
        elif change_pct < -5:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.FLAT

        # Calculate moving averages
        window = config.get("moving_average_window", 3)
        moving_avg = self._moving_average(values, window)

        # Detect peaks and valleys
        peaks, valleys = self._detect_peaks_valleys(values)

        return {
            "type": "trend",
            "values": values,
            "labels": labels,
            "direction": direction.value,
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "moving_average": moving_avg,
            "peaks": peaks,
            "valleys": valleys,
            "statistics": {
                "mean": round(sum(values) / len(values), 2),
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values),
            },
        }

    def _moving_average(self, values: list[float], window: int) -> list[float]:
        """Calculate simple moving average."""
        if window <= 1 or len(values) < window:
            return values[:]
        result = []
        for i in range(len(values) - window + 1):
            avg = sum(values[i:i + window]) / window
            result.append(round(avg, 2))
        return result

    def _detect_peaks_valleys(self, values: list[float]) -> tuple[list[int], list[int]]:
        """Detect peak and valley indices in the data."""
        peaks = []
        valleys = []
        for i in range(1, len(values) - 1):
            if values[i] > values[i - 1] and values[i] > values[i + 1]:
                peaks.append(i)
            elif values[i] < values[i - 1] and values[i] < values[i + 1]:
                valleys.append(i)
        return peaks, valleys


class GaugeRenderer:
    """
    Renders gauge/meter visualizations for KPI displays.
    """

    def render(self, data: dict[str, Any], config: Optional[dict] = None) -> dict[str, Any]:
        """Render gauge visualization data."""
        config = config or {}
        value = data.get("value", 0)
        min_val = data.get("min", 0)
        max_val = data.get("max", 100)
        zones = data.get("zones", [])

        # Calculate percentage
        pct = ((value - min_val) / (max_val - min_val) * 100) if max_val > min_val else 0
        pct = max(0, min(100, pct))

        # Determine current zone
        current_zone = None
        for zone in zones:
            if zone["min"] <= value <= zone["max"]:
                current_zone = zone
                break

        # Calculate angle for needle (0-180 degrees)
        angle = (pct / 100) * 180

        return {
            "type": "gauge",
            "value": value,
            "percentage": round(pct, 1),
            "angle": round(angle, 1),
            "zones": zones,
            "current_zone": current_zone,
            "color": current_zone["color"] if current_zone else "#6b7280",
            "label": current_zone["label"] if current_zone else "Unknown",
        }


class TableRenderer:
    """
    Renders table data with sorting, filtering, and pagination.
    """

    def render(self, data: dict[str, Any], config: Optional[dict] = None) -> dict[str, Any]:
        """Render table visualization data."""
        config = config or {}
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        total_count = data.get("total_count", len(rows))
        page = data.get("page", 1)
        page_size = data.get("page_size", 25)

        # Apply sorting if specified
        sort_by = config.get("sort_by")
        sort_order = config.get("sort_order", "desc")
        if sort_by and columns:
            col_idx = columns.index(sort_by) if sort_by in columns else -1
            if col_idx >= 0:
                rows = sorted(
                    rows,
                    key=lambda r: r[col_idx] if col_idx < len(r) else "",
                    reverse=(sort_order == "desc"),
                )

        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_rows = rows[start:end]
        total_pages = math.ceil(total_count / page_size) if page_size else 1

        return {
            "type": "table",
            "columns": columns,
            "rows": paginated_rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_count": total_count,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "sortable": config.get("sortable", True),
            "filterable": config.get("filterable", True),
        }


class SparklineRenderer:
    """
    Renders sparkline (inline chart) data for KPI widgets.
    """

    def render(self, data: dict[str, Any], config: Optional[dict] = None) -> dict[str, Any]:
        """Render sparkline visualization data."""
        config = config or {}
        values = data.get("values", [])
        labels = data.get("labels", [])

        if not values:
            return {"type": "sparkline", "error": "No data points"}

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Normalize to 0-100 scale for rendering
        normalized = [round((v - min_val) / range_val * 100, 1) for v in values]

        # Determine trend
        first_val = values[0]
        last_val = values[-1]
        trend = "up" if last_val > first_val else "down" if last_val < first_val else "flat"

        return {
            "type": "sparkline",
            "values": values,
            "normalized": normalized,
            "labels": labels,
            "trend": trend,
            "min": min_val,
            "max": max_val,
            "width": config.get("width", 120),
            "height": config.get("height", 32),
            "color": config.get("color", "#3b82f6"),
        }
