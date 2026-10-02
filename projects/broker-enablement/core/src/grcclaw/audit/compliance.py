"""
Compliance tracking — framework control mapping, assessment, and scoring.

Maps controls to frameworks (SOC 2, ISO 27001, NIST, PCI DSS, etc.),
tracks compliance status, and computes compliance scores.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .models import (
    AuditEngagement,
    AuditStatus,
    AuditType,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ControlStatus,
    ControlType,
    Finding,
    FindingSeverity,
    FindingStatus,
    OverallOpinion,
    Workpaper,
)


# ---------------------------------------------------------------------------
# Framework control catalog
# ---------------------------------------------------------------------------

FRAMEWORK_CONTROLS: dict[str, list[dict[str, str]]] = {
    "soc2": [
        {"id": "CC1.1", "title": "Control Environment", "type": "preventive"},
        {"id": "CC1.2", "title": "Integrity and Ethical Values", "type": "preventive"},
        {"id": "CC1.3", "title": "Board Independence", "type": "preventive"},
        {"id": "CC1.4", "title": "Organizational Structure", "type": "preventive"},
        {"id": "CC1.5", "title": "Hiring and Retention", "type": "preventive"},
        {"id": "CC2.1", "title": "Communication and Information", "type": "preventive"},
        {"id": "CC2.2", "title": "Internal Communication", "type": "preventive"},
        {"id": "CC2.3", "title": "External Communication", "type": "preventive"},
        {"id": "CC3.1", "title": "Risk Assessment Process", "type": "preventive"},
        {"id": "CC3.2", "title": "Risk Identification", "type": "detective"},
        {"id": "CC3.3", "title": "Risk Analysis", "type": "detective"},
        {"id": "CC3.4", "title": "Risk Response", "type": "corrective"},
        {"id": "CC4.1", "title": "Monitoring Activities", "type": "detective"},
        {"id": "CC4.2", "title": "Internal Control Monitoring", "type": "detective"},
        {"id": "CC5.1", "title": "Control Activities", "type": "preventive"},
        {"id": "CC5.2", "title": "Control Selection", "type": "preventive"},
        {"id": "CC5.3", "title": "Control Deployment", "type": "preventive"},
        {"id": "CC6.1", "title": "Logical Access Controls", "type": "preventive"},
        {"id": "CC6.2", "title": "User Access Provisioning", "type": "preventive"},
        {"id": "CC6.3", "title": "User Access Deprovisioning", "type": "preventive"},
        {"id": "CC6.4", "title": "Privileged Access", "type": "preventive"},
        {"id": "CC6.5", "title": "Access Reviews", "type": "detective"},
        {"id": "CC6.6", "title": "Authentication", "type": "preventive"},
        {"id": "CC6.7", "title": "Network Security", "type": "preventive"},
        {"id": "CC6.8", "title": "Data Transmission Security", "type": "preventive"},
        {"id": "CC7.1", "title": "Vulnerability Management", "type": "detective"},
        {"id": "CC7.2", "title": "Security Incident Detection", "type": "detective"},
        {"id": "CC7.3", "title": "Incident Response", "type": "corrective"},
        {"id": "CC7.4", "title": "Incident Recovery", "type": "recovery"},
        {"id": "CC7.5", "title": "Incident Reporting", "type": "detective"},
        {"id": "CC8.1", "title": "Change Management", "type": "preventive"},
        {"id": "CC8.2", "title": "Change Testing", "type": "preventive"},
        {"id": "CC8.3", "title": "Change Approval", "type": "preventive"},
        {"id": "CC9.1", "title": "Business Continuity", "type": "recovery"},
        {"id": "CC9.2", "title": "Disaster Recovery", "type": "recovery"},
        {"id": "CC9.3", "title": "Backup and Restoration", "type": "recovery"},
    ],
    "iso27001": [
        {"id": "A.5.1", "title": "Information Security Policies", "type": "preventive"},
        {"id": "A.5.2", "title": "Information Security Roles", "type": "preventive"},
        {"id": "A.5.3", "title": "Segregation of Duties", "type": "preventive"},
        {"id": "A.5.4", "title": "Management Responsibilities", "type": "preventive"},
        {"id": "A.5.5", "title": "Contact with Authorities", "type": "preventive"},
        {"id": "A.5.6", "title": "Information Security in Projects", "type": "preventive"},
        {"id": "A.5.7", "title": "Threat Intelligence", "type": "detective"},
        {"id": "A.5.8", "title": "Information Security in Supplier Relationships", "type": "preventive"},
        {"id": "A.5.9", "title": "Inventory of Information Assets", "type": "preventive"},
        {"id": "A.5.10", "title": "Acceptable Use of Information", "type": "preventive"},
        {"id": "A.5.11", "title": "Return of Assets", "type": "preventive"},
        {"id": "A.5.12", "title": "Classification of Information", "type": "preventive"},
        {"id": "A.5.13", "title": "Labelling of Information", "type": "preventive"},
        {"id": "A.5.14", "title": "Information Transfer", "type": "preventive"},
        {"id": "A.5.15", "title": "Access Control", "type": "preventive"},
        {"id": "A.5.16", "title": "Identity Management", "type": "preventive"},
        {"id": "A.5.17", "title": "Authentication Information", "type": "preventive"},
        {"id": "A.5.18", "title": "Access Rights", "type": "preventive"},
        {"id": "A.5.19", "title": "Information Security in Supplier Relationships", "type": "preventive"},
        {"id": "A.5.20", "title": "Addressing Information Security in Supplier Relationships", "type": "preventive"},
        {"id": "A.5.21", "title": "Managing Information Security in the ICT Supply Chain", "type": "preventive"},
        {"id": "A.5.22", "title": "Monitoring, Review and Change Management of Supplier Services", "type": "detective"},
        {"id": "A.5.23", "title": "Information Security for Use of Cloud Services", "type": "preventive"},
        {"id": "A.5.24", "title": "Information Security Incident Management Planning", "type": "corrective"},
        {"id": "A.5.25", "title": "Assessment and Decision on Information Security Events", "type": "detective"},
        {"id": "A.5.26", "title": "Response to Information Security Incidents", "type": "corrective"},
        {"id": "A.5.27", "title": "Learning from Information Security Incidents", "type": "preventive"},
        {"id": "A.5.28", "title": "Collection of Evidence", "type": "detective"},
        {"id": "A.5.29", "title": "Information Security During Disruption", "type": "recovery"},
        {"id": "A.5.30", "title": "ICT Readiness for Business Continuity", "type": "recovery"},
        {"id": "A.5.31", "title": "Legal, Statutory, Regulatory and Contractual Requirements", "type": "preventive"},
        {"id": "A.5.32", "title": "Intellectual Property Rights", "type": "preventive"},
        {"id": "A.5.33", "title": "Protection of Records", "type": "preventive"},
        {"id": "A.5.34", "title": "Privacy and Protection of PII", "type": "preventive"},
        {"id": "A.5.35", "title": "Independent Review of Information Security", "type": "detective"},
        {"id": "A.5.36", "title": "Compliance with Policies, Rules and Standards", "type": "detective"},
        {"id": "A.5.37", "title": "Documented Operating Procedures", "type": "preventive"},
    ],
    "nist_csf": [
        {"id": "ID.AM-1", "title": "Asset Management - Hardware", "type": "preventive"},
        {"id": "ID.AM-2", "title": "Asset Management - Software", "type": "preventive"},
        {"id": "ID.AM-3", "title": "Asset Management - Data Flows", "type": "preventive"},
        {"id": "ID.AM-4", "title": "Asset Management - External Systems", "type": "preventive"},
        {"id": "ID.AM-5", "title": "Asset Management - Inventory", "type": "preventive"},
        {"id": "ID.BE-1", "title": "Business Environment - Mission", "type": "preventive"},
        {"id": "ID.BE-2", "title": "Business Environment - Stakeholders", "type": "preventive"},
        {"id": "ID.BE-3", "title": "Business Environment - Critical Infrastructure", "type": "preventive"},
        {"id": "ID.BE-4", "title": "Business Environment - Supply Chain", "type": "preventive"},
        {"id": "ID.BE-5", "title": "Business Environment - Dependencies", "type": "preventive"},
        {"id": "ID.GV-1", "title": "Governance - Policies", "type": "preventive"},
        {"id": "ID.GV-2", "title": "Governance - Roles and Responsibilities", "type": "preventive"},
        {"id": "ID.GV-3", "title": "Governance - Legal and Regulatory", "type": "preventive"},
        {"id": "ID.GV-4", "title": "Governance - Risk Management Strategy", "type": "preventive"},
        {"id": "ID.RA-1", "title": "Risk Assessment - Vulnerability Identification", "type": "detective"},
        {"id": "ID.RA-2", "title": "Risk Assessment - Threat Identification", "type": "detective"},
        {"id": "ID.RA-3", "title": "Risk Assessment - Impact Analysis", "type": "detective"},
        {"id": "ID.RA-4", "title": "Risk Assessment - Risk Response", "type": "corrective"},
        {"id": "ID.RA-5", "title": "Risk Assessment - Risk Register", "type": "preventive"},
        {"id": "ID.RA-6", "title": "Risk Assessment - Supply Chain Risk", "type": "detective"},
        {"id": "ID.SC-1", "title": "Supply Chain Risk Management", "type": "preventive"},
        {"id": "ID.SC-2", "title": "Supplier Identification", "type": "preventive"},
        {"id": "ID.SC-3", "title": "Supplier Contracts", "type": "preventive"},
        {"id": "ID.SC-4", "title": "Supplier Monitoring", "type": "detective"},
        {"id": "ID.SC-5", "title": "Supplier Audits", "type": "detective"},
        {"id": "PR.AC-1", "title": "Identity Management - Authentication", "type": "preventive"},
        {"id": "PR.AC-2", "title": "Identity Management - Authorization", "type": "preventive"},
        {"id": "PR.AC-3", "title": "Identity Management - Access Revocation", "type": "preventive"},
        {"id": "PR.AC-4", "title": "Identity Management - Remote Access", "type": "preventive"},
        {"id": "PR.AC-5", "title": "Identity Management - Least Privilege", "type": "preventive"},
        {"id": "PR.AC-6", "title": "Identity Management - Authentication Strength", "type": "preventive"},
        {"id": "PR.AT-1", "title": "Awareness and Training", "type": "preventive"},
        {"id": "PR.AT-2", "title": "Role-Based Training", "type": "preventive"},
        {"id": "PR.AT-3", "title": "Social Engineering Awareness", "type": "preventive"},
        {"id": "PR.AT-4", "title": "Executive Awareness", "type": "preventive"},
        {"id": "PR.DS-1", "title": "Data Security - Data at Rest", "type": "preventive"},
        {"id": "PR.DS-2", "title": "Data Security - Data in Transit", "type": "preventive"},
        {"id": "PR.DS-3", "title": "Data Security - Data Handling", "type": "preventive"},
        {"id": "PR.DS-4", "title": "Data Security - Data Disposal", "type": "preventive"},
        {"id": "PR.DS-5", "title": "Data Security - Data Leakage", "type": "detective"},
        {"id": "PR.IP-1", "title": "Information Protection - Baseline Configuration", "type": "preventive"},
        {"id": "PR.IP-2", "title": "Information Protection - System Development", "type": "preventive"},
        {"id": "PR.IP-3", "title": "Information Protection - Configuration Change Control", "type": "preventive"},
        {"id": "PR.IP-4", "title": "Information Protection - Backups", "type": "recovery"},
        {"id": "PR.IP-5", "title": "Information Protection - Policy Compliance", "type": "detective"},
        {"id": "PR.IP-6", "title": "Information Protection - Vulnerability Management", "type": "detective"},
        {"id": "PR.IP-7", "title": "Information Protection - Protection Processes", "type": "preventive"},
        {"id": "PR.IP-8", "title": "Information Protection - Protection Technology", "type": "preventive"},
        {"id": "PR.IP-9", "title": "Information Protection - Response Plans", "type": "corrective"},
        {"id": "PR.IP-10", "title": "Information Protection - Recovery Plans", "type": "recovery"},
        {"id": "PR.MA-1", "title": "Maintenance - Timely Maintenance", "type": "preventive"},
        {"id": "PR.MA-2", "title": "Maintenance - Maintenance Tools", "type": "preventive"},
        {"id": "PR.PT-1", "title": "Protective Technology - Audit Logs", "type": "detective"},
        {"id": "PR.PT-2", "title": "Protective Technology - Removable Media", "type": "preventive"},
        {"id": "PR.PT-3", "title": "Protective Technology - Access Control", "type": "preventive"},
        {"id": "PR.PT-4", "title": "Protective Technology - Wireless Security", "type": "preventive"},
        {"id": "PR.PT-5", "title": "Protective Technology - Cryptographic Protections", "type": "preventive"},
        {"id": "DE.AE-1", "title": "Anomalies and Events - Baseline of Network Operations", "type": "detective"},
        {"id": "DE.AE-2", "title": "Anomalies and Events - Event Data Analysis", "type": "detective"},
        {"id": "DE.AE-3", "title": "Anomalies and Events - Event Detection", "type": "detective"},
        {"id": "DE.AE-4", "title": "Anomalies and Events - Incident Impact", "type": "detective"},
        {"id": "DE.AE-5", "title": "Anomalies and Events - Alert Thresholds", "type": "detective"},
        {"id": "DE.CM-1", "title": "Continuous Monitoring - Network Monitoring", "type": "detective"},
        {"id": "DE.CM-2", "title": "Continuous Monitoring - Host Monitoring", "type": "detective"},
        {"id": "DE.CM-3", "title": "Continuous Monitoring - Application Monitoring", "type": "detective"},
        {"id": "DE.CM-4", "title": "Continuous Monitoring - External Service Monitoring", "type": "detective"},
        {"id": "DE.CM-5", "title": "Continuous Monitoring - Monitoring Personnel", "type": "detective"},
        {"id": "DE.CM-6", "title": "Continuous Monitoring - Alert Management", "type": "detective"},
        {"id": "DE.CM-7", "title": "Continuous Monitoring - Vulnerability Scans", "type": "detective"},
        {"id": "DE.CM-8", "title": "Continuous Monitoring - Software Integrity", "type": "detective"},
        {"id": "DE.DP-1", "title": "Detection Processes - Roles and Responsibilities", "type": "preventive"},
        {"id": "DE.DP-2", "title": "Detection Processes - Compliance", "type": "detective"},
        {"id": "DE.DP-3", "title": "Detection Processes - Testing", "type": "detective"},
        {"id": "DE.DP-4", "title": "Detection Processes - Event Analysis", "type": "detective"},
        {"id": "DE.DP-5", "title": "Detection Processes - Continuous Improvement", "type": "preventive"},
        {"id": "RS.RP-1", "title": "Response Planning - Response Plan", "type": "corrective"},
        {"id": "RS.CO-1", "title": "Response - Communications", "type": "corrective"},
        {"id": "RS.CO-2", "title": "Response - Reporting", "type": "corrective"},
        {"id": "RS.CO-3", "title": "Response - Coordination", "type": "corrective"},
        {"id": "RS.CO-4", "title": "Response - Voluntary Information Sharing", "type": "corrective"},
        {"id": "RS.AN-1", "title": "Response - Analysis", "type": "detective"},
        {"id": "RS.AN-2", "title": "Response - Forensics", "type": "detective"},
        {"id": "RS.AN-3", "title": "Response - Incident Categorization", "type": "detective"},
        {"id": "RS.AN-4", "title": "Response - Process Improvement", "type": "preventive"},
        {"id": "RS.MI-1", "title": "Response - Mitigation", "type": "corrective"},
        {"id": "RS.MI-2", "title": "Response - Eradication", "type": "corrective"},
        {"id": "RS.MI-3", "title": "Response - Recovery", "type": "recovery"},
        {"id": "RS.IM-1", "title": "Response - Lessons Learned", "type": "preventive"},
        {"id": "RS.IM-2", "title": "Response - Response Plan Updates", "type": "preventive"},
        {"id": "RC.RP-1", "title": "Recovery Planning - Recovery Plan", "type": "recovery"},
        {"id": "RC.IM-1", "title": "Recovery - Lessons Learned", "type": "preventive"},
        {"id": "RC.IM-2", "title": "Recovery - Recovery Plan Updates", "type": "preventive"},
    ],
    "pci_dss": [
        {"id": "1.1", "title": "Firewall Configuration Standards", "type": "preventive"},
        {"id": "1.2", "title": "Network Security Controls", "type": "preventive"},
        {"id": "1.3", "title": "Network Segmentation", "type": "preventive"},
        {"id": "1.4", "title": "Personal Firewall", "type": "preventive"},
        {"id": "1.5", "title": "Security Policies", "type": "preventive"},
        {"id": "2.1", "title": "Vendor Defaults", "type": "preventive"},
        {"id": "2.2", "title": "Configuration Standards", "type": "preventive"},
        {"id": "2.3", "title": "Encryption of Administrative Access", "type": "preventive"},
        {"id": "2.4", "title": "Inventory of System Components", "type": "preventive"},
        {"id": "2.5", "title": "Security Policies for All System Components", "type": "preventive"},
        {"id": "2.6", "title": "Shared Hosting Providers", "type": "preventive"},
        {"id": "3.1", "title": "Data Retention", "type": "preventive"},
        {"id": "3.2", "title": "Sensitive Authentication Data Storage", "type": "preventive"},
        {"id": "3.3", "title": "Masking PAN", "type": "preventive"},
        {"id": "3.4", "title": "PAN Encryption", "type": "preventive"},
        {"id": "3.5", "title": "Cryptographic Key Management", "type": "preventive"},
        {"id": "3.6", "title": "Key Management Procedures", "type": "preventive"},
        {"id": "3.7", "title": "Key Custodian Acknowledgment", "type": "preventive"},
        {"id": "4.1", "title": "Strong Cryptography for Transmission", "type": "preventive"},
        {"id": "4.2", "title": "End-User Messaging", "type": "preventive"},
        {"id": "5.1", "title": "Anti-Malware", "type": "detective"},
        {"id": "5.2", "title": "Anti-Malware Updates", "type": "detective"},
        {"id": "5.3", "title": "Anti-Malware Scanning", "type": "detective"},
        {"id": "5.4", "title": "Anti-Malware on Portable Media", "type": "detective"},
        {"id": "6.1", "title": "Vulnerability Management Process", "type": "detective"},
        {"id": "6.2", "title": "Security Patches", "type": "preventive"},
        {"id": "6.3", "title": "Software Security Patches", "type": "preventive"},
        {"id": "6.4", "title": "Change Control", "type": "preventive"},
        {"id": "6.5", "title": "Common Vulnerabilities", "type": "preventive"},
        {"id": "6.6", "title": "Web Application Firewalls", "type": "preventive"},
        {"id": "7.1", "title": "Access Control - Need to Know", "type": "preventive"},
        {"id": "7.2", "title": "Access Control - Default Deny", "type": "preventive"},
        {"id": "7.3", "title": "Access Control - Review", "type": "detective"},
        {"id": "8.1", "title": "User Identification", "type": "preventive"},
        {"id": "8.2", "title": "Authentication", "type": "preventive"},
        {"id": "8.3", "title": "Multi-Factor Authentication", "type": "preventive"},
        {"id": "8.4", "title": "Authentication Credentials", "type": "preventive"},
        {"id": "8.5", "title": "Identification Management", "type": "preventive"},
        {"id": "8.6", "title": "Service Provider Authentication", "type": "preventive"},
        {"id": "8.7", "title": "Database Access", "type": "preventive"},
        {"id": "8.8", "title": "Authentication for Third Parties", "type": "preventive"},
        {"id": "9.1", "title": "Physical Access Restrictions", "type": "preventive"},
        {"id": "9.2", "title": "Physical Access Controls", "type": "preventive"},
        {"id": "9.3", "title": "Physical Access for Visitors", "type": "preventive"},
        {"id": "9.4", "title": "Media Storage", "type": "preventive"},
        {"id": "9.5", "title": "Media Transportation", "type": "preventive"},
        {"id": "9.6", "title": "Media Disposal", "type": "preventive"},
        {"id": "9.7", "title": "Media Destruction", "type": "preventive"},
        {"id": "9.8", "title": "Removable Media", "type": "preventive"},
        {"id": "9.9", "title": "Point-of-Interaction Devices", "type": "preventive"},
        {"id": "10.1", "title": "Audit Logs", "type": "detective"},
        {"id": "10.2", "title": "Audit Log Coverage", "type": "detective"},
        {"id": "10.3", "title": "Audit Log Content", "type": "detective"},
        {"id": "10.4", "title": "Audit Log Time Synchronization", "type": "detective"},
        {"id": "10.5", "title": "Audit Log Protection", "type": "preventive"},
        {"id": "10.6", "title": "Audit Log Review", "type": "detective"},
        {"id": "10.7", "title": "Audit Log Retention", "type": "preventive"},
        {"id": "11.1", "title": "Security Testing", "type": "detective"},
        {"id": "11.2", "title": "Vulnerability Scans", "type": "detective"},
        {"id": "11.3", "title": "Penetration Testing", "type": "detective"},
        {"id": "11.4", "title": "Intrusion Detection", "type": "detective"},
        {"id": "11.5", "title": "Change Detection", "type": "detective"},
        {"id": "11.6", "title": "Security Testing Documentation", "type": "detective"},
        {"id": "12.1", "title": "Security Policy", "type": "preventive"},
        {"id": "12.2", "title": "Risk Assessment", "type": "detective"},
        {"id": "12.3", "title": "Usage Policies", "type": "preventive"},
        {"id": "12.4", "title": "Information Security Responsibilities", "type": "preventive"},
        {"id": "12.5", "title": "Security Management", "type": "preventive"},
        {"id": "12.6", "title": "Security Awareness Program", "type": "preventive"},
        {"id": "12.7", "title": "Personnel Screening", "type": "preventive"},
        {"id": "12.8", "title": "Service Provider Management", "type": "preventive"},
        {"id": "12.9", "title": "Service Provider Compliance", "type": "detective"},
        {"id": "12.10", "title": "Incident Response Plan", "type": "corrective"},
        {"id": "12.11", "title": "Key Management", "type": "preventive"},
    ],
    "gdpr": [
        {"id": "Art.5", "title": "Principles Relating to Processing", "type": "preventive"},
        {"id": "Art.6", "title": "Lawfulness of Processing", "type": "preventive"},
        {"id": "Art.7", "title": "Conditions for Consent", "type": "preventive"},
        {"id": "Art.8", "title": "Child's Consent", "type": "preventive"},
        {"id": "Art.9", "title": "Special Categories of Data", "type": "preventive"},
        {"id": "Art.10", "title": "Data Relating to Criminal Convictions", "type": "preventive"},
        {"id": "Art.11", "title": "Processing Not Requiring Identification", "type": "preventive"},
        {"id": "Art.12", "title": "Transparent Information", "type": "preventive"},
        {"id": "Art.13", "title": "Information to Data Subject", "type": "preventive"},
        {"id": "Art.14", "title": "Information Where Data Not Collected from Subject", "type": "preventive"},
        {"id": "Art.15", "title": "Right of Access", "type": "preventive"},
        {"id": "Art.16", "title": "Right to Rectification", "type": "corrective"},
        {"id": "Art.17", "title": "Right to Erasure", "type": "corrective"},
        {"id": "Art.18", "title": "Right to Restriction of Processing", "type": "preventive"},
        {"id": "Art.19", "title": "Notification Obligation", "type": "preventive"},
        {"id": "Art.20", "title": "Right to Data Portability", "type": "preventive"},
        {"id": "Art.21", "title": "Right to Object", "type": "preventive"},
        {"id": "Art.22", "title": "Automated Decision-Making", "type": "preventive"},
        {"id": "Art.23", "title": "Restrictions", "type": "preventive"},
        {"id": "Art.24", "title": "Responsibility of Controller", "type": "preventive"},
        {"id": "Art.25", "title": "Data Protection by Design and Default", "type": "preventive"},
        {"id": "Art.26", "title": "Joint Controllers", "type": "preventive"},
        {"id": "Art.27", "title": "Representatives of Controllers", "type": "preventive"},
        {"id": "Art.28", "title": "Processor", "type": "preventive"},
        {"id": "Art.29", "title": "Processing Under Authority of Processor", "type": "preventive"},
        {"id": "Art.30", "title": "Records of Processing Activities", "type": "detective"},
        {"id": "Art.31", "title": "Cooperation with Supervisory Authority", "type": "preventive"},
        {"id": "Art.32", "title": "Security of Processing", "type": "preventive"},
        {"id": "Art.33", "title": "Notification of Personal Data Breach", "type": "corrective"},
        {"id": "Art.34", "title": "Communication of Personal Data Breach", "type": "corrective"},
        {"id": "Art.35", "title": "Data Protection Impact Assessment", "type": "detective"},
        {"id": "Art.36", "title": "Prior Consultation", "type": "preventive"},
        {"id": "Art.37", "title": "Designation of Data Protection Officer", "type": "preventive"},
        {"id": "Art.38", "title": "Position of Data Protection Officer", "type": "preventive"},
        {"id": "Art.39", "title": "Tasks of Data Protection Officer", "type": "preventive"},
        {"id": "Art.40", "title": "Codes of Conduct", "type": "preventive"},
        {"id": "Art.41", "title": "Monitoring of Approved Codes", "type": "detective"},
        {"id": "Art.42", "title": "Certification", "type": "preventive"},
        {"id": "Art.43", "title": "Certification Bodies", "type": "preventive"},
        {"id": "Art.44", "title": "General Principle for Transfers", "type": "preventive"},
        {"id": "Art.45", "title": "Transfers on Basis of Adequacy Decision", "type": "preventive"},
        {"id": "Art.46", "title": "Transfers Subject to Appropriate Safeguards", "type": "preventive"},
        {"id": "Art.47", "title": "Binding Corporate Rules", "type": "preventive"},
        {"id": "Art.48", "title": "Transfers Not Authorized by Union Law", "type": "preventive"},
        {"id": "Art.49", "title": "Derogations for Specific Situations", "type": "preventive"},
        {"id": "Art.50", "title": "International Cooperation", "type": "preventive"},
    ],
    "hipaa": [
        {"id": "164.308(a)(1)", "title": "Security Management Process", "type": "preventive"},
        {"id": "164.308(a)(2)", "title": "Assigned Security Responsibility", "type": "preventive"},
        {"id": "164.308(a)(3)", "title": "Workforce Security", "type": "preventive"},
        {"id": "164.308(a)(4)", "title": "Information Access Management", "type": "preventive"},
        {"id": "164.308(a)(5)", "title": "Security Awareness and Training", "type": "preventive"},
        {"id": "164.308(a)(6)", "title": "Security Incident Procedures", "type": "corrective"},
        {"id": "164.308(a)(7)", "title": "Contingency Plan", "type": "recovery"},
        {"id": "164.308(a)(8)", "title": "Evaluation", "type": "detective"},
        {"id": "164.308(b)", "title": "Business Associate Contracts", "type": "preventive"},
        {"id": "164.310(a)", "title": "Facility Access Controls", "type": "preventive"},
        {"id": "164.310(b)", "title": "Workstation Use", "type": "preventive"},
        {"id": "164.310(c)", "title": "Workstation Security", "type": "preventive"},
        {"id": "164.310(d)", "title": "Device and Media Controls", "type": "preventive"},
        {"id": "164.312(a)", "title": "Access Control", "type": "preventive"},
        {"id": "164.312(b)", "title": "Audit Controls", "type": "detective"},
        {"id": "164.312(c)", "title": "Integrity", "type": "preventive"},
        {"id": "164.312(d)", "title": "Person or Entity Authentication", "type": "preventive"},
        {"id": "164.312(e)", "title": "Transmission Security", "type": "preventive"},
        {"id": "164.314(a)", "title": "Privacy Rule Compliance", "type": "preventive"},
        {"id": "164.314(b)", "title": "Business Associate Provisions", "type": "preventive"},
        {"id": "164.316(a)", "title": "Policies and Procedures", "type": "preventive"},
        {"id": "164.316(b)", "title": "Documentation", "type": "preventive"},
        {"id": "164.530(a)", "title": "Safeguards", "type": "preventive"},
        {"id": "164.530(b)", "title": "Privacy Official", "type": "preventive"},
        {"id": "164.530(c)", "title": "Complaints", "type": "corrective"},
        {"id": "164.530(d)", "title": "Refraining from Retaliatory Acts", "type": "preventive"},
        {"id": "164.530(e)", "title": "Waiver of Rights", "type": "preventive"},
        {"id": "164.530(f)", "title": "Policies and Procedures", "type": "preventive"},
        {"id": "164.530(g)", "title": "Documentation", "type": "preventive"},
        {"id": "164.530(h)", "title": "Group Health Plans", "type": "preventive"},
        {"id": "164.530(i)", "title": "Genetic Information", "type": "preventive"},
        {"id": "164.530(j)", "title": "Marketing", "type": "preventive"},
    ],
}


class ComplianceTracker:
    """
    Tracks compliance controls, assessments, and scores across frameworks.

    Features:
    - Framework control catalog with pre-built control sets
    - Control status tracking and assessment workflow
    - Compliance scoring (0-100)
    - Finding-to-control mapping
    - Audit engagement management
    - Workpaper tracking
    - SQLite persistence
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._lock = threading.RLock()
        self._controls: dict[str, ComplianceControl] = {}
        self._assessments: dict[str, ComplianceAssessment] = {}
        self._audits: dict[str, AuditEngagement] = {}
        self._findings: dict[str, Finding] = {}
        self._workpapers: dict[str, Workpaper] = {}
        self._framework_controls: dict[str, list[str]] = defaultdict(list)

        if storage_path:
            self._storage_path = Path(storage_path)
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_storage()
        else:
            self._storage_path = None
            self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def _init_storage(self) -> None:
        """Initialize SQLite storage."""
        self._conn = sqlite3.connect(str(self._storage_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS controls (
                control_id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                control_identifier TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                control_type TEXT NOT NULL,
                status TEXT NOT NULL,
                owner TEXT,
                assessor TEXT,
                assessment_date TEXT,
                next_assessment_date TEXT,
                evidence_ids TEXT,
                finding_ids TEXT,
                risk_ids TEXT,
                compensating_controls TEXT,
                notes TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_controls_framework ON controls(framework);
            CREATE INDEX IF NOT EXISTS idx_controls_status ON controls(status);

            CREATE TABLE IF NOT EXISTS assessments (
                assessment_id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                assessment_name TEXT NOT NULL,
                status TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                assessor TEXT,
                total_controls INTEGER DEFAULT 0,
                compliant_controls INTEGER DEFAULT 0,
                partially_compliant_controls INTEGER DEFAULT 0,
                non_compliant_controls INTEGER DEFAULT 0,
                not_assessed_controls INTEGER DEFAULT 0,
                not_applicable_controls INTEGER DEFAULT 0,
                compliance_score REAL DEFAULT 0,
                control_ids TEXT,
                finding_ids TEXT,
                report_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_assessments_framework ON assessments(framework);

            CREATE TABLE IF NOT EXISTS audits (
                audit_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                audit_type TEXT NOT NULL,
                status TEXT NOT NULL,
                framework TEXT,
                scope TEXT,
                objectives TEXT,
                lead_auditor TEXT,
                team TEXT,
                start_date TEXT,
                end_date TEXT,
                fieldwork_start TEXT,
                fieldwork_end TEXT,
                report_date TEXT,
                control_ids TEXT,
                finding_ids TEXT,
                evidence_ids TEXT,
                workpaper_ids TEXT,
                report_id TEXT,
                overall_opinion TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_audits_status ON audits(status);
            CREATE INDEX IF NOT EXISTS idx_audits_framework ON audits(framework);

            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                audit_id TEXT,
                control_id TEXT,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                root_cause TEXT,
                impact TEXT,
                recommendation TEXT,
                remediation TEXT,
                remediation_owner TEXT,
                due_date TEXT,
                remediated_at TEXT,
                verified_at TEXT,
                verified_by TEXT,
                evidence_ids TEXT,
                risk_ids TEXT,
                capa_ids TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);
            CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
            CREATE INDEX IF NOT EXISTS idx_findings_audit ON findings(audit_id);

            CREATE TABLE IF NOT EXISTS workpapers (
                workpaper_id TEXT PRIMARY KEY,
                audit_id TEXT,
                control_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                procedure TEXT,
                conclusion TEXT,
                preparer TEXT,
                reviewer TEXT,
                preparation_date TEXT,
                review_date TEXT,
                evidence_ids TEXT,
                finding_ids TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_workpapers_audit ON workpapers(audit_id);
        """)
        self._conn.commit()
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Load all data from SQLite storage."""
        if not self._conn:
            return

        cursor = self._conn.execute("SELECT * FROM controls")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            control = ComplianceControl(
                control_id=d["control_id"],
                framework=ComplianceFramework(d["framework"]),
                control_identifier=d["control_identifier"],
                title=d["title"],
                description=d["description"] or "",
                control_type=ControlType(d["control_type"]),
                status=ControlStatus(d["status"]),
                owner=d["owner"],
                assessor=d["assessor"],
                assessment_date=d["assessment_date"],
                next_assessment_date=d["next_assessment_date"],
                evidence_ids=json.loads(d["evidence_ids"]) if d["evidence_ids"] else [],
                finding_ids=json.loads(d["finding_ids"]) if d["finding_ids"] else [],
                risk_ids=json.loads(d["risk_ids"]) if d["risk_ids"] else [],
                compensating_controls=json.loads(d["compensating_controls"]) if d["compensating_controls"] else [],
                notes=json.loads(d["notes"]) if d["notes"] else [],
                tags=json.loads(d["tags"]) if d["tags"] else [],
                created_at=d["created_at"],
                updated_at=d["updated_at"],
                metadata=json.loads(d["metadata"]) if d["metadata"] else {},
            )
            self._controls[control.control_id] = control
            self._framework_controls[control.framework.value].append(control.control_id)

        cursor = self._conn.execute("SELECT * FROM assessments")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            assessment = ComplianceAssessment(
                assessment_id=d["assessment_id"],
                framework=ComplianceFramework(d["framework"]),
                assessment_name=d["assessment_name"],
                status=AuditStatus(d["status"]),
                start_date=d["start_date"],
                end_date=d["end_date"],
                assessor=d["assessor"],
                total_controls=d["total_controls"],
                compliant_controls=d["compliant_controls"],
                partially_compliant_controls=d["partially_compliant_controls"],
                non_compliant_controls=d["non_compliant_controls"],
                not_assessed_controls=d["not_assessed_controls"],
                not_applicable_controls=d["not_applicable_controls"],
                compliance_score=d["compliance_score"],
                control_ids=json.loads(d["control_ids"]) if d["control_ids"] else [],
                finding_ids=json.loads(d["finding_ids"]) if d["finding_ids"] else [],
                report_id=d["report_id"],
                created_at=d["created_at"],
                updated_at=d["updated_at"],
                metadata=json.loads(d["metadata"]) if d["metadata"] else {},
            )
            self._assessments[assessment.assessment_id] = assessment

        cursor = self._conn.execute("SELECT * FROM audits")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            audit = AuditEngagement(
                audit_id=d["audit_id"],
                name=d["name"],
                audit_type=AuditType(d["audit_type"]),
                status=AuditStatus(d["status"]),
                framework=ComplianceFramework(d["framework"]) if d["framework"] else None,
                scope=json.loads(d["scope"]) if d["scope"] else [],
                objectives=json.loads(d["objectives"]) if d["objectives"] else [],
                lead_auditor=d["lead_auditor"],
                team=json.loads(d["team"]) if d["team"] else [],
                start_date=d["start_date"],
                end_date=d["end_date"],
                fieldwork_start=d["fieldwork_start"],
                fieldwork_end=d["fieldwork_end"],
                report_date=d["report_date"],
                control_ids=json.loads(d["control_ids"]) if d["control_ids"] else [],
                finding_ids=json.loads(d["finding_ids"]) if d["finding_ids"] else [],
                evidence_ids=json.loads(d["evidence_ids"]) if d["evidence_ids"] else [],
                workpaper_ids=json.loads(d["workpaper_ids"]) if d["workpaper_ids"] else [],
                report_id=d["report_id"],
                overall_opinion=OverallOpinion(d["overall_opinion"]) if d["overall_opinion"] else None,
                created_at=d["created_at"],
                updated_at=d["updated_at"],
                metadata=json.loads(d["metadata"]) if d["metadata"] else {},
            )
            self._audits[audit.audit_id] = audit

        cursor = self._conn.execute("SELECT * FROM findings")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            finding = Finding(
                finding_id=d["finding_id"],
                audit_id=d["audit_id"],
                control_id=d["control_id"],
                severity=FindingSeverity(d["severity"]),
                status=FindingStatus(d["status"]),
                title=d["title"],
                description=d["description"] or "",
                root_cause=d["root_cause"],
                impact=d["impact"],
                recommendation=d["recommendation"],
                remediation=d["remediation"],
                remediation_owner=d["remediation_owner"],
                due_date=d["due_date"],
                remediated_at=d["remediated_at"],
                verified_at=d["verified_at"],
                verified_by=d["verified_by"],
                evidence_ids=json.loads(d["evidence_ids"]) if d["evidence_ids"] else [],
                risk_ids=json.loads(d["risk_ids"]) if d["risk_ids"] else [],
                capa_ids=json.loads(d["capa_ids"]) if d["capa_ids"] else [],
                created_at=d["created_at"],
                updated_at=d["updated_at"],
                metadata=json.loads(d["metadata"]) if d["metadata"] else {},
            )
            self._findings[finding.finding_id] = finding

        cursor = self._conn.execute("SELECT * FROM workpapers")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            wp = Workpaper(
                workpaper_id=d["workpaper_id"],
                audit_id=d["audit_id"],
                control_id=d["control_id"],
                title=d["title"],
                description=d["description"],
                procedure=d["procedure"],
                conclusion=d["conclusion"],
                preparer=d["preparer"],
                reviewer=d["reviewer"],
                preparation_date=d["preparation_date"],
                review_date=d["review_date"],
                evidence_ids=json.loads(d["evidence_ids"]) if d["evidence_ids"] else [],
                finding_ids=json.loads(d["finding_ids"]) if d["finding_ids"] else [],
                created_at=d["created_at"],
                updated_at=d["updated_at"],
                metadata=json.loads(d["metadata"]) if d["metadata"] else {},
            )
            self._workpapers[wp.workpaper_id] = wp

    def _persist_control(self, control: ComplianceControl) -> None:
        """Persist a control to storage."""
        if not self._conn:
            return
        self._conn.execute(
            """INSERT OR REPLACE INTO controls VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                control.control_id,
                control.framework.value,
                control.control_identifier,
                control.title,
                control.description,
                control.control_type.value,
                control.status.value,
                control.owner,
                control.assessor,
                control.assessment_date,
                control.next_assessment_date,
                json.dumps(control.evidence_ids),
                json.dumps(control.finding_ids),
                json.dumps(control.risk_ids),
                json.dumps(control.compensating_controls),
                json.dumps(control.notes),
                json.dumps(control.tags),
                control.created_at,
                control.updated_at,
                json.dumps(control.metadata),
            ),
        )
        self._conn.commit()

    def _persist_assessment(self, assessment: ComplianceAssessment) -> None:
        """Persist an assessment to storage."""
        if not self._conn:
            return
        self._conn.execute(
            """INSERT OR REPLACE INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                assessment.assessment_id,
                assessment.framework.value,
                assessment.assessment_name,
                assessment.status.value,
                assessment.start_date,
                assessment.end_date,
                assessment.assessor,
                assessment.total_controls,
                assessment.compliant_controls,
                assessment.partially_compliant_controls,
                assessment.non_compliant_controls,
                assessment.not_assessed_controls,
                assessment.not_applicable_controls,
                assessment.compliance_score,
                json.dumps(assessment.control_ids),
                json.dumps(assessment.finding_ids),
                assessment.report_id,
                assessment.created_at,
                assessment.updated_at,
                json.dumps(assessment.metadata),
            ),
        )
        self._conn.commit()

    def _persist_audit(self, audit: AuditEngagement) -> None:
        """Persist an audit to storage."""
        if not self._conn:
            return
        self._conn.execute(
            """INSERT OR REPLACE INTO audits VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                audit.audit_id,
                audit.name,
                audit.audit_type.value,
                audit.status.value,
                audit.framework.value if audit.framework else None,
                json.dumps(audit.scope),
                json.dumps(audit.objectives),
                audit.lead_auditor,
                json.dumps(audit.team),
                audit.start_date,
                audit.end_date,
                audit.fieldwork_start,
                audit.fieldwork_end,
                audit.report_date,
                json.dumps(audit.control_ids),
                json.dumps(audit.finding_ids),
                json.dumps(audit.evidence_ids),
                json.dumps(audit.workpaper_ids),
                audit.report_id,
                audit.overall_opinion.value if audit.overall_opinion else None,
                audit.created_at,
                audit.updated_at,
                json.dumps(audit.metadata),
            ),
        )
        self._conn.commit()

    def _persist_finding(self, finding: Finding) -> None:
        """Persist a finding to storage."""
        if not self._conn:
            return
        self._conn.execute(
            """INSERT OR REPLACE INTO findings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                finding.finding_id,
                finding.audit_id,
                finding.control_id,
                finding.severity.value,
                finding.status.value,
                finding.title,
                finding.description,
                finding.root_cause,
                finding.impact,
                finding.recommendation,
                finding.remediation,
                finding.remediation_owner,
                finding.due_date,
                finding.remediated_at,
                finding.verified_at,
                finding.verified_by,
                json.dumps(finding.evidence_ids),
                json.dumps(finding.risk_ids),
                json.dumps(finding.capa_ids),
                finding.created_at,
                finding.updated_at,
                json.dumps(finding.metadata),
            ),
        )
        self._conn.commit()

    def _persist_workpaper(self, wp: Workpaper) -> None:
        """Persist a workpaper to storage."""
        if not self._conn:
            return
        self._conn.execute(
            """INSERT OR REPLACE INTO workpapers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                wp.workpaper_id,
                wp.audit_id,
                wp.control_id,
                wp.title,
                wp.description,
                wp.procedure,
                wp.conclusion,
                wp.preparer,
                wp.reviewer,
                wp.preparation_date,
                wp.review_date,
                json.dumps(wp.evidence_ids),
                json.dumps(wp.finding_ids),
                wp.created_at,
                wp.updated_at,
                json.dumps(wp.metadata),
            ),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Framework controls
    # ------------------------------------------------------------------

    def load_framework_controls(self, framework: ComplianceFramework) -> list[ComplianceControl]:
        """
        Load the standard control catalog for a framework.

        Creates control records for each control in the framework's catalog
        if they don't already exist.
        """
        with self._lock:
            framework_key = framework.value
            catalog = FRAMEWORK_CONTROLS.get(framework_key, [])
            controls = []

            for entry in catalog:
                # Check if control already exists
                existing = None
                for cid in self._framework_controls.get(framework_key, []):
                    ctrl = self._controls.get(cid)
                    if ctrl and ctrl.control_identifier == entry["id"]:
                        existing = ctrl
                        break

                if existing:
                    controls.append(existing)
                else:
                    control = ComplianceControl(
                        framework=framework,
                        control_identifier=entry["id"],
                        title=entry["title"],
                        control_type=ControlType(entry["type"]),
                        status=ControlStatus.NOT_ASSESSED,
                    )
                    self._controls[control.control_id] = control
                    self._framework_controls[framework_key].append(control.control_id)
                    self._persist_control(control)
                    controls.append(control)

            return controls

    def get_framework_control_count(self, framework: ComplianceFramework) -> int:
        """Get the number of controls in a framework catalog."""
        return len(FRAMEWORK_CONTROLS.get(framework.value, []))

    # ------------------------------------------------------------------
    # Control management
    # ------------------------------------------------------------------

    def create_control(
        self,
        framework: ComplianceFramework,
        control_identifier: str,
        title: str,
        description: str = "",
        control_type: ControlType = ControlType.PREVENTIVE,
        owner: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> ComplianceControl:
        """Create a new compliance control."""
        with self._lock:
            control = ComplianceControl(
                framework=framework,
                control_identifier=control_identifier,
                title=title,
                description=description,
                control_type=control_type,
                owner=owner,
                tags=tags or [],
            )
            self._controls[control.control_id] = control
            self._framework_controls[framework.value].append(control.control_id)
            self._persist_control(control)
            return control

    def get_control(self, control_id: str) -> Optional[ComplianceControl]:
        """Get a control by ID."""
        return self._controls.get(control_id)

    def get_control_by_identifier(
        self, framework: ComplianceFramework, identifier: str
    ) -> Optional[ComplianceControl]:
        """Get a control by its framework identifier (e.g., 'CC6.1')."""
        for cid in self._framework_controls.get(framework.value, []):
            ctrl = self._controls.get(cid)
            if ctrl and ctrl.control_identifier == identifier:
                return ctrl
        return None

    def list_controls(
        self,
        framework: Optional[ComplianceFramework] = None,
        status: Optional[ControlStatus] = None,
        control_type: Optional[ControlType] = None,
        owner: Optional[str] = None,
    ) -> list[ComplianceControl]:
        """List controls with optional filters."""
        controls = list(self._controls.values())
        if framework:
            controls = [c for c in controls if c.framework == framework]
        if status:
            controls = [c for c in controls if c.status == status]
        if control_type:
            controls = [c for c in controls if c.control_type == control_type]
        if owner:
            controls = [c for c in controls if c.owner == owner]
        return controls

    def update_control_status(
        self,
        control_id: str,
        status: ControlStatus,
        assessor: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[ComplianceControl]:
        """Update a control's assessment status."""
        with self._lock:
            control = self._controls.get(control_id)
            if not control:
                return None
            control.status = status
            control.assessor = assessor or control.assessor
            control.assessment_date = datetime.now(timezone.utc).isoformat()
            control.updated_at = datetime.now(timezone.utc).isoformat()
            if notes:
                control.notes.append(notes)
            self._persist_control(control)
            return control

    def link_evidence_to_control(self, control_id: str, evidence_id: str) -> bool:
        """Link evidence to a control."""
        with self._lock:
            control = self._controls.get(control_id)
            if not control:
                return False
            if evidence_id not in control.evidence_ids:
                control.evidence_ids.append(evidence_id)
                control.updated_at = datetime.now(timezone.utc).isoformat()
                self._persist_control(control)
            return True

    def link_finding_to_control(self, control_id: str, finding_id: str) -> bool:
        """Link a finding to a control."""
        with self._lock:
            control = self._controls.get(control_id)
            if not control:
                return False
            if finding_id not in control.finding_ids:
                control.finding_ids.append(finding_id)
                control.updated_at = datetime.now(timezone.utc).isoformat()
                self._persist_control(control)
            return True

    # ------------------------------------------------------------------
    # Assessment management
    # ------------------------------------------------------------------

    def create_assessment(
        self,
        framework: ComplianceFramework,
        assessment_name: str,
        assessor: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ComplianceAssessment:
        """Create a new compliance assessment."""
        with self._lock:
            # Load framework controls if not already loaded
            self.load_framework_controls(framework)

            control_ids = list(self._framework_controls.get(framework.value, []))
            assessment = ComplianceAssessment(
                framework=framework,
                assessment_name=assessment_name,
                assessor=assessor,
                start_date=start_date,
                end_date=end_date,
                control_ids=control_ids,
            )
            self._assessments[assessment.assessment_id] = assessment
            self._persist_assessment(assessment)
            return assessment

    def get_assessment(self, assessment_id: str) -> Optional[ComplianceAssessment]:
        """Get an assessment by ID."""
        return self._assessments.get(assessment_id)

    def list_assessments(
        self,
        framework: Optional[ComplianceFramework] = None,
        status: Optional[AuditStatus] = None,
    ) -> list[ComplianceAssessment]:
        """List assessments with optional filters."""
        assessments = list(self._assessments.values())
        if framework:
            assessments = [a for a in assessments if a.framework == framework]
        if status:
            assessments = [a for a in assessments if a.status == status]
        return assessments

    def update_assessment_status(
        self, assessment_id: str, status: AuditStatus
    ) -> Optional[ComplianceAssessment]:
        """Update an assessment's status."""
        with self._lock:
            assessment = self._assessments.get(assessment_id)
            if not assessment:
                return None
            assessment.status = status
            assessment.updated_at = datetime.now(timezone.utc).isoformat()
            if status == AuditStatus.CLOSED and not assessment.end_date:
                assessment.end_date = datetime.now(timezone.utc).isoformat()
            self._persist_assessment(assessment)
            return assessment

    def compute_compliance_score(self, assessment_id: str) -> Optional[float]:
        """
        Compute compliance score for an assessment.

        Score = (compliant + 0.5 * partially_compliant) / (total - not_applicable) * 100
        """
        with self._lock:
            assessment = self._assessments.get(assessment_id)
            if not assessment:
                return None

            applicable = (
                assessment.total_controls - assessment.not_applicable_controls
            )
            if applicable == 0:
                return 0.0

            score = (
                (assessment.compliant_controls + 0.5 * assessment.partially_compliant_controls)
                / applicable
                * 100
            )
            assessment.compliance_score = round(score, 2)
            assessment.updated_at = datetime.now(timezone.utc).isoformat()
            self._persist_assessment(assessment)
            return assessment.compliance_score

    def refresh_assessment_counts(self, assessment_id: str) -> Optional[ComplianceAssessment]:
        """Recalculate control status counts for an assessment."""
        with self._lock:
            assessment = self._assessments.get(assessment_id)
            if not assessment:
                return None

            counts = defaultdict(int)
            for cid in assessment.control_ids:
                ctrl = self._controls.get(cid)
                if ctrl:
                    counts[ctrl.status] += 1

            assessment.total_controls = len(assessment.control_ids)
            assessment.compliant_controls = counts[ControlStatus.COMPLIANT]
            assessment.partially_compliant_controls = counts[ControlStatus.PARTIALLY_COMPLIANT]
            assessment.non_compliant_controls = counts[ControlStatus.NON_COMPLIANT]
            assessment.not_assessed_controls = counts[ControlStatus.NOT_ASSESSED]
            assessment.not_applicable_controls = counts[ControlStatus.NOT_APPLICABLE]
            assessment.updated_at = datetime.now(timezone.utc).isoformat()
            self._persist_assessment(assessment)
            self.compute_compliance_score(assessment_id)
            return assessment

    # ------------------------------------------------------------------
    # Audit engagement management
    # ------------------------------------------------------------------

    def create_audit(
        self,
        name: str,
        audit_type: AuditType = AuditType.INTERNAL,
        framework: Optional[ComplianceFramework] = None,
        scope: Optional[list[str]] = None,
        objectives: Optional[list[str]] = None,
        lead_auditor: Optional[str] = None,
        team: Optional[list[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AuditEngagement:
        """Create a new audit engagement."""
        with self._lock:
            audit = AuditEngagement(
                name=name,
                audit_type=audit_type,
                framework=framework,
                scope=scope or [],
                objectives=objectives or [],
                lead_auditor=lead_auditor,
                team=team or [],
                start_date=start_date,
                end_date=end_date,
            )
            self._audits[audit.audit_id] = audit
            self._persist_audit(audit)
            return audit

    def get_audit(self, audit_id: str) -> Optional[AuditEngagement]:
        """Get an audit by ID."""
        return self._audits.get(audit_id)

    def list_audits(
        self,
        status: Optional[AuditStatus] = None,
        audit_type: Optional[AuditType] = None,
        framework: Optional[ComplianceFramework] = None,
    ) -> list[AuditEngagement]:
        """List audits with optional filters."""
        audits = list(self._audits.values())
        if status:
            audits = [a for a in audits if a.status == status]
        if audit_type:
            audits = [a for a in audits if a.audit_type == audit_type]
        if framework:
            audits = [a for a in audits if a.framework == framework]
        return audits

    def transition_audit_status(
        self, audit_id: str, new_status: AuditStatus
    ) -> Optional[AuditEngagement]:
        """Transition an audit to a new status."""
        with self._lock:
            audit = self._audits.get(audit_id)
            if not audit:
                return None
            audit.status = new_status
            audit.updated_at = datetime.now(timezone.utc).isoformat()

            now = datetime.now(timezone.utc).isoformat()
            if new_status == AuditStatus.FIELDWORK and not audit.fieldwork_start:
                audit.fieldwork_start = now
            elif new_status == AuditStatus.REPORTING and not audit.fieldwork_end:
                audit.fieldwork_end = now
            elif new_status == AuditStatus.CLOSED:
                audit.end_date = audit.end_date or now
                audit.report_date = audit.report_date or now

            self._persist_audit(audit)
            return audit

    def link_control_to_audit(self, audit_id: str, control_id: str) -> bool:
        """Link a control to an audit engagement."""
        with self._lock:
            audit = self._audits.get(audit_id)
            if not audit:
                return False
            if control_id not in audit.control_ids:
                audit.control_ids.append(control_id)
                audit.updated_at = datetime.now(timezone.utc).isoformat()
                self._persist_audit(audit)
            return True

    def link_finding_to_audit(self, audit_id: str, finding_id: str) -> bool:
        """Link a finding to an audit engagement."""
        with self._lock:
            audit = self._audits.get(audit_id)
            if not audit:
                return False
            if finding_id not in audit.finding_ids:
                audit.finding_ids.append(finding_id)
                audit.updated_at = datetime.now(timezone.utc).isoformat()
                self._persist_audit(audit)
            return True

    # ------------------------------------------------------------------
    # Finding management
    # ------------------------------------------------------------------

    def create_finding(
        self,
        title: str,
        description: str,
        severity: FindingSeverity = FindingSeverity.MEDIUM,
        audit_id: Optional[str] = None,
        control_id: Optional[str] = None,
        root_cause: Optional[str] = None,
        impact: Optional[str] = None,
        recommendation: Optional[str] = None,
        remediation_owner: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Finding:
        """Create a new audit finding."""
        with self._lock:
            finding = Finding(
                title=title,
                description=description,
                severity=severity,
                audit_id=audit_id,
                control_id=control_id,
                root_cause=root_cause,
                impact=impact,
                recommendation=recommendation,
                remediation_owner=remediation_owner,
                due_date=due_date,
            )
            self._findings[finding.finding_id] = finding
            self._persist_finding(finding)

            if audit_id:
                self.link_finding_to_audit(audit_id, finding.finding_id)
            if control_id:
                self.link_finding_to_control(control_id, finding.finding_id)

            return finding

    def get_finding(self, finding_id: str) -> Optional[Finding]:
        """Get a finding by ID."""
        return self._findings.get(finding_id)

    def list_findings(
        self,
        audit_id: Optional[str] = None,
        control_id: Optional[str] = None,
        severity: Optional[FindingSeverity] = None,
        status: Optional[FindingStatus] = None,
    ) -> list[Finding]:
        """List findings with optional filters."""
        findings = list(self._findings.values())
        if audit_id:
            findings = [f for f in findings if f.audit_id == audit_id]
        if control_id:
            findings = [f for f in findings if f.control_id == control_id]
        if severity:
            findings = [f for f in findings if f.severity == severity]
        if status:
            findings = [f for f in findings if f.status == status]
        return findings

    def update_finding_status(
        self,
        finding_id: str,
        new_status: FindingStatus,
        remediation: Optional[str] = None,
        verified_by: Optional[str] = None,
    ) -> Optional[Finding]:
        """Update a finding's status."""
        with self._lock:
            finding = self._findings.get(finding_id)
            if not finding:
                return None
            finding.status = new_status
            finding.updated_at = datetime.now(timezone.utc).isoformat()

            if remediation:
                finding.remediation = remediation
            if new_status == FindingStatus.REMEDIATED:
                finding.remediated_at = datetime.now(timezone.utc).isoformat()
            elif new_status == FindingStatus.VERIFIED:
                finding.verified_at = datetime.now(timezone.utc).isoformat()
                finding.verified_by = verified_by
            elif new_status == FindingStatus.CLOSED:
                finding.verified_at = finding.verified_at or datetime.now(timezone.utc).isoformat()
                finding.verified_by = finding.verified_by or verified_by

            self._persist_finding(finding)
            return finding

    def get_open_findings(self) -> list[Finding]:
        """Get all open findings."""
        return [
            f for f in self._findings.values()
            if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)
        ]

    def get_overdue_findings(self) -> list[Finding]:
        """Get all overdue findings."""
        now = datetime.now(timezone.utc)
        overdue = []
        for f in self._findings.values():
            if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS) and f.due_date:
                try:
                    due = datetime.fromisoformat(f.due_date)
                    if due < now:
                        overdue.append(f)
                except (ValueError, TypeError):
                    pass
        return overdue

    # ------------------------------------------------------------------
    # Workpaper management
    # ------------------------------------------------------------------

    def create_workpaper(
        self,
        title: str,
        audit_id: Optional[str] = None,
        control_id: Optional[str] = None,
        description: Optional[str] = None,
        procedure: Optional[str] = None,
        preparer: Optional[str] = None,
    ) -> Workpaper:
        """Create a new workpaper."""
        with self._lock:
            wp = Workpaper(
                title=title,
                audit_id=audit_id,
                control_id=control_id,
                description=description,
                procedure=procedure,
                preparer=preparer,
                preparation_date=datetime.now(timezone.utc).isoformat(),
            )
            self._workpapers[wp.workpaper_id] = wp
            self._persist_workpaper(wp)

            if audit_id:
                audit = self._audits.get(audit_id)
                if audit and wp.workpaper_id not in audit.workpaper_ids:
                    audit.workpaper_ids.append(wp.workpaper_id)
                    audit.updated_at = datetime.now(timezone.utc).isoformat()
                    self._persist_audit(audit)

            return wp

    def get_workpaper(self, workpaper_id: str) -> Optional[Workpaper]:
        """Get a workpaper by ID."""
        return self._workpapers.get(workpaper_id)

    def list_workpapers(
        self,
        audit_id: Optional[str] = None,
        control_id: Optional[str] = None,
    ) -> list[Workpaper]:
        """List workpapers with optional filters."""
        wps = list(self._workpapers.values())
        if audit_id:
            wps = [w for w in wps if w.audit_id == audit_id]
        if control_id:
            wps = [w for w in wps if w.control_id == control_id]
        return wps

    def review_workpaper(
        self,
        workpaper_id: str,
        conclusion: str,
        reviewer: str,
    ) -> Optional[Workpaper]:
        """Review and conclude a workpaper."""
        with self._lock:
            wp = self._workpapers.get(workpaper_id)
            if not wp:
                return None
            wp.conclusion = conclusion
            wp.reviewer = reviewer
            wp.review_date = datetime.now(timezone.utc).isoformat()
            wp.updated_at = datetime.now(timezone.utc).isoformat()
            self._persist_workpaper(wp)
            return wp

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    def get_compliance_summary(
        self, framework: Optional[ComplianceFramework] = None
    ) -> dict[str, Any]:
        """Get a compliance summary across all or a specific framework."""
        with self._lock:
            controls = list(self._controls.values())
            if framework:
                controls = [c for c in controls if c.framework == framework]

            by_status: dict[str, int] = defaultdict(int)
            by_type: dict[str, int] = defaultdict(int)
            for c in controls:
                by_status[c.status.value] += 1
                by_type[c.control_type.value] += 1

            total = len(controls)
            assessed = total - by_status[ControlStatus.NOT_ASSESSED.value]
            compliant = by_status[ControlStatus.COMPLIANT.value]
            partially = by_status[ControlStatus.PARTIALLY_COMPLIANT.value]
            non_compliant = by_status[ControlStatus.NON_COMPLIANT.value]
            not_applicable = by_status[ControlStatus.NOT_APPLICABLE.value]

            applicable = total - not_applicable
            score = 0.0
            if applicable > 0:
                score = round((compliant + 0.5 * partially) / applicable * 100, 2)

            return {
                "framework": framework.value if framework else "all",
                "total_controls": total,
                "assessed_controls": assessed,
                "compliant": compliant,
                "partially_compliant": partially,
                "non_compliant": non_compliant,
                "not_assessed": by_status[ControlStatus.NOT_ASSESSED.value],
                "not_applicable": not_applicable,
                "compensating_control": by_status[ControlStatus.COMPENSATING_CONTROL.value],
                "compliance_score": score,
                "by_status": dict(by_status),
                "by_type": dict(by_type),
            }

    def get_audit_summary(self, audit_id: str) -> Optional[dict[str, Any]]:
        """Get a summary of an audit engagement."""
        with self._lock:
            audit = self._audits.get(audit_id)
            if not audit:
                return None

            findings = [
                self._findings[fid] for fid in audit.finding_ids
                if fid in self._findings
            ]
            by_severity: dict[str, int] = defaultdict(int)
            by_status: dict[str, int] = defaultdict(int)
            for f in findings:
                by_severity[f.severity.value] += 1
                by_status[f.status.value] += 1

            return {
                "audit_id": audit.audit_id,
                "name": audit.name,
                "status": audit.status.value,
                "type": audit.audit_type.value,
                "framework": audit.framework.value if audit.framework else None,
                "lead_auditor": audit.lead_auditor,
                "start_date": audit.start_date,
                "end_date": audit.end_date,
                "total_controls": len(audit.control_ids),
                "total_findings": len(findings),
                "total_workpapers": len(audit.workpaper_ids),
                "total_evidence": len(audit.evidence_ids),
                "findings_by_severity": dict(by_severity),
                "findings_by_status": dict(by_status),
                "overall_opinion": audit.overall_opinion.value if audit.overall_opinion else None,
            }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close storage connections."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> ComplianceTracker:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
