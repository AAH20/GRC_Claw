# Microsoft Presidio × Hermes Agent — Enterprise PII Protection Integration Guide

**Author:** Ahmed Hassan (CISO)  
**Date:** 2026-10-01  
**Presidio Version:** 2.2.362+ (latest)  
**License:** MIT  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Key Features for Ahmed's Stack](#2-key-features-for-ahmeds-stack)
3. [Integration Guide — Presidio + Hermes Agent](#3-integration-guide--presidio--hermes-agent)
4. [Configuration Examples — Python Code](#4-configuration-examples--python-code)
5. [GDPR/CCPA Compliance Alignment](#5-gdprccpa-compliance-alignment)
6. [Pitfalls and Best Practices](#6-pitfalls-and-best-practices)

---

## 1. Architecture Overview

### What is Presidio?

Presidio (Latin: *praesidium* — "protection, garrison") is Microsoft's open-source data protection and de-identification SDK. It provides **fast identification and anonymization** of private entities in text, images, and structured data.

### Core Modules

| Module | Package | Purpose |
|--------|---------|---------|
| **Analyzer** | `presidio-analyzer` | PII detection in unstructured text |
| **Anonymizer** | `presidio-anonymizer` | De-identification via operators (redact, replace, hash, mask, encrypt) |
| **Image Redactor** | `presidio-image-redactor` | PII redaction in images via OCR (Tesseract) |
| **Structured** | `presidio-structured` | PII detection in tabular/semi-structured data (CSV, JSON) |
| **CLI** | `presidio-cli` | File/directory scanning from command line |

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT SOURCES                             │
│  Unstructured Text │ Images (PNG/JPG/DICOM) │ Structured (CSV/JSON)│
└────────┬──────────────────┬──────────────────────┬───────────────┘
         │                  │                      │
         ▼                  ▼                      ▼
┌─────────────────┐ ┌──────────────────┐ ┌────────────────────────┐
│  AnalyzerEngine │ │ImageRedactorEngine│ │   StructuredEngine     │
│  (spaCy/Stanza/ │ │  (Tesseract OCR + │ │  (Pandas/JSON analysis │
│   Transformers) │ │   AnalyzerEngine) │ │   + AnonymizerEngine)  │
└────────┬────────┘ └────────┬─────────┘ └───────────┬────────────┘
         │                   │                      │
         ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              RecognizerResult List (entity_type, span, score)    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AnonymizerEngine                             │
│  Operators: replace │ redact │ hash │ mask │ encrypt │ custom    │
│  Resolves overlaps → picks highest-scoring operator per entity   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DE-IDENTIFIED OUTPUT                          │
│  <PERSON> │ <EMAIL_ADDRESS> │ <US_SSN> │ <CREDIT_CARD> │ ...   │
└─────────────────────────────────────────────────────────────────┘
```

### Detection Pipeline (AnalyzerEngine)

1. **NLP Engine** processes text → tokens, lemmas, NER entities, POS tags
2. **Recognizer Registry** iterates all registered recognizers:
   - **Pattern-based** (regex + checksum validation) — deterministic, fast
   - **NLP-based** (spaCy/Stanza/Transformers NER) — ML model inference
   - **Deny-list** — exact match against curated word lists
   - **Remote** — delegates to external PII detection services
3. **Context Enhancer** boosts scores when context words found (e.g., "patient" near a name)
4. **Score Threshold** filters results (default 0.6)
5. **Overlap Resolution** — highest score wins; larger span wins on ties

### Anonymization Pipeline (AnonymizerEngine)

1. Receives `RecognizerResult` list from Analyzer
2. Resolves overlapping spans (full overlap → higher score; containment → larger span; partial → concatenate)
3. Applies per-entity operator chain
4. Returns `AnonymizedResult` with cleaned text

---

## 2. Key Features for Ahmed's Stack

### 2.1 NLP + Pattern Matching (Dual Detection)

Presidio combines **two complementary detection strategies**:

| Strategy | Mechanism | Best For | Example |
|----------|-----------|----------|---------|
| **Pattern Matching** | Regex + checksum validation | Structured PII with known formats | Credit cards (Luhn), SSNs, IBANs, phone numbers |
| **NLP/NER** | spaCy/Stanza/Transformers models | Unstructured PII in free text | Person names, organizations, locations |

**Why this matters for Ahmed:** Pattern matching catches what regex can define deterministically (no false negatives on known formats). NLP catches what requires contextual understanding (e.g., "John Smith" vs "Apple Inc."). Together they provide defense-in-depth.

### 2.2 Customizable Pipelines

Five extension points:

1. **Custom Recognizers** — Python classes, YAML config, or ad-hoc API parameters
2. **NLP Engine Swap** — spaCy ↔ Stanza ↔ Transformers (HuggingFace)
3. **Custom Operators** — Python lambdas or classes for anonymization logic
4. **YAML No-Code Config** — recognizer registry without code changes
5. **Third-Party Integrations** — Azure AI Language, Amazon Comprehend, GLiNER, Flair, LangExtract (LLM-based)

### 2.3 Multi-Language Support

```python
configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_lg"},
        {"lang_code": "es", "model_name": "es_core_news_md"},
        {"lang_code": "de", "model_name": "de_core_news_md"},
        {"lang_code": "fr", "model_name": "fr_core_news_md"},
    ],
}
```

### 2.4 Deployment Flexibility

- **Python SDK** — direct library integration
- **Docker** — containerized REST API
- **Kubernetes** — orchestrated deployment
- **PySpark** — big data batch processing
- **Azure Data Factory** — cloud-native pipelines

### 2.5 Supported Entity Types (100+)

Key categories: `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `US_SSN`, `CREDIT_CARD`, `IBAN`, `IP_ADDRESS`, `LOCATION`, `DATE_TIME`, `NRP` (nationality/religion/political), `MEDICAL_LICENSE`, `URL`, `CRYPTO`, `IBAN_CODE`, plus country-specific recognizers for 20+ countries.

### 2.6 LLM-Based PII Detection (LangExtract)

New in 2.2.362+ — uses local LLMs (Ollama) or Azure OpenAI for context-dependent PII detection that regex/NER cannot catch:

```python
from presidio_analyzer.predefined_recognizers import BasicLangExtractRecognizer
recognizer = BasicLangExtractRecognizer()  # Uses Ollama local model
```

---

## 3. Integration Guide — Presidio + Hermes Agent

### 3.1 Hermes Agent's Existing Privacy Features

Hermes Agent already has built-in privacy controls:

| Feature | Config Key | What It Does |
|---------|-----------|--------------|
| **Secret Redaction** | `security.redact_secrets: true` | Masks API keys, tokens, JWTs in tool output and logs |
| **PII Redaction (Gateway)** | `privacy.redact_pii: true` | Hashes user IDs, strips phone numbers from LLM context |
| **Prompt Anonymization** | `privacy.anonymize_prompts: true` | Scrub PII from prompts before model provider, restores in response |
| **MoA Privacy Filter** | `moa.privacy_filter: "display"` or `"full"` | Redacts PII in advisor/reference outputs |

**Key insight:** Hermes's built-in PII redaction is **regex-based** (emails, phones, IPs, tokens). Presidio adds **NLP-powered NER** for person names, organizations, locations, and 100+ entity types that regex cannot reliably detect.

### 3.2 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HERMES AGENT                                  │
│                                                                      │
│  User Input ──► ┌──────────────────────────────────────────────┐    │
│                 │  Hermes Built-in Privacy Layer               │    │
│                 │  (redact.py — secrets, tokens, API keys)     │    │
│                 └──────────────────┬───────────────────────────┘    │
│                                    │                                 │
│                                    ▼                                 │
│                 ┌──────────────────────────────────────────────┐    │
│                 │  Presidio Integration Layer (NEW)            │    │
│                 │  ┌──────────────┐  ┌───────────────────┐    │    │
│                 │  │  Analyzer    │  │  Anonymizer       │    │    │
│                 │  │  Engine      │─►│  Engine           │    │    │
│                 │  │  (NER+Regex) │  │  (redact/replace) │    │    │
│                 │  └──────────────┘  └───────────────────┘    │    │
│                 └──────────────────┬───────────────────────────┘    │
│                                    │                                 │
│                                    ▼                                 │
│                 ┌──────────────────────────────────────────────┐    │
│                 │  LLM Provider (OpenAI/Anthropic/OpenRouter)   │    │
│                 └──────────────────────────────────────────────┘    │
│                                                                      │
│  Tool Output ──► ┌──────────────────────────────────────────────┐   │
│                  │  Presidio Post-Processing                    │   │
│                  │  (scan tool results before logging/storage)  │   │
│                  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Integration Points

There are **three integration points** where Presidio adds value:

#### Integration Point 1: Pre-LLM Prompt Scrubbing (Most Critical)

**Problem:** User messages containing PII (names, emails, SSNs) are sent to LLM providers. Even with Hermes's `anonymize_prompts`, only regex-detectable PII is caught.

**Solution:** Add Presidio as a deeper PII scrubber before the prompt reaches the LLM.

```python
# hermes_presidio_guard.py — Pre-LLM PII scrubber
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class PresidioPromptGuard:
    """Scrub PII from prompts before they reach the LLM provider."""
    
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.operators = {
            "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CC>"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
        }
    
    def scrub(self, text: str) -> tuple[str, dict]:
        """
        Returns: (scrubbed_text, mapping_dict)
        mapping_dict allows restoration of original values in LLM response.
        """
        results = self.analyzer.analyze(
            text=text,
            language="en",
            score_threshold=0.7,
        )
        
        if not results:
            return text, {}
        
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=self.operators,
        )
        
        # Build restoration mapping
        mapping = {}
        for result in results:
            original = text[result.start:result.end]
            mapping[f"<{result.entity_type}>"] = original
        
        return anonymized.text, mapping
```

#### Integration Point 2: Tool Output Scanning (DLP)

**Problem:** Tool outputs (web search results, file reads, command output) may contain PII that gets logged or stored in session history.

**Solution:** Scan tool outputs with Presidio before they enter logs or conversation context.

```python
# hermes_tool_output_scanner.py
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine, OperatorConfig

class ToolOutputScanner:
    """Scan tool outputs for PII before logging/storage."""
    
    def __init__(self, score_threshold: float = 0.75):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.threshold = score_threshold
    
    def scan_and_redact(self, text: str) -> str:
        """Redact any PII found in tool output."""
        results = self.analyzer.analyze(
            text=text,
            language="en",
            score_threshold=self.threshold,
        )
        
        if not results:
            return text
        
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": OperatorConfig("redact", {})},
        )
        
        return anonymized.text
    
    def scan_and_report(self, text: str) -> dict:
        """Scan and return PII findings without redacting (for audit)."""
        results = self.analyzer.analyze(
            text=text,
            language="en",
            score_threshold=self.threshold,
        )
        
        findings = []
        for r in results:
            findings.append({
                "entity_type": r.entity_type,
                "score": r.score,
                "span": (r.start, r.end),
                # Don't include actual value in audit log — that defeats the purpose
            })
        
        return {
            "pii_detected": len(findings) > 0,
            "findings_count": len(findings),
            "findings": findings,
        }
```

#### Integration Point 3: Session Log Scrubbing

**Problem:** Hermes session logs (JSONL) contain full conversation history including PII.

```python
# hermes_log_scrubber.py
import json
from pathlib import Path
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine, OperatorConfig

class SessionLogScrubber:
    """Scrub PII from Hermes session log files."""
    
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
    
    def scrub_log_file(self, log_path: str, output_path: str = None):
        """
        Read a JSONL session log, scrub PII from all string values,
        write scrubbed version.
        """
        if output_path is None:
            output_path = log_path.replace(".jsonl", ".scrubbed.jsonl")
        
        with open(log_path, "r") as f_in, open(output_path, "w") as f_out:
            for line in f_in:
                record = json.loads(line)
                scrubbed = self._scrub_dict(record)
                f_out.write(json.dumps(scrubbed) + "\n")
        
        return output_path
    
    def _scrub_dict(self, obj):
        """Recursively scrub all string values in a dict/list structure."""
        if isinstance(obj, str):
            return self._scrub_text(obj)
        elif isinstance(obj, dict):
            return {k: self._scrub_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._scrub_dict(item) for item in obj]
        return obj
    
    def _scrub_text(self, text: str) -> str:
        results = self.analyzer.analyze(text=text, language="en", score_threshold=0.7)
        if not results:
            return text
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"})},
        )
        return anonymized.text
```

### 3.4 Docker Deployment (Sidecar Pattern)

For production, deploy Presidio as a sidecar service:

```yaml
# docker-compose.yml
version: "3.8"

services:
  presidio-analyzer:
    image: mcr.microsoft.com/presidio-analyzer:latest
    ports:
      - "5002:5002"
    environment:
      - NLP_ENGINE=spacy
  
  presidio-anonymizer:
    image: mcr.microsoft.com/presidio-anonymizer:latest
    ports:
      - "5001:5001"
  
  hermes-agent:
    build: .
    environment:
      - PRESIDIO_ANALYZER_URL=http://presidio-analyzer:5002
      - PRESIDIO_ANONYMIZER_URL=http://presidio-anonymizer:5001
    depends_on:
      - presidio-analyzer
      - presidio-anonymizer
```

### 3.5 Hermes Config Integration

Add Presidio settings to `~/.hermes/config.yaml`:

```yaml
# ~/.hermes/config.yaml — Add these sections

# Existing Hermes privacy settings
privacy:
  redact_pii: true              # Built-in regex PII redaction
  anonymize_prompts: true       # Built-in prompt anonymization
  scrub_emails: true
  scrub_tokens: true
  scrub_ips: true
  scrub_phones: true

# Presidio integration (new)
presidio:
  enabled: true
  mode: "sidecar"               # "sdk" (in-process) or "sidecar" (HTTP service)
  analyzer_url: "http://localhost:5002"
  anonymizer_url: "http://localhost:5001"
  score_threshold: 0.7          # 0.0-1.0, higher = fewer false positives
  entities:                     # Restrict to specific entity types
    - PERSON
    - EMAIL_ADDRESS
    - PHONE_NUMBER
    - US_SSN
    - CREDIT_CARD
    - LOCATION
    - DATE_TIME
  default_operator: "replace"   # replace, redact, hash, mask, encrypt
  scrub_tool_outputs: true      # Scan tool results before logging
  scrub_session_logs: true      # Scan session logs before storage
  scrub_memory: true            # Scan memories before persistence
  audit_log: true               # Log PII detection events (without values)
```

---

## 4. Configuration Examples — Python Code

### 4.1 Basic PII Scanning

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Initialize engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Sample text with PII
text = """
Customer John Smith (SSN: 123-45-6789) called from 212-555-5555.
Email: john.smith@example.com. Credit card: 4111-1111-1111-1111.
Lives at 123 Main Street, New York, NY 10001.
"""

# Step 1: Analyze — detect PII entities
results = analyzer.analyze(
    text=text,
    language="en",
    score_threshold=0.6,
)

print("Detected PII entities:")
for r in results:
    print(f"  {r.entity_type}: '{text[r.start:r.end]}' (confidence: {r.score:.2f})")

# Step 2: Anonymize — redact detected PII
operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
    "US_SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
    "CREDIT_CARD": OperatorConfig("mask", {
        "masking_char": "*",
        "chars_to_mask": 16,
        "from_end": False,
    }),
    "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
}

anonymized = anonymizer.anonymize(
    text=text,
    analyzer_results=results,
    operators=operators,
)

print(f"\nAnonymized text:\n{anonymized.text}")
```

### 4.2 Custom Recognizer for Internal IDs

```python
from presidio_analyzer import PatternRecognizer, Pattern

# Detect internal employee badge numbers (format: EMP-XXXXX)
employee_id_pattern = Pattern(
    name="employee_id_pattern",
    regex=r"\bEMP-\d{5}\b",
    score=0.9,
)

employee_recognizer = PatternRecognizer(
    supported_entity="EMPLOYEE_ID",
    patterns=[employee_id_pattern],
    context=["employee", "badge", "staff id", "worker"],
)

# Detect internal project codenames
project_recognizer = PatternRecognizer(
    supported_entity="INTERNAL_PROJECT",
    deny_list=["Titan", "Sapphire", "Nightingale", "Ironclad"],
    deny_list_score=1.0,
)

# Register with analyzer
analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(employee_recognizer)
analyzer.registry.add_recognizer(project_recognizer)

# Now these will be detected
text = "Employee EMP-12345 worked on Project Titan."
results = analyzer.analyze(text=text, language="en")
```

### 4.3 YAML-Based Recognizer Configuration (No-Code)

```yaml
# custom_recognizers.yaml
recognizers:
  - name: "Employee ID Recognizer"
    supported_language: "en"
    supported_entity: "EMPLOYEE_ID"
    patterns:
      - name: "emp_id"
        regex: "\\bEMP-\\d{5}\\b"
        score: 0.9
    context:
      - "employee"
      - "badge"
      - "staff"

  - name: "Project Code Recognizer"
    supported_language: "en"
    supported_entity: "INTERNAL_PROJECT"
    deny_list:
      - "Titan"
      - "Sapphire"
      - "Nightingale"
    deny_list_score: 1.0

  - name: "Policy Number Recognizer"
    supported_language: "en"
    supported_entity: "POLICY_NUMBER"
    patterns:
      - name: "policy_format"
        regex: "\\bPOL-[A-Z]{2}-\\d{6}\\b"
        score: 0.95
    context:
      - "policy"
      - "insurance"
      - "claim"
```

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

registry_provider = RecognizerRegistryProvider(
    conf_file="custom_recognizers.yaml"
)
analyzer = AnalyzerEngine(
    registry=registry_provider.create_recognizer_registry()
)
```

### 4.4 Multi-Language Configuration

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_lg"},
        {"lang_code": "es", "model_name": "es_core_news_md"},
        {"lang_code": "de", "model_name": "de_core_news_md"},
        {"lang_code": "fr", "model_name": "fr_core_news_md"},
    ],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    supported_languages=["en", "es", "de", "fr"],
)

