"""LMS integration modules for Canvas, Moodle, and SCORM."""

from onboarding.integrations.canvas import CanvasClient
from onboarding.integrations.moodle import MoodleClient
from onboarding.integrations.scorm import ScormClient

__all__ = ["CanvasClient", "MoodleClient", "ScormClient"]
