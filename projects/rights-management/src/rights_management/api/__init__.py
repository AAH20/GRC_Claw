"""API routers for the rights-management service."""

from rights_management.api import infringement, licenses, takedown, usage, validation

__all__ = ["infringement", "licenses", "takedown", "usage", "validation"]