# Analyze in different languages
results_en = analyzer.analyze(text="My name is John Smith", language="en")
results_es = analyzer.analyze(text="Me llamo Juan García", language="es")
```

### 4.5 Structured Data (CSV/JSON) Scanning

```python
import pandas as pd
from presidio_structured import StructuredEngine, PandasAnalysisBuilder
from presidio_anonymizer.entities import OperatorConfig

# Initialize
pandas_engine = StructuredEngine()

# Sample data
df = pd.DataFrame({
    "name": ["John Doe", "Jane Smith"],
    "email": ["john@example.com", "jane@example.com"],
    "ssn": ["123-45-6789", "987-65-4321"],
    "department": ["Engineering", "Marketing"],  # Not PII
})

# Auto-detect PII columns
tabular_analysis = PandasAnalysisBuilder().generate_analysis(df)
print(tabular_analysis)
# Output: {'name': 'PERSON', 'email': 'EMAIL_ADDRESS', 'ssn': 'US_SSN'}

# Anonymize
operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
    "US_SSN": OperatorConfig("hash", {"hash_type": "sha256"}),
}

anonymized_df = pandas_engine.anonymize(
    df, tabular_analysis, operators=operators
)
print(anonymized_df)
```

### 4.6 Reversible Anonymization (Encrypt/Decrypt)

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine, DeanonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, DecryptorConfig

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()
deanonymizer = DeanonymizerEngine()

text = "Patient John Doe, SSN 123-45-6789"

# Anonymize with encryption (reversible)
results = analyzer.analyze(text=text, language="en")
anonymized = anonymizer.anonymize(
    text=text,
    analyzer_results=results,
    operators={
        "PERSON": OperatorConfig("encrypt", {"key": "my-secret-key-16chars"}),
        "US_SSN": OperatorConfig("encrypt", {"key": "my-secret-key-16chars"}),
    },
)
print(f"Encrypted: {anonymized.text}")

# Deanonymize (when authorized)
deanonymized = deanonymizer.deanonymize(
    text=anonymized.text,
    entities=anonymized.items,
    decryptor_configs=[
        DecryptorConfig(key="my-secret-key-16chars")
    ],
)
print(f"Decrypted: {deanonymized.text}")
```

