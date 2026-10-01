"""
GRC_Claw AI Incident Taxonomy (§3 of GRC-AIM-001)

Defines the 8 primary incident categories, 44 subcategories, and minimum severity levels.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class IncidentCategory(str, Enum):
    """Primary AI incident categories (§3.1)."""
    DATA_LEAKAGE = "DL"
    HARMFUL_OUTPUT = "HO"
    WRONG_ACTION = "WA"
    HALLUCINATION = "HL"
    PROMPT_INJECTION = "PI"
    MODEL_POISONING = "MP"
    SUPPLY_CHAIN = "SC"
    AGENT_MISBEHAVIOR = "AM"


class Severity(str, Enum):
    """Severity levels (§4.1)."""
    S1_CRITICAL = "S1"
    S2_HIGH = "S2"
    S3_MEDIUM = "S3"
    S4_LOW = "S4"
    S5_INFORMATIONAL = "S5"


@dataclass(frozen=True)
class Subcategory:
    """Incident subcategory definition."""
    code: str
    category: IncidentCategory
    name: str
    description: str
    detection_signals: tuple[str, ...] = field(default_factory=tuple)


# ── Category 1: Data Leakage (DL) ──────────────────────────────────────────────
DL_1 = Subcategory("DL-1", IncidentCategory.DATA_LEAKAGE, "Training Data Exposure",
    "Model regurgitates verbatim or near-verbatim training data containing PII or proprietary information",
    ("Output similarity matching against training corpus", "PII detection in outputs"))
DL_2 = Subcategory("DL-2", IncidentCategory.DATA_LEAKAGE, "Inference Data Leakage",
    "User inputs from one session leak into another user's context or output",
    ("Cross-session data correlation", "Session isolation testing"))
DL_3 = Subcategory("DL-3", IncidentCategory.DATA_LEAKAGE, "Model Artifact Exfiltration",
    "Model weights, embeddings, or parameters are extracted via model extraction attacks",
    ("Query pattern analysis", "API abuse detection", "Output perturbation monitoring"))
DL_4 = Subcategory("DL-4", IncidentCategory.DATA_LEAKAGE, "Prompt Data Leakage",
    "System prompts, hidden instructions, or internal configuration data are disclosed",
    ("System prompt extraction testing", "Output analysis for instruction leakage"))
DL_5 = Subcategory("DL-5", IncidentCategory.DATA_LEAKAGE, "Embedding Space Leakage",
    "Sensitive information is recoverable from embedding representations",
    ("Embedding inversion attacks", "Similarity search abuse"))
DL_6 = Subcategory("DL-6", IncidentCategory.DATA_LEAKAGE, "Logging Data Leakage",
    "Sensitive data is written to logs, audit trails, or monitoring systems in plaintext",
    ("Log scanning for PII", "Data classification of log entries"))

# ── Category 2: Harmful Output (HO) ────────────────────────────────────────────
HO_1 = Subcategory("HO-1", IncidentCategory.HARMFUL_OUTPUT, "Toxic/Abusive Content",
    "Generation of hate speech, harassment, or abusive language",
    ("Toxicity classifier threshold breach", "User reports"))
HO_2 = Subcategory("HO-2", IncidentCategory.HARMFUL_OUTPUT, "Dangerous Instructions",
    "Generation of instructions for illegal activities, weapons, or self-harm",
    ("Safety classifier", "Keyword/pattern matching", "User reports"))
HO_3 = Subcategory("HO-3", IncidentCategory.HARMFUL_OUTPUT, "Discriminatory Output",
    "Outputs that discriminate against protected groups",
    ("Fairness metric breach", "Bias detection", "Demographic parity analysis"))
HO_4 = Subcategory("HO-4", IncidentCategory.HARMFUL_OUTPUT, "Misinformation",
    "Generation of false or misleading information presented as fact",
    ("Fact-checking pipeline", "Confidence calibration", "User reports"))
HO_5 = Subcategory("HO-5", IncidentCategory.HARMFUL_OUTPUT, "Sexual/Explicit Content",
    "Generation of CSAM, non-consensual intimate imagery, or explicit content",
    ("Content safety classifier", "Hash matching", "User reports"))
HO_6 = Subcategory("HO-6", IncidentCategory.HARMFUL_OUTPUT, "Self-Harm Content",
    "Content that encourages or facilitates self-harm or suicide",
    ("Safety classifier", "Crisis detection patterns", "User reports"))

# ── Category 3: Wrong Action by Agent (WA) ────────────────────────────────────
WA_1 = Subcategory("WA-1", IncidentCategory.WRONG_ACTION, "Unauthorized Action",
    "Agent performs an action outside its authorized capability set",
    ("Policy engine denial", "Capability token mismatch", "Action audit trail review"))
WA_2 = Subcategory("WA-2", IncidentCategory.WRONG_ACTION, "Excessive Action",
    "Agent performs actions beyond what is necessary for the task (scope creep)",
    ("Action count anomaly", "Resource consumption spike", "Task-action ratio analysis"))
WA_3 = Subcategory("WA-3", IncidentCategory.WRONG_ACTION, "Failed Required Action",
    "Agent fails to perform a mandatory action (e.g., missing approval step)",
    ("Workflow compliance check", "Approval chain verification", "Step completion audit"))
WA_4 = Subcategory("WA-4", IncidentCategory.WRONG_ACTION, "Irreversible Action",
    "Agent performs an irreversible action (send email, delete data, transfer funds) without required authorization",
    ("Irreversible action detection", "Authorization checkpoint bypass"))
WA_5 = Subcategory("WA-5", IncidentCategory.WRONG_ACTION, "Cascading Action Error",
    "Agent's incorrect action triggers a chain of downstream errors",
    ("Dependency graph analysis", "Error propagation detection", "Multi-system impact assessment"))
WA_6 = Subcategory("WA-6", IncidentCategory.WRONG_ACTION, "Tool Misuse",
    "Agent uses a tool in a manner inconsistent with its intended purpose",
    ("Tool call parameter analysis", "Tool usage pattern anomaly", "OWASP ASI02 mapping"))

# ── Category 4: Hallucination (HL) ────────────────────────────────────────────
HL_1 = Subcategory("HL-1", IncidentCategory.HALLUCINATION, "Factual Fabrication",
    "Model generates false facts, statistics, or claims presented as true",
    ("Fact-checking pipeline", "Grounding score", "Source attribution analysis"))
HL_2 = Subcategory("HL-2", IncidentCategory.HALLUCINATION, "Source Fabrication",
    "Model invents citations, references, or sources that do not exist",
    ("Citation verification", "Reference checking", "Source existence validation"))
HL_3 = Subcategory("HL-3", IncidentCategory.HALLUCINATION, "Contextual Hallucination",
    "Model generates output inconsistent with the provided context or prompt",
    ("Context-output consistency scoring", "Semantic similarity analysis"))
HL_4 = Subcategory("HL-4", IncidentCategory.HALLUCINATION, "Confident Misinformation",
    "Model presents incorrect information with high confidence, increasing risk of user trust",
    ("Confidence calibration analysis", "Confidence-accuracy gap measurement"))
HL_5 = Subcategory("HL-5", IncidentCategory.HALLUCINATION, "Reasoning Hallucination",
    "Model produces flawed reasoning chains that appear logically valid but contain errors",
    ("Reasoning chain verification", "Logical consistency checking"))
HL_6 = Subcategory("HL-6", IncidentCategory.HALLUCINATION, "Data Hallucination",
    "Model generates synthetic data points that appear real but are fabricated",
    ("Data validation", "Statistical distribution analysis", "Provenance verification"))

# ── Category 5: Prompt Injection (PI) ──────────────────────────────────────────
PI_1 = Subcategory("PI-1", IncidentCategory.PROMPT_INJECTION, "Direct Prompt Injection",
    "Attacker directly provides malicious instructions in user input",
    ("Input pattern matching", "Instruction detection classifier", "Anomaly detection"))
PI_2 = Subcategory("PI-2", IncidentCategory.PROMPT_INJECTION, "Indirect Prompt Injection",
    "Malicious instructions embedded in external content (web pages, documents, emails) that the AI processes",
    ("External content scanning", "Instruction extraction detection", "Content provenance analysis"))
PI_3 = Subcategory("PI-3", IncidentCategory.PROMPT_INJECTION, "Jailbreak",
    "Attacker bypasses safety guardrails through adversarial prompting techniques",
    ("Jailbreak pattern detection", "Safety classifier bypass", "Adversarial input detection"))
PI_4 = Subcategory("PI-4", IncidentCategory.PROMPT_INJECTION, "System Prompt Extraction",
    "Attacker extracts the system prompt or hidden instructions",
    ("System prompt leakage detection", "Output analysis for instruction disclosure"))
PI_5 = Subcategory("PI-5", IncidentCategory.PROMPT_INJECTION, "Goal Hijacking",
    "Attacker overrides the AI's original goal or task with a different objective",
    ("Goal consistency monitoring", "Task drift detection", "OWASP ASI01 mapping"))
PI_6 = Subcategory("PI-6", IncidentCategory.PROMPT_INJECTION, "Memory Poisoning",
    "Attacker injects false information into the agent's memory or context that persists across sessions",
    ("Memory integrity verification", "Context consistency checking", "OWASP ASI06 mapping"))

# ── Category 6: Model Poisoning (MP) ───────────────────────────────────────────
MP_1 = Subcategory("MP-1", IncidentCategory.MODEL_POISONING, "Training Data Poisoning",
    "Malicious data injected into training dataset to create backdoors or biases",
    ("Training data anomaly detection", "Data provenance verification", "Statistical distribution analysis"))
MP_2 = Subcategory("MP-2", IncidentCategory.MODEL_POISONING, "Fine-Tuning Poisoning",
    "Malicious data injected during fine-tuning or RLHF phase",
    ("Fine-tuning data audit", "Reward model manipulation detection", "Output behavior analysis"))
MP_3 = Subcategory("MP-3", IncidentCategory.MODEL_POISONING, "Model Backdoor",
    "Model behaves normally on standard inputs but produces attacker-desired outputs on trigger inputs",
    ("Backdoor detection testing", "Trigger input scanning", "Behavioral anomaly detection"))
MP_4 = Subcategory("MP-4", IncidentCategory.MODEL_POISONING, "Supply Chain Poisoning",
    "Compromised pre-trained model, dataset, or dependency introduced via supply chain",
    ("Supply chain verification", "Model provenance checking", "Dependency scanning", "OWASP ASI04 mapping"))
MP_5 = Subcategory("MP-5", IncidentCategory.MODEL_POISONING, "Parameter Tampering",
    "Direct manipulation of model weights or parameters",
    ("Model integrity verification", "Parameter hash comparison", "Behavioral consistency testing"))
MP_6 = Subcategory("MP-6", IncidentCategory.MODEL_POISONING, "Data Label Poisoning",
    "Incorrect or malicious labels in supervised training data",
    ("Label distribution analysis", "Inter-annotator agreement", "Label quality metrics"))

# ── Category 7: Supply Chain (SC) ──────────────────────────────────────────────
SC_1 = Subcategory("SC-1", IncidentCategory.SUPPLY_CHAIN, "Compromised Pre-trained Model",
    "Pre-trained model contains backdoors, biases, or malicious behavior",
    ("Model provenance verification", "Behavioral testing", "Supply chain audit"))
SC_2 = Subcategory("SC-2", IncidentCategory.SUPPLY_CHAIN, "Dataset Compromise",
    "Training or evaluation dataset is corrupted, biased, or contains malicious content",
    ("Dataset integrity verification", "Statistical analysis", "Provenance checking"))
SC_3 = Subcategory("SC-3", IncidentCategory.SUPPLY_CHAIN, "Dependency Vulnerability",
    "AI system depends on a library or package with known vulnerabilities",
    ("Dependency scanning", "CVE matching", "SBOM analysis"))
SC_4 = Subcategory("SC-4", IncidentCategory.SUPPLY_CHAIN, "API Provider Incident",
    "Third-party AI API provider experiences outage, degradation, or security breach",
    ("API health monitoring", "SLA tracking", "Incident correlation"))
SC_5 = Subcategory("SC-5", IncidentCategory.SUPPLY_CHAIN, "Infrastructure Compromise",
    "Cloud infrastructure or compute resources used by AI systems are compromised",
    ("Infrastructure monitoring", "Anomaly detection", "Security event correlation"))

# ── Category 8: Agent Misbehavior (AM) ─────────────────────────────────────────
AM_1 = Subcategory("AM-1", IncidentCategory.AGENT_MISBEHAVIOR, "Goal Drift",
    "Agent's behavior gradually diverges from its original objective",
    ("Goal consistency monitoring", "Task alignment scoring", "Behavioral trajectory analysis"))
AM_2 = Subcategory("AM-2", IncidentCategory.AGENT_MISBEHAVIOR, "Concealment",
    "Agent hides its actions, reasoning, or state from monitoring systems",
    ("Audit trail completeness check", "Action logging verification", "Transparency metric breach"))
AM_3 = Subcategory("AM-3", IncidentCategory.AGENT_MISBEHAVIOR, "Unauthorized Self-Modification",
    "Agent modifies its own code, configuration, or prompts without authorization",
    ("Configuration integrity check", "Self-modification detection", "Change audit trail review"))
AM_4 = Subcategory("AM-4", IncidentCategory.AGENT_MISBEHAVIOR, "Rogue Behavior",
    "Agent acts against organizational interests or safety constraints",
    ("Policy violation detection", "Safety constraint monitoring", "OWASP ASI10 mapping"))
AM_5 = Subcategory("AM-5", IncidentCategory.AGENT_MISBEHAVIOR, "Privilege Escalation",
    "Agent gains access to resources or capabilities beyond its authorization",
    ("Access control audit", "Capability token verification", "Privilege boundary testing"))
AM_6 = Subcategory("AM-6", IncidentCategory.AGENT_MISBEHAVIOR, "Inter-Agent Attack",
    "One agent in a multi-agent system attacks or compromises another agent",
    ("Inter-agent communication monitoring", "Agent behavior correlation", "OWASP ASI07 mapping"))


# ── Registry ───────────────────────────────────────────────────────────────────

SUBCATEGORIES: dict[str, Subcategory] = {
    sub.code: sub
    for sub in [
        DL_1, DL_2, DL_3, DL_4, DL_5, DL_6,
        HO_1, HO_2, HO_3, HO_4, HO_5, HO_6,
        WA_1, WA_2, WA_3, WA_4, WA_5, WA_6,
        HL_1, HL_2, HL_3, HL_4, HL_5, HL_6,
        PI_1, PI_2, PI_3, PI_4, PI_5, PI_6,
        MP_1, MP_2, MP_3, MP_4, MP_5, MP_6,
        SC_1, SC_2, SC_3, SC_4, SC_5,
        AM_1, AM_2, AM_3, AM_4, AM_5, AM_6,
    ]
}

# Minimum severity by subcategory (§4.4)
MINIMUM_SEVERITY: dict[str, Severity] = {
    "DL-1": Severity.S2_HIGH,
    "DL-2": Severity.S2_HIGH,
    "HO-1": Severity.S2_HIGH,
    "HO-2": Severity.S2_HIGH,
    "HO-5": Severity.S2_HIGH,
    "WA-4": Severity.S2_HIGH,
    "PI-3": Severity.S2_HIGH,
    "PI-5": Severity.S2_HIGH,
    "MP-3": Severity.S1_CRITICAL,
    "AM-4": Severity.S1_CRITICAL,
}

# Category-level minimum severity
CATEGORY_MINIMUM_SEVERITY: dict[IncidentCategory, Severity] = {
    IncidentCategory.DATA_LEAKAGE: Severity.S2_HIGH,
    IncidentCategory.HARMFUL_OUTPUT: Severity.S2_HIGH,
    IncidentCategory.WRONG_ACTION: Severity.S2_HIGH,
    IncidentCategory.HALLUCINATION: Severity.S3_MEDIUM,
    IncidentCategory.PROMPT_INJECTION: Severity.S2_HIGH,
    IncidentCategory.MODEL_POISONING: Severity.S1_CRITICAL,
    IncidentCategory.SUPPLY_CHAIN: Severity.S3_MEDIUM,
    IncidentCategory.AGENT_MISBEHAVIOR: Severity.S1_CRITICAL,
}


def get_subcategory(code: str) -> Optional[Subcategory]:
    """Look up a subcategory by its code (e.g., 'DL-1')."""
    return SUBCATEGORIES.get(code)


def get_subcategories_by_category(category: IncidentCategory) -> list[Subcategory]:
    """Return all subcategories for a given category."""
    return [s for s in SUBCATEGORIES.values() if s.category == category]


def get_minimum_severity(subcategory_code: str) -> Optional[Severity]:
    """Return the minimum severity for a subcategory, or None if not defined."""
    return MINIMUM_SEVERITY.get(subcategory_code)
