"""Configuration module for GRC Marketing Core."""

from .feature_flags import FeatureFlags, get_feature_flags
from .settings import Settings, get_settings

__all__ = ["FeatureFlags", "Settings", "get_feature_flags", "get_settings"]