### 4.7 Batch Processing for Large Datasets

```python
from presidio_analyzer import BatchAnalyzerEngine
from presidio_anonymizer import BatchAnonymizerEngine
import pandas as pd

batch_analyzer = BatchAnalyzerEngine()
batch_anonymizer = BatchAnonymizerEngine()

df = pd.read_csv("customer_data.csv")

# Analyze entire column
results = batch_analyzer.analyze(
    df["free_text_column"],
    language="en",
    score_threshold=0.7,
)

# Anonymize
anonymized = batch_anonymizer.anonymize(
    df,
    results,
    operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"})},
)
```

### 4.8 Image Redaction

```python
from PIL import Image
from presidio_image_redactor import ImageRedactorEngine

image = Image.open("document_with_pii.png")
engine = ImageRedactorEngine()

# Redact PII regions with a fill color
redacted_image = engine.redact(image, fill=(255, 255, 255))  # White out
redacted_image.save("redacted.png")

# Or get bounding boxes for audit
redacted_image, bboxes = engine.redact_and_return_bbox(
    image, fill=(255, 255, 255)
)
print(f"Redacted {len(bboxes)} PII regions")
```

---

## 5. GDPR/CCPA Compliance Alignment

### 5.1 GDPR Alignment

| GDPR Requirement | Presidio Capability | How It Helps |
|-----------------|---------------------|--------------|
| **Art. 5(1)(c) — Data Minimization** | Anonymizer operators (redact, replace) | Minimize PII in processing pipelines |
| **Art. 5(1)(f) — Integrity & Confidentiality** | Encrypt operator (AES) | Protect PII with encryption at rest |
| **Art. 25 — Data Protection by Design** | Custom recognizers, configurable pipelines | Build privacy into system architecture |
| **Art. 32 — Security of Processing** | Hash operator (SHA-256/512) | Pseudonymization per Art. 4(5) |
| **Art. 35 — DPIA** | Audit logging of PII detections | Document processing activities |
| **Art. 17 — Right to Erasure** | Redact operator | Complete removal of PII from text |
| **Art. 20 — Data Portability** | Structured data anonymization | Export data without PII |
| **Art. 44-49 — International Transfers** | On-premises deployment | No data leaves infrastructure |

