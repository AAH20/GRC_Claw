"""Configuration module for GRC Marketing Core."""

from .feature_flags import FeatureFlags, get_feature_flags
from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings", "FeatureFlags", "get_feature_flags"]
