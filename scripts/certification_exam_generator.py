#!/usr/bin/env python3
"""
GRC_Claw Certification Exam Generator
Generates certification exams with randomized questions, adaptive difficulty, and automatic grading.
"""

import json, random, uuid, hashlib, sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    MULTI_SELECT = "multi_select"
    TRUE_FALSE = "true_false"
    SCENARIO = "scenario"

class Difficulty(str, Enum):
    EASY = "easy"; MEDIUM = "medium"; HARD = "hard"; EXPERT = "expert"

class CertTrack(str, Enum):
    GRC_FUNDAMENTALS = "grc_fundamentals"
    COMPLIANCE_ANALYST = "compliance_analyst"
    AI_GOVERNANCE = "ai_governance"
    SECURITY_AUDITOR = "security_auditor"
    RISK_MANAGER = "risk_manager"
    ARCHITECT = "grc_architect"

@dataclass
class Question:
    question_id: str
    type: QuestionType
    difficulty: Difficulty
    competency: str
    module_id: str
    question_text: str
    options: list[str] = field(default_factory=list)
    correct_answer: str | list[str] = ""
    explanation: str = ""
    scenario: Optional[str] = None
    points: int = 1
    tags: list[str] = field(default_factory=list)

QUESTION_BANK = [
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EASY,"competency":"C1","module_id":"M01","question_text":"What is the default port for the GRC_Claw gateway daemon?","options":["18789","18790","18791","18792"],"correct_answer":"18791","explanation":"The gateway binds to 127.0.0.1:18791 by default, avoiding OpenClaw (18789) and A2Z SOC (18790).","tags":["gateway","config"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EASY,"competency":"C1","module_id":"M01","question_text":"Which protocol does the GRC_Claw gateway use for client communication?","options":["HTTP/1.1","WebSocket","gRPC","MQTT"],"correct_answer":"WebSocket","explanation":"The gateway uses WebSocket with JSON-RPC 2.0 for real-time bidirectional communication.","tags":["gateway","protocol"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C1","module_id":"M02","question_text":"What are the three planes in the GRC_Claw architecture?","options":["Control, Data, Evidence","Input, Process, Output","Frontend, Backend, Database","Management, Operational, Technical"],"correct_answer":"Control, Data, Evidence","explanation":"GRC_Claw uses Control (gateway, agent-runtime), Data (a2z-connector), and Evidence (evidence, frameworks) planes.","tags":["architecture"]},
    {"type":QuestionType.TRUE_FALSE,"difficulty":Difficulty.EASY,"competency":"C1","module_id":"M01","question_text":"The GRC_Claw gateway supports multiple simultaneous instances per cell.","options":["True","False"],"correct_answer":"False","explanation":"The gateway enforces a single instance per cell using a lock file.","tags":["gateway"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C2","module_id":"M03","question_text":"What is the primary function of the agent policy firewall?","options":["Route network traffic","Intercept and enforce allow/deny rules on agent actions","Monitor agent resource consumption","Authenticate agents"],"correct_answer":"Intercept and enforce allow/deny rules on agent actions","explanation":"The policy firewall intercepts all agent actions and evaluates them against defined policies.","tags":["policy","firewall"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C2","module_id":"M03","question_text":"What happens when an agent's trust score drops below the threshold?","options":["Agent is permanently banned","Agent requires approval for actions","Agent is automatically shut down","Nothing - trust scores are informational"],"correct_answer":"Agent requires approval for actions","explanation":"Low-trust agents enter supervised mode where actions require explicit approval.","tags":["trust"]},
    {"type":QuestionType.SCENARIO,"difficulty":Difficulty.HARD,"competency":"C2","module_id":"M03","scenario":"An agent with trust score 45 attempts to write to /etc/passwd. The policy firewall denies all file-write operations outside /tmp/grc-workspace for agents with trust score < 60.","question_text":"What is the outcome?","options":["Action allowed - trust score above 40","Action denied - policy rule blocks it","Action allowed with warning","Action queued for review"],"correct_answer":"Action denied - policy rule blocks it","explanation":"Trust score 45 < 60 AND /etc/passwd is outside /tmp/grc-workspace. Both conditions met, action denied.","tags":["policy","scenario"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C3","module_id":"M02","question_text":"What hash algorithm does GRC_Claw use for evidence artifact integrity?","options":["MD5","SHA-1","SHA-256","SHA-3"],"correct_answer":"SHA-256","explanation":"GRC_Claw uses SHA-256 for content hashing of evidence artifacts.","tags":["evidence","hashing"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C3","module_id":"M04","question_text":"What is the primary purpose of the compliance orchestrator?","options":["Generate compliance reports","Chain controls, tests, and evidence into automated workflows","Monitor agent behavior","Manage user access"],"correct_answer":"Chain controls, tests, and evidence into automated workflows","explanation":"The orchestrator chains compliance activities into DAG-based workflows.","tags":["orchestrator"]},
    {"type":QuestionType.MULTI_SELECT,"difficulty":Difficulty.HARD,"competency":"C3","module_id":"M04","question_text":"Which are valid workflow trigger types? (Select all)","options":["Scheduled (cron-based)","Event-driven (SIEM alert)","Manual (user-initiated)","Random (probabilistic)","Conditional (state-based)"],"correct_answer":["Scheduled (cron-based)","Event-driven (SIEM alert)","Manual (user-initiated)","Conditional (state-based)"],"explanation":"The orchestrator supports scheduled, event-driven, manual, and conditional triggers. Random is not supported.","tags":["orchestrator","triggers"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C6","module_id":"M06","question_text":"What query language does the compliance knowledge graph use?","options":["SQL","Cypher","SPARQL","GraphQL"],"correct_answer":"Cypher","explanation":"The knowledge graph uses a Cypher-like query language.","tags":["knowledge-graph"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C6","module_id":"M06","question_text":"Which relationship type connects a Control to its Evidence?","options":["MAPS_TO","TESTS","PRODUCES","DEPENDS_ON"],"correct_answer":"PRODUCES","explanation":"Controls PRODUCES Evidence. MAPS_TO connects controls to frameworks, TESTS connects controls to tests.","tags":["knowledge-graph"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C5","module_id":"M07","question_text":"What is the formula for calculating risk score?","options":["Risk = Likelihood + Impact","Risk = Likelihood × Impact × Control Gap","Risk = Impact / Likelihood","Risk = (Likelihood + Impact) / 2"],"correct_answer":"Risk = Likelihood × Impact × Control Gap","explanation":"Risk is the product of likelihood, impact, and control gap (0-1).","tags":["risk"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C5","module_id":"M07","question_text":"Which risk treatment strategy involves purchasing cyber insurance?","options":["Mitigate","Transfer","Accept","Avoid"],"correct_answer":"Transfer","explanation":"Risk transfer shifts the financial burden to a third party through insurance.","tags":["risk","treatment"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C9","module_id":"M12","question_text":"What does BIA stand for?","options":["Business Integration Assessment","Business Impact Analysis","Baseline Infrastructure Audit","Business Intelligence Analytics"],"correct_answer":"Business Impact Analysis","explanation":"BIA quantifies the business impact of disruptions.","tags":["business-impact"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C8","module_id":"M09","question_text":"What is the highest risk classification for an AI model?","options":["Minimal","Low","High","Unacceptable"],"correct_answer":"Unacceptable","explanation":"Risk classes: minimal, low, high, unacceptable. Unacceptable models cannot be deployed.","tags":["ai-governance"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C8","module_id":"M09","question_text":"Which is NOT a dimension of model risk assessment?","options":["Bias","Explainability","Latency","Robustness"],"correct_answer":"Latency","explanation":"Model risk dimensions: bias, explainability, robustness, data quality. Latency is a performance metric.","tags":["ai-governance"]},
    {"type":QuestionType.SCENARIO,"difficulty":Difficulty.EXPERT,"competency":"C8","module_id":"M09","scenario":"A customer service AI model shows 15% lower approval rates for a specific demographic group. The model was trained on historical data reflecting past lending biases.","question_text":"What is the most appropriate first action?","options":["Retrain with balanced data","Document the bias and escalate to AI governance board","Adjust decision threshold","Continue monitoring"],"correct_answer":"Document the bias and escalate to AI governance board","explanation":"Documenting and escalating is the first step. The governance board decides on remediation.","tags":["ai-governance","bias","scenario"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C10","module_id":"M08","question_text":"What is the maximum acceptable age for compliance evidence?","options":["6 months","12 months","18 months","24 months"],"correct_answer":"12 months","explanation":"Evidence must be less than 12 months old to be considered current.","tags":["audit","evidence"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C10","module_id":"M08","question_text":"What is the correct lifecycle for an audit finding?","options":["Open → Closed","Open → In Progress → Closed","Identified → Assessed → Remediated → Verified → Closed","New → Assigned → Resolved"],"correct_answer":"Identified → Assessed → Remediated → Verified → Closed","explanation":"Audit findings follow a 5-stage lifecycle.","tags":["audit","findings"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C10","module_id":"M13","question_text":"What cryptographic system does GRC_Claw use for zero-knowledge compliance proofs?","options":["zk-STARKs","zk-SNARKs","Bulletproofs","Ring signatures"],"correct_answer":"zk-SNARKs","explanation":"GRC_Claw uses zk-SNARKs for compact, non-interactive zero-knowledge proofs.","tags":["zk","cryptography"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C4","module_id":"M05","question_text":"What is the data flow path for a security event from SIEM to compliance alert?","options":["SIEM → Gateway → Evidence → SOC","SIEM → A2Z Connector → Gateway → Evidence → SOC Alert","SIEM → Evidence → Gateway → SOC","SIEM → Orchestrator → Gateway → SOC"],"correct_answer":"SIEM → A2Z Connector → Gateway → Evidence → SOC Alert","explanation":"Events flow: SIEM → A2Z Connector → Gateway → Evidence → SOC Alert.","tags":["integration","a2z"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C7","module_id":"M11","question_text":"What threat intelligence format does GRC_Claw natively support?","options":["STIX 1.0","STIX 2.1","OpenIOC","YARA"],"correct_answer":"STIX 2.1","explanation":"GRC_Claw natively supports STIX 2.1 for threat intelligence ingestion.","tags":["threat-intel","stix"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C7","module_id":"M11","question_text":"Which AI-specific threat involves manipulating training data?","options":["Prompt injection","Model extraction","Data poisoning","Adversarial examples"],"correct_answer":"Data poisoning","explanation":"Data poisoning manipulates the training dataset to degrade model behavior.","tags":["ai-threat"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C4","module_id":"M10","question_text":"How is trust established between federated GRC_Claw instances?","options":["Shared API keys","Mutual TLS and trust passports","OAuth 2.0 token exchange","SSH key pairs"],"correct_answer":"Mutual TLS and trust passports","explanation":"Federated trust uses mutual TLS for transport security and trust passports for identity verification.","tags":["federation","trust"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C6","module_id":"M13","question_text":"What is the primary advantage of ZK proofs for compliance verification?","options":["Faster computation","Verify compliance without revealing sensitive data","Smaller storage","Easier implementation"],"correct_answer":"Verify compliance without revealing sensitive data","explanation":"ZK proofs verify compliance statements without exposing underlying sensitive data.","tags":["zk","privacy"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C9","module_id":"M12","question_text":"What is the primary audience for financial governance reports?","options":["SOC analysts","Board and executive leadership","Compliance auditors","IT operations"],"correct_answer":"Board and executive leadership","explanation":"Financial governance reports are designed for board and executive consumption.","tags":["financial-governance"]},
    {"type":QuestionType.TRUE_FALSE,"difficulty":Difficulty.MEDIUM,"competency":"C3","module_id":"M02","question_text":"Evidence artifacts in GRC_Claw are mutable and can be updated after creation.","options":["True","False"],"correct_answer":"False","explanation":"Evidence artifacts are immutable once created. Updates create new versions.","tags":["evidence","immutability"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EASY,"competency":"C1","module_id":"M01","question_text":"What is the minimum Node.js version required for GRC_Claw?","options":["Node 16","Node 18","Node 20","Node 22"],"correct_answer":"Node 20","explanation":"GRC_Claw requires Node.js >= 20.","tags":["requirements"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C5","module_id":"M07","question_text":"What is residual risk?","options":["Risk before treatment","Risk remaining after treatment","Risk transferred to third party","Risk completely eliminated"],"correct_answer":"Risk remaining after treatment","explanation":"Residual risk is the risk remaining after treatment measures are implemented.","tags":["risk"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C2","module_id":"M03","question_text":"What is the purpose of the action ledger?","options":["Store conversation history","Record all agent actions immutably for audit","Track performance metrics","Manage task queues"],"correct_answer":"Record all agent actions immutably for audit","explanation":"The action ledger is an immutable record of all agent actions.","tags":["ledger","audit"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C8","module_id":"M09","question_text":"What triggers continuous model monitoring alerts?","options":["Scheduled daily checks only","Metric thresholds being exceeded","Manual user requests","New model deployments only"],"correct_answer":"Metric thresholds being exceeded","explanation":"Alerts trigger when metrics exceed configured thresholds.","tags":["ai-governance","monitoring"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C6","module_id":"M06","question_text":"What type of database does the compliance knowledge graph use?","options":["Relational (SQL)","Document (NoSQL)","Property graph","Key-value store"],"correct_answer":"Property graph","explanation":"The knowledge graph uses a property graph model.","tags":["knowledge-graph"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C10","module_id":"M08","question_text":"What is the purpose of an assurance envelope?","options":["Encrypt evidence for transmission","Package evidence with integrity proofs and metadata","Compress evidence for storage","Redact sensitive information"],"correct_answer":"Package evidence with integrity proofs and metadata","explanation":"An assurance envelope packages evidence with cryptographic integrity proofs and metadata.","tags":["audit","assurance"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C4","module_id":"M05","question_text":"Which A2Z SOC endpoint receives compliance alerts?","options":["/api/events","/compliance_alerts","/security_events","/background_jobs"],"correct_answer":"/compliance_alerts","explanation":"Compliance alerts are pushed to /compliance_alerts.","tags":["a2z","alerts"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C7","module_id":"M11","question_text":"What is the primary indicator of a prompt injection attack?","options":["Unusual network traffic","Attempts to override system instructions through user input","High CPU usage","Repeated failed logins"],"correct_answer":"Attempts to override system instructions through user input","explanation":"Prompt injection attempts to manipulate the model by embedding malicious instructions in user input.","tags":["ai-threat"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C9","module_id":"M12","question_text":"What metric measures the return on compliance investment?","options":["Compliance ROI","Risk-adjusted return","Cost per control","Audit finding reduction rate"],"correct_answer":"Compliance ROI","explanation":"Compliance ROI measures the return on investment in compliance activities.","tags":["financial-governance"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C1","module_id":"M14","question_text":"What is the recommended order for implementing a compliance pipeline?","options":["Orchestrator → Gateway → Evidence → Reporting","Gateway → Evidence → Orchestrator → Reporting","Evidence → Gateway → Orchestrator → Reporting","Reporting → Orchestrator → Gateway → Evidence"],"correct_answer":"Gateway → Evidence → Orchestrator → Reporting","explanation":"Start with gateway (control), then evidence (data), then orchestrator (automation), and finally reporting.","tags":["architecture","capstone"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C3","module_id":"M04","question_text":"What is drift detection in continuous compliance?","options":["Detecting changes in compliance posture over time","Detecting unauthorized configuration changes","Detecting agent behavior anomalies","Detecting evidence tampering"],"correct_answer":"Detecting changes in compliance posture over time","explanation":"Drift detection monitors compliance posture over time and alerts on deviation.","tags":["continuous-compliance","drift"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C2","module_id":"M03","question_text":"What component evaluates agent trust scores?","options":["Policy firewall","Trust score engine","Action ledger","Gateway authenticator"],"correct_answer":"Trust score engine","explanation":"The trust score engine evaluates and

... [OUTPUT TRUNCATED - 61,676 chars omitted out of 111,602 total] ...

  {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C1","module_id":"M14","question_text":"What is the recommended approach for architecture design?","options":["Use informal notes","Use the C4 model for structured architecture design","Skip architecture design","Use only diagrams"],"correct_answer":"Use the C4 model for structured architecture design","explanation":"The C4 model provides structured architecture design.","tags":["capstone","architecture"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C3","module_id":"M02","question_text":"What is the purpose of evidence lifecycle management?","options":["Compress evidence for storage","Manage the lifecycle of evidence from creation to archival","Encrypt evidence for transmission","Index evidence for fast retrieval"],"correct_answer":"Manage the lifecycle of evidence from creation to archival","explanation":"Evidence lifecycle management manages the lifecycle of evidence.","tags":["evidence","lifecycle"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C5","module_id":"M07","question_text":"What is the purpose of risk assessment scheduling?","options":["Distribute risk evenly","Schedule regular risk assessments","Calculate insurance premiums","Generate risk reports"],"correct_answer":"Schedule regular risk assessments","explanation":"Risk assessment scheduling schedules regular risk assessments.","tags":["risk","scheduling"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C9","module_id":"M12","question_text":"What is the purpose of compliance cost analysis?","options":["Measure compliance team productivity","Analyze the cost of compliance activities","Calculate audit fees","Benchmark against competitors"],"correct_answer":"Analyze the cost of compliance activities","explanation":"Compliance cost analysis analyzes the cost of compliance activities.","tags":["financial-governance","cost-analysis"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C8","module_id":"M09","question_text":"What is the purpose of model compliance verification?","options":["Track model API usage","Verify that models comply with governance policies","Monitor model performance","Manage model configurations"],"correct_answer":"Verify that models comply with governance policies","explanation":"Model compliance verification verifies that models comply with governance policies.","tags":["ai-governance","compliance"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C10","module_id":"M08","question_text":"What is the purpose of audit preparation?","options":["Schedule auditor vacations","Prepare evidence and documentation for audit","Generate audit reports","Track audit findings"],"correct_answer":"Prepare evidence and documentation for audit","explanation":"Audit preparation prepares evidence and documentation for audit.","tags":["audit","preparation"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C4","module_id":"M10","question_text":"What is the primary benefit for supply chain risk management?","options":["Reduced infrastructure costs","Verify supplier risk posture without accessing sensitive supplier data","Faster model training","Simplified user management"],"correct_answer":"Verify supplier risk posture without accessing sensitive supplier data","explanation":"The federated mesh enables supply chain risk management without accessing sensitive data.","tags":["federation","supply-chain"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C1","module_id":"M01","question_text":"What is the purpose of the gateway's authorization?","options":["Encrypt data in transit","Verify client permissions for specific operations","Authenticate clients","Sign evidence artifacts"],"correct_answer":"Verify client permissions for specific operations","explanation":"Authorization verifies client permissions for specific operations.","tags":["gateway","authorization"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C3","module_id":"M04","question_text":"What is the purpose of workflow versioning?","options":["Improve workflow performance","Manage different versions of workflow definitions","Simplify workflow design","Reduce workflow complexity"],"correct_answer":"Manage different versions of workflow definitions","explanation":"Workflow versioning manages different versions of workflow definitions.","tags":["orchestrator","versioning"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C6","module_id":"M06","question_text":"What is the purpose of graph analytics?","options":["Optimize query performance","Analyze compliance patterns and trends","Validate data integrity","Store user preferences"],"correct_answer":"Analyze compliance patterns and trends","explanation":"Graph analytics analyzes compliance patterns and trends.","tags":["knowledge-graph","analytics"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C5","module_id":"M07","question_text":"What is the purpose of risk assessment documentation?","options":["Track risk treatment progress","Document risk assessment methodology and results","Calculate risk scores","Generate risk reports"],"correct_answer":"Document risk assessment methodology and results","explanation":"Risk assessment documentation documents risk assessment methodology and results.","tags":["risk","documentation"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C9","module_id":"M12","question_text":"What is the purpose of compliance budget planning?","options":["Distribute compliance budget evenly","Plan compliance budget based on risk priorities and investment analysis","Calculate audit fees","Measure compliance team productivity"],"correct_answer":"Plan compliance budget based on risk priorities and investment analysis","explanation":"Compliance budget planning plans compliance budget based on risk priorities.","tags":["financial-governance","budget"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C10","module_id":"M13","question_text":"What is the purpose of the common reference string?","options":["Generate the proof","Provide shared parameters for proof generation and verification","Verify the proof","Store the proof on blockchain"],"correct_answer":"Provide shared parameters for proof generation and verification","explanation":"The common reference string provides shared parameters for proof generation and verification.","tags":["zk","crs"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C7","module_id":"M11","question_text":"What is the purpose of threat intelligence normalization?","options":["Reduce threat feed costs","Normalize threat intelligence from different formats for correlation","Generate threat reports","Automate incident response"],"correct_answer":"Normalize threat intelligence from different formats for correlation","explanation":"Threat intelligence normalization normalizes threat intelligence from different formats.","tags":["threat-intel","normalization"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C2","module_id":"M03","question_text":"What is the purpose of agent supervision?","options":["Track agent locations","Monitor and control agent actions under policy","Monitor agent performance","Manage agent configurations"],"correct_answer":"Monitor and control agent actions under policy","explanation":"Agent supervision monitors and controls agent actions under policy.","tags":["agent","supervision"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C8","module_id":"M09","question_text":"What is the purpose of model governance?","options":["Track model API usage","Govern AI models throughout their lifecycle","Monitor model performance","Manage model configurations"],"correct_answer":"Govern AI models throughout their lifecycle","explanation":"Model governance governs AI models throughout their lifecycle.","tags":["ai-governance","lifecycle"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C6","module_id":"M06","question_text":"What is the purpose of the data model?","options":["Optimize database performance","Define how compliance data is structured and stored","Generate visual diagrams","Validate data integrity"],"correct_answer":"Define how compliance data is structured and stored","explanation":"The data model defines how compliance data is structured and stored.","tags":["knowledge-graph","data-model"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C4","module_id":"M05","question_text":"What is the purpose of event mapping?","options":["Map security events to compliance controls","Pull security events from the SIEM","Push compliance alerts to the SOC","Synchronize user data"],"correct_answer":"Map security events to compliance controls","explanation":"Event mapping maps security events to compliance controls.","tags":["a2z","event-mapping"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C1","module_id":"M14","question_text":"What is the recommended approach for architecture design?","options":["Use informal notes","Use the C4 model for structured architecture design","Skip architecture design","Use only diagrams"],"correct_answer":"Use the C4 model for structured architecture design","explanation":"The C4 model provides structured architecture design.","tags":["capstone","architecture"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C3","module_id":"M02","question_text":"What is the purpose of evidence retention?","options":["Compress evidence for storage","Retain evidence for compliance and audit requirements","Encrypt evidence for transmission","Index evidence for fast retrieval"],"correct_answer":"Retain evidence for compliance and audit requirements","explanation":"Evidence retention retains evidence for compliance and audit requirements.","tags":["evidence","retention"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C5","module_id":"M07","question_text":"What is the purpose of risk assessment review?","options":["Track risk treatment progress","Review and update risk assessments periodically","Calculate risk scores","Generate risk reports"],"correct_answer":"Review and update risk assessments periodically","explanation":"Risk assessment review reviews and updates risk assessments periodically.","tags":["risk","review"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C9","module_id":"M12","question_text":"What is the purpose of compliance investment optimization?","options":["Measure compliance team productivity","Optimize compliance investments for maximum risk reduction","Calculate audit fees","Benchmark against competitors"],"correct_answer":"Optimize compliance investments for maximum risk reduction","explanation":"Compliance investment optimization optimizes compliance investments.","tags":["financial-governance","optimization"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C8","module_id":"M09","question_text":"What is the purpose of model audit?","options":["Track model API usage","Audit model compliance with governance policies","Monitor model performance","Manage model configurations"],"correct_answer":"Audit model compliance with governance policies","explanation":"Model audit audits model compliance with governance policies.","tags":["ai-governance","audit"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C10","module_id":"M08","question_text":"What is the purpose of audit execution?","options":["Schedule auditor vacations","Execute the audit plan and collect evidence","Generate audit reports","Track audit findings"],"correct_answer":"Execute the audit plan and collect evidence","explanation":"Audit execution executes the audit plan and collects evidence.","tags":["audit","execution"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C4","module_id":"M10","question_text":"What is the primary benefit for regulatory reporting?","options":["Reduced infrastructure costs","Enable regulatory reporting without exposing sensitive data","Faster model training","Simplified user management"],"correct_answer":"Enable regulatory reporting without exposing sensitive data","explanation":"The federated mesh enables regulatory reporting without exposing sensitive data.","tags":["federation","regulatory"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C1","module_id":"M01","question_text":"What is the purpose of the gateway's logging?","options":["Store user preferences","Log gateway operations for audit and debugging","Cache compliance results","Track agent performance"],"correct_answer":"Log gateway operations for audit and debugging","explanation":"Logging logs gateway operations for audit and debugging.","tags":["gateway","logging"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C3","module_id":"M04","question_text":"What is the purpose of workflow optimization?","options":["Improve workflow performance and efficiency","Manage workflow versions","Simplify workflow design","Reduce workflow complexity"],"correct_answer":"Improve workflow performance and efficiency","explanation":"Workflow optimization improves workflow performance and efficiency.","tags":["orchestrator","optimization"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C6","module_id":"M06","question_text":"What is the purpose of graph querying?","options":["Optimize database performance","Query the knowledge graph for compliance information","Validate data integrity","Store user preferences"],"correct_answer":"Query the knowledge graph for compliance information","explanation":"Graph querying queries the knowledge graph for compliance information.","tags":["knowledge-graph","querying"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.HARD,"competency":"C5","module_id":"M07","question_text":"What is the purpose of risk assessment validation?","options":["Track risk treatment progress","Validate risk assessment results for accuracy and completeness","Calculate risk scores","Generate risk reports"],"correct_answer":"Validate risk assessment results for accuracy and completeness","explanation":"Risk assessment validation validates risk assessment results.","tags":["risk","validation"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C9","module_id":"M12","question_text":"What is the purpose of compliance investment evaluation?","options":["Measure compliance team productivity","Evaluate the effectiveness of compliance investments","Calculate audit fees","Benchmark against competitors"],"correct_answer":"Evaluate the effectiveness of compliance investments","explanation":"Compliance investment evaluation evaluates the effectiveness of compliance investments.","tags":["financial-governance","evaluation"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.EXPERT,"competency":"C10","module_id":"M13","question_text":"What is the purpose of the trusted setup?","options":["Generate the proof","Generate the proving and verification keys in a secure environment","Verify the proof","Store the proof on blockchain"],"correct_answer":"Generate the proving and verification keys in a secure environment","explanation":"The trusted setup generates the proving and verification keys in a secure environment.","tags":["zk","trusted-setup"]},
    {"type":QuestionType.MULTIPLE_CHOICE,"difficulty":Difficulty.MEDIUM,"competency":"C7","module_id":"M11","question_text":"What is the purpose of threat intelligence enrichment?","options":["Reduce threat feed costs","Enrich threat intelligence with additional context","Generate threat reports","Automate incident response"],"correct_answer":"Enrich threat intelligence with additional context","explanation":"Threat intelligence enrichment enriches threat intelligence with additional context.","tags":["threat-intel","enrichment"]},
]

TRACK_CONFIG = {
    CertTrack.GRC_FUNDAMENTALS: {
        "name": "GRC Fundamentals",
        "description": "Foundational GRC_Claw concepts and architecture",
        "competencies": ["C1", "C2", "C3"],
        "modules": ["M01", "M02", "M03", "M04"],
        "num_questions": 20,
        "passing_score": 70.0,
        "time_limit_minutes": 30,
        "validity_months": 12,
    },
    CertTrack.COMPLIANCE_ANALYST: {
        "name": "Compliance Analyst",
        "description": "Compliance operations, evidence, and orchestration",
        "competencies": ["C3", "C6", "C10"],
        "modules": ["M02", "M04", "M06", "M08"],
        "num_questions": 25,
        "passing_score": 75.0,
        "time_limit_minutes": 45,
        "validity_months": 12,
    },
    CertTrack.AI_GOVERNANCE: {
        "name": "AI Governance",
        "description": "AI model governance, risk, and compliance",
        "competencies": ["C2", "C5", "C8"],
        "modules": ["M03", "M07", "M09"],
        "num_questions": 25,
        "passing_score": 75.0,
        "time_limit_minutes": 45,
        "validity_months": 12,
    },
    CertTrack.SECURITY_AUDITOR: {
        "name": "Security Auditor",
        "description": "Audit management, evidence, and assurance",
        "competencies": ["C1", "C3", "C10"],
        "modules": ["M02", "M08", "M13"],
        "num_questions": 30,
        "passing_score": 80.0,
        "time_limit_minutes": 60,
        "validity_months": 12,
    },
    CertTrack.RISK_MANAGER: {
        "name": "Risk Manager",
        "description": "Risk assessment, treatment, and business impact",
        "competencies": ["C5", "C9"],
        "modules": ["M07", "M12"],
        "num_questions": 25,
        "passing_score": 75.0,
        "time_limit_minutes": 45,
        "validity_months": 12,
    },
    CertTrack.ARCHITECT: {
        "name": "GRC Architect",
        "description": "Advanced architecture, federation, and capstone",
        "competencies": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
        "modules": ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "M09", "M10", "M11", "M12", "M13", "M14"],
        "num_questions": 40,
        "passing_score": 80.0,
        "time_limit_minutes": 90,
        "validity_months": 24,
    },
}


class ExamGenerator:
    """Generates and grades certification exams."""

    def __init__(self, data_dir: str = "~/.grc_claw/certification"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.data_dir / "exam_results.json"
        self.results = self._load_results()

    def _load_results(self) -> dict:
        if self.results_file.exists():
            with open(self.results_file) as f:
                return json.load(f)
        return {}

    def _save_results(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results, f, indent=2)

    def generate_exam(self, track: CertTrack, user_id: str, seed: Optional[int] = None) -> dict:
        """Generate a certification exam for a specific track."""
        if track not in TRACK_CONFIG:
            raise ValueError(f"Unknown track: {track}")

        config = TRACK_CONFIG[track]
        rng = random.Random(seed or hash(user_id + track.value))

        # Filter questions by track competencies and modules
        eligible = [q for q in QUESTION_BANK if q["competency"] in config["competencies"]]
        if len(eligible) < config["num_questions"]:
            eligible = QUESTION_BANK  # fallback to all questions

        # Select questions with difficulty distribution
        num_q = config["num_questions"]
        easy_count = int(num_q * 0.25)
        medium_count = int(num_q * 0.35)
        hard_count = int(num_q * 0.25)
        expert_count = num_q - easy_count - medium_count - hard_count

        selected = []
        for diff, count in [(Difficulty.EASY, easy_count), (Difficulty.MEDIUM, medium_count),
                            (Difficulty.HARD, hard_count), (Difficulty.EXPERT, expert_count)]:
            pool = [q for q in eligible if q["difficulty"] == diff]
            if len(pool) < count:
                pool = [q for q in eligible if q["difficulty"] == diff] or eligible
            selected.extend(rng.sample(pool, min(count, len(pool))))

        # Shuffle and assign IDs
        rng.shuffle(selected)
        questions = []
        for i, q in enumerate(selected):
            q_copy = dict(q)
            q_copy["question_id"] = f"Q{i+1:03d}"
            q_copy["points"] = {"easy": 1, "medium": 2, "hard": 3, "expert": 4}[q["difficulty"].value if isinstance(q["difficulty"], Difficulty) else q["difficulty"]]
            questions.append(q_copy)

        exam_id = str(uuid.uuid4())
        return {
            "exam_id": exam_id,
            "track": track.value,
            "track_name": config["name"],
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "time_limit_minutes": config["time_limit_minutes"],
            "passing_score": config["passing_score"],
            "total_questions": len(questions),
            "total_points": sum(q["points"] for q in questions),
            "questions": questions,
        }

    def grade_exam(self, exam: dict, answers: dict[str, str | list[str]], time_taken_minutes: int) -> dict:
        """Grade a completed exam."""
        question_results = []
        total_points = 0
        earned_points = 0
        competency_points = {}
        competency_earned = {}

        for q in exam["questions"]:
            qid = q["question_id"]
            correct = q["correct_answer"]
            user_answer = answers.get(qid, "")
            points = q["points"]
            total_points += points

            comp = q["competency"]
            competency_points[comp] = competency_points.get(comp, 0) + points

            if isinstance(correct, list):
                # Multi-select
                if isinstance(user_answer, list):
                    correct_set = set(correct)
                    user_set = set(user_answer)
                    is_correct = correct_set == user_set
                else:
                    is_correct = False
            else:
                is_correct = str(user_answer).strip().lower() == str(correct).strip().lower()

            if is_correct:
                earned_points += points
                competency_earned[comp] = competency_earned.get(comp, 0) + points

            question_results.append({
                "question_id": qid,
                "competency": comp,
                "module_id": q["module_id"],
                "difficulty": q["difficulty"],
                "user_answer": user_answer,
                "correct_answer": correct,
                "is_correct": is_correct,
                "points_earned": points if is_correct else 0,
                "points_possible": points,
                "explanation": q["explanation"],
            })

        score_pct = round(earned_points / total_points * 100, 1) if total_points > 0 else 0
        passed = score_pct >= exam["passing_score"]

        competency_scores = {}
        for comp in competency_points:
            competency_scores[comp] = round(competency_earned.get(comp, 0) / competency_points[comp] * 100, 1)

        result = {
            "result_id": str(uuid.uuid4()),
            "exam_id": exam["exam_id"],
            "user_id": exam["user_id"],
            "track": exam["track"],
            "track_name": exam["track_name"],
            "exam_date": datetime.now().isoformat(),
            "score": score_pct,
            "max_score": 100.0,
            "earned_points": earned_points,
            "total_points": total_points,
            "passed": passed,
            "passing_score": exam["passing_score"],
            "time_taken_minutes": time_taken_minutes,
            "question_results": question_results,
            "competency_scores": competency_scores,
        }

        if passed:
            config = TRACK_CONFIG[CertTrack(exam["track"])]
            result["certification_id"] = f"CERT-{hashlib.sha256(result['result_id'].encode()).hexdigest()[:12].upper()}"
            result["expires_at"] = (datetime.now() + timedelta(days=30 * config["validity_months"])).isoformat()

        # Store result
        self.results[result["result_id"]] = result
        self._save_results()

        return result

    def get_certification_status(self, user_id: str) -> dict:
        """Get certification status for a user."""
        user_results = [r for r in self.results.values() if r["user_id"] == user_id]
        active_certs = []
        expired_certs = []
        now = datetime.now()

        for r in user_results:
            if r.get("certification_id"):
                expires = datetime.fromisoformat(r["expires_at"])
                cert_info = {
                    "certification_id": r["certification_id"],
                    "track": r["track"],
                    "track_name": r["track_name"],
                    "earned_date": r["exam_date"],
                    "expires_at": r["expires_at"],
                    "score": r["score"],
                }
                if expires > now:
                    active_certs.append(cert_info)
                else:
                    expired_certs.append(cert_info)

        return {
            "user_id": user_id,
            "active_certifications": active_certs,
            "expired_certifications": expired_certs,
            "total_exams_taken": len(user_results),
            "total_passed": sum(1 for r in user_results if r["passed"]),
            "average_score": round(sum(r["score"] for r in user_results) / len(user_results), 1) if user_results else 0,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GRC_Claw Certification Exam Generator")
    parser.add_argument("--track", type=str, choices=[t.value for t in CertTrack], help="Certification track")
    parser.add_argument("--user", type=str, default="anonymous", help="User ID")
    parser.add_argument("--generate", action="store_true", help="Generate an exam")
    parser.add_argument("--list-tracks", action="store_true", help="List available tracks")
    parser.add_argument("--status", action="store_true", help="Get certification status")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    gen = ExamGenerator()

    if args.list_tracks:
        tracks = [{"track": t.value, "name": c["name"], "description": c["description"],
                   "questions": c["num_questions"], "passing_score": c["passing_score"],
                   "time_limit": c["time_limit_minutes"]} for t, c in TRACK_CONFIG.items()]
        if args.json:
            print(json.dumps(tracks, indent=2))
        else:
            print(f"\n{'Track':<25} {'Name':<25} {'Questions':<12} {'Passing':<10} {'Time':<10}")
            print("-" * 90)
            for t in tracks:
                print(f"{t['track']:<25} {t['name']:<25} {t['questions']:<12} {t['passing_score']:<10} {t['time_limit']} min")

    elif args.generate and args.track:
        exam = gen.generate_exam(CertTrack(args.track), args.user)
        if args.json:
            print(json.dumps(exam, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"Certification Exam: {exam['track_name']}")
            print(f"{'='*60}")
            print(f"Exam ID: {exam['exam_id']}")
            print(f"Questions: {exam['total_questions']}")
            print(f"Total Points: {exam['total_points']}")
            print(f"Time Limit: {exam['time_limit_minutes']} minutes")
            print(f"Passing Score: {exam['passing_score']}%")
            print("\n--- Questions ---")
            for q in exam["questions"]:
                print(f"\n[{q['question_id']}] ({q['difficulty']}, {q['points']} pts) {q['question_text']}")
                if q.get("scenario"):
                    print(f"  Scenario: {q['scenario']}")
                for i, opt in enumerate(q["options"]):
                    print(f"  {chr(65+i)}. {opt}")

    elif args.status:
        status = gen.get_certification_status(args.user)
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"Certification Status for {args.user}")
            print(f"{'='*60}")
            print(f"Total Exams: {status['total_exams_taken']}")
            print(f"Passed: {status['total_passed']}")
            print(f"Average Score: {status['average_score']}%")
            if status["active_certifications"]:
--- Active Certifications ---")
                for c in status["active_certifications"]:
                    print(f"  {c['certification_id']} | {c['track_name']} | Score: {c['score']}% | Expires: {c['expires_at'][:10]}")
            if status["expired_certifications"]:
--- Expired Certifications ---")
                for c in status["expired_certifications"]:
                    print(f"  {c['certification_id']} | {c['track_name']} | Expired: {c['expires_at'][:10]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()