### 5.2 CCPA Alignment

| CCPA Requirement | Presidio Capability | How It Helps |
|-----------------|---------------------|--------------|
| **§1798.100 — Right to Know** | Analyzer detects all PII categories | Identify what personal info is collected |
| **§1798.105 — Right to Delete** | Redact operator | Remove PII from records |
| **§1798.110 — Right to Opt-Out** | Custom recognizers for sale tracking | Detect data sharing patterns |
| **§1798.150 — Data Breach** | Audit logging | Document what PII was exposed |
| **§1798.140 — "Personal Information"** | 100+ entity types detected | Covers CCPA's broad PI definition |

### 5.3 Compliance Mapping Table

```
┌────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE FRAMEWORK                             │
├──────────────┬─────────────────────────────────────────────────────┤
│ GDPR Art. 4  │ Pseudonymization: hash/encrypt operators           │
│ GDPR Art. 17 │ Right to erasure: redact operator                   │
│ GDPR Art. 25 │ Privacy by design: configurable pipelines           │
│ GDPR Art. 32 │ Security: AES encryption, SHA-256 hashing           │
│ GDPR Art. 35 │ DPIA: audit logging of detection events             │
│ CCPA 1798.100│ Right to know: comprehensive PII detection           │
│ CCPA 1798.105│ Right to delete: redact operator                    │
│ HIPAA        │ PHI detection: medical license, health entities     │
│ PCI-DSS      │ Credit card detection: Luhn checksum validation     │
│ SOC 2        │ Audit trail: detection event logging                │
└──────────────┴─────────────────────────────────────────────────────┘
```

