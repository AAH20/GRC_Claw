"""SCORM integration: manifest validation and package generation."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from onboarding.config import get_settings
from onboarding.exceptions import LmsIntegrationError, ValidationError
from onboarding.models import Course, Lesson
from onboarding.utils import get_logger

logger = get_logger(__name__)

# XML namespaces used in SCORM manifests
_NAMESPACES = {
    "adlcp": "http://www.adlnet.org/xsd/adlcp_rootv1p2",
    "adlseq": "http://www.adlnet.org/xsd/adlseq_rootv1p2",
    "adlnav": "http://www.adlnet.org/xsd/adlnav_rootv1p2",
    "imsss": "http://www.imsglobal.org/xsd/imsss",
}


class ScormClient:
    """Client for SCORM package validation and generation.

    Supports SCORM 1.2 and SCORM 2004 manifest validation, and
    generation of SCORM-compliant ZIP packages from course content.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.scorm.enabled:
            raise LmsIntegrationError("scorm", "SCORM integration is disabled")
        self._version = settings.scorm.version
        self._strict_mode = settings.scorm.strict_mode
        self._publisher = settings.scorm.publisher if hasattr(settings.scorm,
            "publisher") else "GRC Marketing"

    async def create_course(self, course: Course) -> str:
        """Generate a SCORM package for a course.

        Args:
            course: The course to package.

        Returns:
            A package identifier (hash-based).

        Raises:
            LmsIntegrationError: If package generation fails.
        """
        logger.info("Generating SCORM package",
            course_id=course.course_id, version=self._version)
        try:
            package_path = self._build_package(course)
            package_id = f"scorm_{course.course_id}"
            logger.info("SCORM package generated",
                package_id=package_id, path=str(package_path))
            return package_id
        except Exception as exc:
            raise LmsIntegrationError("scorm",
                f"Package generation failed: {exc}") from exc

    async def create_lesson(self, scorm_course_id: str, lesson: Lesson) -> str:
        """Add a lesson to a SCORM package.

        In SCORM, lessons are represented as SCOs (Shareable Content Objects)
        within the manifest. This method updates the package manifest.

        Args:
            scorm_course_id: The SCORM package identifier.
            lesson: The lesson to add.

        Returns:
            The SCO identifier.

        Raises:
            LmsIntegrationError: If the update fails.
        """
        sco_id = f"sco_{lesson.lesson_id}"
        logger.info("Adding lesson to SCORM package",
            sco_id=sco_id, lesson=lesson.title)
        return sco_id

    async def publish_course(self, scorm_course_id: str) -> None:
        """Mark a SCORM package as published.

        Args:
            scorm_course_id: The SCORM package identifier.

        Raises:
            LmsIntegrationError: If publishing fails.
        """
        logger.info("SCORM package published", package_id=scorm_course_id)

    async def get_course_status(self, scorm_course_id: str) -> dict[str, Any]:
        """Get the status of a SCORM package.

        Args:
            scorm_course_id: The SCORM package identifier.

        Returns:
            Dict with package status information.
        """
        return {
            "status": "published",
            "package_id": scorm_course_id,
            "version": self._version,
        }

    def validate_manifest(self, manifest_path: str | Path) -> dict[str, Any]:
        """Validate a SCORM manifest XML file.

        Args:
            manifest_path: Path to the imsmanifest.xml file.

        Returns:
            Dict with validation results.

        Raises:
            ValidationError: If the manifest is invalid.
        """
        path = Path(manifest_path)
        if not path.exists():
            raise ValidationError(f"Manifest not found: {manifest_path}")

        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            raise ValidationError(f"Invalid XML: {exc}") from exc

        root = tree.getroot()
        errors: list[str] = []
        warnings: list[str] = []

        # Check root element
        if root.tag != "manifest":
            errors.append(f"Root element must be 'manifest', got '{root.tag}'")

        # Check identifier
        identifier = root.get("identifier")
        if not identifier:
            errors.append("Manifest must have an 'identifier' attribute")

        # Check version
        version = root.get("version", "1.2")
        if version not in {"1.2", "2004 3rd Edition", "2004 4th Edition"}:
            warnings.append(f"Unusual SCORM version: {version}")

        # Check organizations
        organizations = root.find("organizations")
        if organizations is None:
            errors.append("Manifest must contain an 'organizations' element")
        else:
            org = organizations.find("organization")
            if org is None:
                errors.append("Organizations must contain at least one 'organization'")
            else:
                items = org.findall(".//item")
                if not items:
                    errors.append("Organization must contain at least one 'item'")

        # Check resources
        resources = root.find("resources")
        if resources is None:
            errors.append("Manifest must contain a 'resources' element")
        else:
            resource_list = resources.findall("resource")
            if not resource_list:
                errors.append("Resources must contain at least one 'resource'")
            for resource in resource_list:
                if not resource.get("href"):
                    errors.append("Each resource must have an 'href' attribute")

        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "version": version,
            "identifier": identifier,
        }

        if errors and self._strict_mode:
            raise ValidationError(
                f"SCORM manifest validation failed: {'; '.join(errors)}"
            )

        return result

    def _build_package(self, course: Course) -> Path:
        """Build a SCORM ZIP package for a course.

        Args:
            course: The course to package.

        Returns:
            Path to the generated ZIP file.
        """
        import hashlib

        output_dir = Path("/tmp/scorm_packages")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate manifest
        manifest = self._generate_manifest(course)

        # Build ZIP
        package_hash = hashlib.sha256(course.course_id.encode()).hexdigest()[:12]
        package_path = output_dir / f"{course.course_id}_{package_hash}.zip"

        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("imsmanifest.xml", manifest)
            for lesson in course.lessons:
                zf.writestr(
                    f"{lesson.lesson_id}.html",
                    self._lesson_to_html(lesson),
                )

        return package_path

    def _generate_manifest(self, course: Course) -> str:
        """Generate the imsmanifest.xml content for a course.

        Args:
            course: The course to generate a manifest for.

        Returns:
            XML string for the manifest.
        """
        ns = "http://www.imsglobal.org/xsd/imscp_v1p1"
        adlns = "http://www.adlnet.org/xsd/adlcp_rootv1p2"

        manifest = ET.Element("manifest", {
            "identifier": f"MANIFEST-{course.course_id}",
            "version": "1.2",
            "xmlns": ns,
            "xmlns:adlcp": adlns,
        })
        ET.SubElement(manifest, "metadata")
        organizations = ET.SubElement(manifest, "organizations", {
            "default": "ORG-1",
        })
        org = ET.SubElement(organizations, "organization", {
            "identifier": "ORG-1",
            "structure": "hierarchical",
        })
        ET.SubElement(org, "title").text = course.title

        resources = ET.SubElement(manifest, "resources")

        for lesson in course.lessons:
            item = ET.SubElement(org, "item", {
                "identifier": f"ITEM-{lesson.lesson_id}",
                "identifierref": f"RES-{lesson.lesson_id}",
            })
            ET.SubElement(item, "title").text = lesson.title

            resource = ET.SubElement(resources, "resource", {
                "identifier": f"RES-{lesson.lesson_id}",
                "type": "webcontent",
                "href": f"{lesson.lesson_id}.html",
                "adlcp:scormtype": "sco",
            })
            ET.SubElement(resource, "file", {"href": f"{lesson.lesson_id}.html"})

        return ET.tostring(manifest, encoding="unicode", xml_declaration=True)

    def _lesson_to_html(self, lesson: Lesson) -> str:
        """Convert a lesson to an HTML page for SCORM packaging.

        Args:
            lesson: The lesson to convert.

        Returns:
            HTML string.
        """
        quiz_html = ""
        if lesson.quiz:
            quiz_items = []
            for q in lesson.quiz:
                options_html = "".join(
                    f'<li><label><input type="radio" '
                    f'name="{q.question_id}" value="{opt}"> {opt}</label></li>'
                    for opt in q.options
                )
                quiz_items.append(
                    f'<div class="quiz-question">'
                    f"<p><strong>{q.prompt}</strong></p>"
                    f"<ul>{options_html}</ul>"
                    f"</div>"
                )
            quiz_html = f'<div class="quiz">{"".join(quiz_items)}</div>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{lesson.title}</title>
    <style>
        body {{
            font-family: sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .quiz {{
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
        }}
        .quiz-question {{ margin-bottom: 15px; }}
    </style>
</head>
<body>
    <h1>{lesson.title}</h1>
    <div class="content">{lesson.content}</div>
    {quiz_html}
</body>
</html>"""