### 5.4 Important Compliance Caveats

> **Presidio is a tool, not a compliance solution.** It helps with technical measures but does not itself ensure compliance. You still need:
> - Legal review of data processing activities
> - Data Processing Agreements (DPAs) with subprocessors
> - Privacy policies and consent mechanisms
> - Data retention policies
> - Breach notification procedures
> - Regular audits and DPIAs

---

## 6. Pitfalls and Best Practices

### 6.1 Common Pitfalls

#### Pitfall 1: False Positives on Short Numeric Patterns

```python
# BAD: Overly broad pattern matches too much
bad_pattern = Pattern(name="weak", regex=r"\d{9}", score=0.9)
# This matches ANY 9-digit number — phone numbers, order IDs, dates

# GOOD: Use checksum validation and context
from presidio_analyzer import PatternRecognizer

good_recognizer = PatternRecognizer(
    supported_entity="US_SSN",
    patterns=[Pattern(name="ssn", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=0.3)],
    context=["ssn", "social", "security", "tax"],
    # Context words boost score only when nearby
)
```

#### Pitfall 2: Missing spaCy Model Download

```python
# BAD: Forgetting to download the NLP model
# AnalyzerEngine() initializes but NER recognizer silently fails
# You only get regex results — person names are missed!

# GOOD: Always download models first
# python -m spacy download en_core_web_lg

# Verify setup:
analyzer = AnalyzerEngine()
results = analyzer.analyze(text="My name is John Smith", language="en")
# Should detect PERSON entity — if not, model is missing
```

#### Pitfall 3: Not Handling Overlapping Entities

```python
# When "John Smith" is detected as both PERSON and part of a larger ORGANIZATION,
# Presidio resolves overlaps automatically, but you should verify behavior:

text = "John Smith from Microsoft called"
results = analyzer.analyze(text=text, language="en")
# PERSON: "John Smith" (score 0.85)
# ORGANIZATION: "Microsoft" (score 0.80)
# These don't overlap, so both are returned

# But for "Microsoft John Smith":
# PERSON might span "Microsoft John Smith" — check your results
```

#### Pitfall 4: Exposing Presidio API Without Authentication

```python
# BAD: Presidio's REST API has NO built-in authentication
# Never expose it directly to untrusted networks

# GOOD: Put it behind an authenticated gateway
# Option 1: Use SDK mode (in-process) instead of HTTP
# Option 2: Add nginx reverse proxy with auth
# Option 3: Deploy in a private network / Kubernetes service mesh
```

#### Pitfall 5: Not Tuning the Score Threshold

```python
# Default threshold is 0.6 — may not be right for your data

# For high-security (fewer false negatives, more false positives):
results = analyzer.analyze(text=text, score_threshold=0.5)

# For high-precision (fewer false positives, may miss some PII):
results = analyzer.analyze(text=text, score_threshold=0.8)

# RECOMMENDATION: Start at 0.7, evaluate on your dataset, then tune
```

#### Pitfall 6: YAML Recognizers Can't Include Checksum Logic

```python
# YAML configuration supports regex + context ONLY
# If you need checksum validation (e.g., for Korean RRN, credit cards),
# you MUST implement a Python-based recognizer

# BAD: Trying to put checksum in YAML (not supported)
# GOOD: Implement PatternRecognizer subclass with validate_result method
```

#### Pitfall 7: Not Evaluating on Your Data

```python
# Always evaluate Presidio on YOUR dataset before production deployment

from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

# Test on representative samples
test_cases = [
    ("My name is John Smith", ["PERSON"]),
    ("Call me at 212-555-5555", ["PHONE_NUMBER"]),
    ("SSN: 123-45-6789", ["US_SSN"]),
    # Add your own edge cases
]

for text, expected_entities in test_cases:
    results = analyzer.analyze(text=text, language="en")
    detected = [r.entity_type for r in results]
    print(f"Text: {text}")
    print(f"  Expected: {expected_entities}")
    print(f"  Detected: {detected}")
    print(f"  Match: {set(expected_entities) == set(detected)}")
```

### 6.2 Best Practices

#### Performance

| Practice | Recommendation |
|----------|---------------|
| **Recognizer execution** | Keep under 100ms per 100 tokens |
| **NLP model choice** | spaCy for speed, Transformers for accuracy |
| **Batch processing** | Use `BatchAnalyzerEngine` for large datasets |
| **Caching** | Cache `AnalyzerEngine` instance — don't recreate per request |
| **GPU acceleration** | Use `cupy-cuda12x` on Linux; Apple Silicon falls back to CPU |

#### Accuracy

| Practice | Recommendation |
|----------|---------------|
| **Start with defaults** | Use default spaCy model, tune later |
| **Add context words** | Domain-specific context boosts precision |
| **Use checksums** | Luhn for credit cards, IBAN validation for bank accounts |
| **Layer detection** | Regex for format + NER for context + deny-list for known values |
| **Evaluate iteratively** | Use presidio-research toolkit for F2.5 scoring |
| **Combine with SaaS** | Use Presidio + Azure AI Language in parallel for best coverage |

#### Security

| Practice | Recommendation |
|----------|---------------|
| **Deploy in private network** | Don't expose Presidio API publicly |
| **Use SDK mode** | In-process is safer than HTTP service |
| **Rotate encryption keys** | If using encrypt operator, implement key rotation |
| **Audit logging** | Log detection events (entity type, score) — never log values |
| **Memory safety** | Clear PII from memory after processing |
| **Dependency isolation** | Custom recognizers with conflicting deps → RemoteRecognizer |

#### Configuration Management

| Practice | Recommendation |
|----------|---------------|
| **Version control** | Store recognizer configs in Git |
| **Environment-specific** | Different models per env (dev/staging/prod) |
| **YAML for teams** | Non-developers can update recognizer lists |
| **Python for complex logic** | Checksums, custom validation → Python classes |
| **Ad-hoc for testing** | Per-request recognizers for experimentation |

### 6.3 Recommended Production Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION DEPLOYMENT                           │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   Hermes     │    │  Presidio    │    │   Audit Log          │  │
│  │   Agent      │◄──►│  Sidecar     │    │   (SIEM/Splunk)      │  │
│  │              │    │  (Docker)    │    │                      │  │
│  │  - SDK mode  │    │              │    │  - Entity types      │  │
│  │  - In-process│    │  - Analyzer  │    │  - Confidence scores │  │
│  │  - No network│    │  - Anonymizer│    │  - Timestamps        │  │
│  │              │    │              │    │  - NO PII values     │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│         │                                           ▲              │
│         │                                           │              │
│         ▼                                           │              │
│  ┌──────────────┐                           ┌──────────────────┐   │
│  │   LLM        │                           │   Key Manager    │   │
│  │   Provider   │                           │   (HashiCorp     │   │
│  │              │                           │    Vault)        │   │
│  │  - No PII    │                           │                  │   │
│  │  - Encrypted │                           │  - AES keys      │   │
│  │  - Audited   │                           │  - Rotation      │   │
│  └──────────────┘                           └──────────────────┘   │
│                                                                      │
│  Data Flow:                                                          │
│  1. User input → Hermes redact.py (secrets) → Presidio (PII) → LLM  │
│  2. LLM response → Presidio scan → Hermes redact.py → User          │
│  3. Tool output → Presidio scan → Audit log → Storage               │
│  4. Session logs → Presidio scrub → Encrypted storage               │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.4 Quick-Start Checklist for Ahmed

- [ ] Install Presidio: `pip install presidio-analyzer presidio-anonymizer`
- [ ] Download spaCy model: `python -m spacy download en_core_web_lg`
- [ ] Enable Hermes built-in privacy: `hermes config set privacy.redact_pii true`
- [ ] Enable prompt anonymization: `hermes config set privacy.anonymize_prompts true`
- [ ] Deploy Presidio sidecar (Docker) or use SDK mode
- [ ] Configure custom recognizers for internal ID formats
- [ ] Set score threshold based on evaluation (start at 0.7)
- [ ] Set up audit logging (entity types + scores, never values)
- [ ] Evaluate on representative dataset before production
- [ ] Document DPIA with Presidio as technical measure
- [ ] Establish key management for encrypt operator
- [ ] Set up log scrubbing pipeline for session logs
- [ ] Schedule quarterly re-evaluation of detection accuracy

---

## Appendix A: Installation

```bash
# Core packages
pip install presidio-analyzer presidio-anonymizer

# NLP model
python -m spacy download en_core_web_lg

# Optional: Image redaction
pip install presidio-image-redactor
# Requires: brew install tesseract (macOS) or apt install tesseract-ocr (Linux)

# Optional: Structured data
pip install presidio-structured

# Optional: LLM-based detection
pip install presidio-analyzer[langextract]

# Optional: CLI
pip install presidio-cli
```

## Appendix B: Supported Entities (Selected)

| Category | Entities |
|----------|----------|
| **Person** | PERSON, TITLE |
| **Contact** | EMAIL_ADDRESS, PHONE_NUMBER, URL |
| **Financial** | CREDIT_CARD, IBAN_CODE, US_BANK_NUMBER, CRYPTO |
| **Government ID** | US_SSN, US_PASSPORT, US_DRIVER_LICENSE, NRP |
| **Location** | LOCATION, GPE, FACILITY |
| **Network** | IP_ADDRESS, MAC_ADDRESS, DOMAIN_NAME |
| **Date/Time** | DATE_TIME |
| **Medical** | MEDICAL_LICENSE, US_DEA_NUMBER |
| **Organization** | ORGANIZATION |

## Appendix C: Key References

- Presidio GitHub: https://github.com/microsoft/presidio
- Presidio Docs: https://microsoft.github.io/presidio/
- Presidio Demo: https://huggingface.co/spaces/presidio/presidio_demo
- Presidio Research: https://github.com/microsoft/presidio-research
- Hermes Agent Docs: https://hermes-agent.nousresearch.com/docs
- Hermes Privacy Config: `hermes config set privacy.redact_pii true`

---

*This guide is a living document. Update as Presidio and Hermes Agent evolve.*
