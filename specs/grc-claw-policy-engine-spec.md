# GRC_Claw Policy Engine Specification

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Supersedes:** —  
**Related:** GRC_Claw Reference Architecture §3.1, GRC_Claw Technical Spec §7, GRC_Claw API Spec §7.1

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Architecture Overview](#2-architecture-overview)
3. [Policy DSL Grammar (EBNF)](#3-policy-dsl-grammar-ebnf)
4. [Policy Compilation Pipeline](#4-policy-compilation-pipeline)
5. [Policy Conflict Detection](#5-policy-conflict-detection)
6. [Policy Impact Analysis](#6-policy-impact-analysis)
7. [Policy Testing Framework](#7-policy-testing-framework)
8. [Policy Performance Optimization](#8-policy-performance-optimization)
9. [Data Models](#9-data-models)
10. [API Contracts](#10-api-contracts)
11. [Appendices](#11-appendices)

---

## 1. Purpose & Scope

This specification deepens the GRC_Claw Policy Engine beyond the high-level architecture defined in the Reference Architecture (§3.1) and Technical Specification (§7). It provides concrete implementation details for:

- A complete **policy DSL grammar** in Extended Backus-Naur Form (EBNF)
- A **compilation pipeline** that transforms Cedar → Rego → WASM
- A **conflict detection algorithm** for identifying policy contradictions
- An **impact analysis methodology** for pre-deployment assessment
- A **testing framework** with property-based testing support
- **Performance optimization strategies** for sub-millisecond evaluation

**In scope:**
- Cedar policy language grammar and semantics
- Cedar-to-Rego translation rules
- Rego-to-WASM compilation
- Conflict detection algorithms (syntactic + semantic)
- Impact analysis (blast radius, affected agents, decision distribution)
- Property-based testing with Hypothesis/fast-check
- Performance optimization (caching, indexing, lazy evaluation)

**Out of scope:**
- Evidence collection pipeline (covered by GRC_Claw Evidence Spec)
- Compliance mapping (covered by GRC_Claw Compliance Mapping Spec)
- Agent identity lifecycle (covered by GRC_Claw Agent Governance Spec)

---

## 2. Architecture Overview

### 2.1 Policy Engine Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GRC_Claw Policy Engine                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     POLICY DEFINITION LAYER                          │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │  Cedar       │  │  Rego        │  │  Policy DSL              │  │   │
│  │  │  Parser      │  │  Parser      │  │  (EBNF Grammar)          │  │   │
│  │  │  (Rust FFI)  │  │  (Go/WASM)   │  │                          │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │   │
│  │         │                 │                        │                 │   │
│  │         └────────────────┬┴────────────────────────┘                 │   │
│  │                          ▼                                           │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │              POLICY COMPILER (Cedar → Rego → WASM)             │  │   │
│  │  │                                                                │  │   │
│  │  │  Cedar AST ──► Intermediate Representation ──► Rego AST         │  │   │
│  │  │       │              │                        │                │  │   │
│  │  │       ▼              ▼                        ▼                │  │   │
│  │  │  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │  │   │
│  │  │  │ Cedar   │   │   IR     │   │  Rego    │   │  WASM    │    │  │   │
│  │  │  │ Schema  │   │ Validator│   │  Compiler│   │  Module  │    │  │   │
│  │  │  │ Check   │   │          │   │          │   │          │    │  │   │
│  │  │  └─────────┘   └──────────┘   └──────────┘   └──────────┘    │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                          │                                           │   │
│  │                          ▼                                           │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │              CONFLICT DETECTION ENGINE                         │  │   │
│  │  │                                                                │  │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │   │
│  │  │  │  Syntactic   │  │  Semantic    │  │  Temporal            │ │  │   │
│  │  │  │  Analyzer    │  │  Analyzer    │  │  Analyzer            │ │  │   │
│  │  │  │  (AST diff)  │  │  (SAT/SMT)   │  │  (effective dates)   │ │  │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                          │                                           │   │
│  │                          ▼                                           │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │              IMPACT ANALYSIS ENGINE                            │  │   │
│  │  │                                                                │  │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │   │
│  │  │  │  Blast       │  │  Decision    │  │  Dependency          │ │  │   │
│  │  │  │  Radius      │  │  Simulation  │  │  Graph Traversal     │ │  │   │
│  │  │  │  Calculator  │  │  Engine      │  │  (Neo4j/AGE)         │ │  │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                          │                                           │   │
│  │                          ▼                                           │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │              POLICY DECISION POINT (PDP)                       │  │   │
│  │  │                                                                │  │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │   │
│  │  │  │  Cedar       │  │  Rego        │  │  Decision            │ │  │   │
│  │  │  │  Evaluator   │  │  Evaluator   │  │  Aggregator          │ │  │   │
│  │  │  │  (Rust SDK)  │  │  (WASM/Go)   │  │  (5-way logic)       │ │  │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │  │   │
│  │  │                                                                │  │   │
│  │  │  Decision: {verdict, policy_id, evidence_hash, context, ts}   │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     TESTING FRAMEWORK                                │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │  Unit Tests  │  │  Property-   │  │  Integration            │  │   │
│  │  │  (pytest)    │  │  Based Tests │  │  Tests (OPA + Cedar)    │  │   │
│  │  │              │  │  (Hypothesis)│  │                          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │  Conflict    │  │  Impact      │  │  Performance            │  │   │
│  │  │  Tests       │  │  Tests       │  │  Benchmarks              │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Cedar Parser | Rust `cedar-policy` crate via FFI | Formal verification, sub-ms evaluation |
| Rego Parser | OPA Go SDK / `opa` CLI | Mature ecosystem, WASM compilation |
| IR Validator | Rust | Type safety, performance |
| Conflict Detection | Z3 SMT solver (via Python bindings) | SAT-based contradiction detection |
| Impact Analysis | Python + NetworkX | Graph algorithms, rapid prototyping |
| Testing | pytest + Hypothesis | Property-based testing, Python ecosystem |
| WASM Runtime | Wasmtime (Rust) | Sandboxed, near-native performance |
| Policy Store | PostgreSQL + S3 | Versioned, auditable, scalable |
| Dependency Graph | Neo4j / Apache AGE | Native graph, Cypher queries |
| Decision Cache | Redis | Sub-ms lookup, TTL support |

---

## 3. Policy DSL Grammar (EBNF)

### 3.1 Complete EBNF Grammar

The GRC_Claw Policy DSL is a superset of Cedar with GRC-specific extensions for agent governance. The grammar is defined in Extended Backus-Naur Form (EBNF) following ISO/IEC 14977.

```ebnf
(* ============================================================ *)
(* GRC_Claw Policy DSL — Complete EBNF Grammar                  *)
(* Version: 1.0                                                 *)
(* ============================================================ *)

(* --- Top-Level Policy Document --- *)

policy-document    = policy-header, { policy-element } ;

policy-header      = "@grcclaw", "(", 
                     "version", "=", version-string, ",",
                     "id", "=", policy-id, ",",
                     "owner", "=", entity-id, ","
                     "frameworks", "=", framework-list,
                     ")" ;

version-string     = '"', major, ".", minor, ".", patch, '"' ;
major              = digit, { digit } ;
minor              = digit, { digit } ;
patch              = digit, { digit } ;

policy-id          = '"', { policy-id-char }, '"' ;
policy-id-char     = letter | digit | "-" | "_" ;

framework-list     = "[", [ framework-id, { ",", framework-id } ], "]" ;
framework-id       = '"', { framework-id-char }, '"' ;
framework-id-char  = letter | digit | "-" | "." ;

entity-id          = '"', { entity-id-char }, '"' ;
entity-id-char     = letter | digit | "-" | "_" | ":" | "/" ;

(* --- Policy Elements --- *)

policy-element     = permit-declaration
                   | forbid-declaration
                   | when-clause
                   | unless-clause
                   | condition-block
                   | rule-declaration
                   | scope-declaration
                   | override-declaration ;

(* --- Effect Declarations --- *)

permit-declaration = "permit", "(", 
                     principal-expr, ",", 
                     action-expr, ",", 
                     resource-expr, ")",
                     [ when-clause ],
                     [ unless-clause ], ";" ;

forbid-declaration = "forbid", "(", 
                     principal-expr, ",", 
                     action-expr, ",", 
                     resource-expr, ")",
                     [ when-clause ],
                     [ unless-clause ], ";" ;

(* --- Principal Expression --- *)

principal-expr     = "principal"
                   | "principal", "in", entity-type, "::", entity-name
                   | "principal", "in", entity-group
                   | "principal", "==", entity-type, "::", entity-name ;

entity-type        = identifier ;
entity-name        = '"', { entity-name-char }, '"' ;
entity-name-char   = letter | digit | "-" | "_" | "." ;
entity-group      = '"', { entity-group-char }, '"' ;
entity-group-char  = letter | digit | "-" | "_" | ":" | "/" ;

(* --- Action Expression --- *)

action-expr        = "action"
                   | "action", "==", action-name
                   | "action", "in", action-set
                   | "action", "in", action-hierarchy ;

action-name        = '"', { action-name-char }, '"' ;
action-name-char   = letter | digit | "-" | "_" ;
action-set         = "[", [ action-name, { ",", action-name } ], "]" ;
action-hierarchy   = action-name, "::*", [ "*" ] ;

(* --- Resource Expression --- *)

resource-expr      = "resource"
                   | "resource", "in", entity-type, "::", entity-name
                   | "resource", "in", resource-group
                   | "resource", "==", entity-type, "::", entity-name ;

resource-group     = '"', { resource-group-char }, '"' ;
resource-group-char = letter | digit | "-" | "_" | ":" | "/" | "*" ;

(* --- Context Expression --- *)

context-expr       = "context"
                   | "context", ".", context-field
                   | "context", ".", context-field, "in", value-set ;

context-field      = identifier, { ".", identifier } ;

(* --- When/Unless Clauses --- *)

when-clause        = "when", "{", condition, "}" ;
unless-clause      = "unless", "{", condition, "}" ;

condition          = or-condition ;
or-condition        = and-condition, { "||", and-condition } ;
and-condition      = not-condition, { "&&", not-condition } ;
not-condition      = [ "!", ], comparison-expr ;
comparison-expr    = primary-expr, [ comparison-operator, primary-expr ] ;

comparison-operator = "==" | "!=" | "<" | "<=" | ">" | ">=" 
                    | "in" | "contains" | "startsWith" | "endsWith"
                    | "matches" ;

primary-expr       = literal
                   | entity-ref
                   | context-expr
                   | "(", condition, ")"
                   | function-call
                   | if-expr ;

(* --- Literals --- *)

literal            = string-literal
                   | integer-literal
                   | double-literal
                   | boolean-literal
                   | ip-literal
                   | datetime-literal
                   | duration-literal
                   | set-literal
                   | record-literal ;

string-literal     = '"', { string-char }, '"' ;
string-char        = letter | digit | "-" | "_" | "." | ":" | "/" | "*" | "@" ;
integer-literal    = [ "-" ], digit, { digit } ;
double-literal     = [ "-" ], digit, { digit }, ".", digit, { digit } ;
boolean-literal    = "true" | "false" ;
ip-literal         = '"', octet, ".", octet, ".", octet, ".", octet, 
                     [ "/", prefix-len ], '"' ;
octet              = digit, { digit } ;
prefix-len         = digit, { digit } ;
datetime-literal   = '"', year, "-", month, "-", day, 
                     "T", hour, ":", minute, ":", second, 
                     [ ".", fraction ], "Z", '"' ;
year               = digit, digit, digit, digit ;
month              = digit, digit ;
day                = digit, digit ;
hour               = digit, digit ;
minute             = digit, digit ;
second             = digit, digit ;
fraction           = digit, { digit } ;
duration-literal   = '"', integer-literal, duration-unit, '"' ;
duration-unit      = "s" | "m" | "h" | "d" | "w" ;
set-literal        = "[", [ primary-expr, { ",", primary-expr } ], "]" ;
record-literal     = "{", [ record-field, { ",", record-field } ], "}" ;
record-field       = identifier, ":", primary-expr ;

(* --- Entity References --- *)

entity-ref         = entity-type, "::", entity-name ;
entity-type        = identifier ;
entity-name        = '"', { entity-name-char }, '"' ;

(* --- Function Calls --- *)

function-call      = identifier, "(", [ argument-list ], ")" ;
argument-list      = primary-expr, { ",", primary-expr } ;

(* --- Conditional Expressions --- *)

if-expr            = "if", condition, "then", primary-expr, 
                     "else", primary-expr ;

(* --- Rule Declarations (GRC Extension) --- *)

rule-declaration   = "rule", identifier, "{",
                     "when", condition, ",",
                     "effect", "=", rule-effect, ",",
                     [ "priority", "=", integer-literal, "," ],
                     [ "approvers", "=", approver-list, "," ],
                     [ "limit", "=", rate-limit-expr, "," ],
                     [ "metadata", "=", record-literal, "," ],
                     "}" ;

rule-effect        = "allow" | "deny" | "warn" | "require_approval" 
                   | "transform" | "escalate" | "throttle" | "log" ;

approver-list      = "[", [ approver, { ",", approver } ], "]" ;
approver           = '"', { approver-char }, '"' ;
approver-char      = letter | digit | "-" | "_" | ":" | "@" ;

rate-limit-expr    = integer-literal, "/", rate-limit-unit ;
rate-limit-unit    = "second" | "minute" | "hour" | "day" | "week" ;

(* --- Scope Declarations (GRC Extension) --- *)

scope-declaration  = "scope", "{",
                     [ "agents", "=", agent-set, "," ],
                     [ "resources", "=", resource-set, "," ],
                     [ "environments", "=", environment-set, "," ],
                     [ "risk-tiers", "=", risk-tier-set, "," ],
                     [ "time-window", "=", time-window-expr, "," ],
                     "}" ;

agent-set          = "all" | "[", [ entity-ref, { ",", entity-ref } ], "]" ;
resource-set       = "all" | "[", [ resource-group, { ",", resource-group } ], "]" ;
environment-set    = "[", [ environment, { ",", environment } ], "]" ;
environment        = "production" | "staging" | "development" | "testing" ;
risk-tier-set      = "[", [ risk-tier, { ",", risk-tier } ], "]" ;
risk-tier          = "prohibited" | "high" | "limited" | "minimal" ;

time-window-expr   = "{", "start", "=", datetime-literal, ",",
                     "end", "=", datetime-literal, "}" ;

(* --- Override Declarations (GRC Extension) --- *)

override-declaration = "override", "(", 
                       "target", "=", policy-id, ",",
                       "strategy", "=", override-strategy,
                       ")" ;

override-strategy  = "deny_overrides" | "allow_overrides" 
                   | "first_match" | "priority_order" ;

(* --- Identifiers --- *)

identifier         = letter, { letter | digit | "_" } ;
letter             = "a" | "b" | ... | "z" | "A" | "B" | ... | "Z" ;
digit              = "0" | "1" | ... | "9" ;

(* --- Comments --- *)

comment            = single-line-comment | multi-line-comment ;
single-line-comment = "//", { comment-char }, newline ;
multi-line-comment = "/*", { comment-char | "*" }, "*/" ;
comment-char       = any-character-except-newline ;
```

### 3.2 Grammar Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Cedar-compatible subset** | All valid Cedar policies are valid GRC_Claw policies |
| **Extensibility** | GRC extensions (rules, scope, override) are additive |
| **Formal verifiability** | EBNF enables parser generation and formal analysis |
| **Human-readable** | Familiar syntax for policy authors |
| **Tool-friendly** | Unambiguous grammar for IDE support and linting |

### 3.3 Reserved Words

The following identifiers are reserved and cannot be used as entity types, field names, or variable names:

```
permit    forbid    when      unless    if        then
else      in        contains  matches   startsWith endsWith
true      false     all       scope     rule      effect
priority  approvers limit     metadata  override  target
strategy  context   principal action    resource
```

---

## 4. Policy Compilation Pipeline

### 4.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POLICY COMPILATION PIPELINE                               │
│                                                                             │
│  Cedar Source (.cedar)                                                      │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────┐                                                        │
│  │  Stage 1:       │  Lexer + Parser (Rust)                                 │
│  │  Cedar Parsing  │  → Cedar AST                                           │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 2:       │  Schema Validation                                     │
│  │  Validation     │  → Validated Cedar AST + Type Annotations              │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 3:       │  Cedar → IR Translation                                │
│  │  IR Generation  │  → GRC-IR (Intermediate Representation)                │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 4:       │  IR Optimization                                       │
│  │  Optimization   │  → Optimized IR (constant folding, dead code elim)    │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 5:       │  IR → Rego Translation                                │
│  │  Rego Codegen   │  → Rego AST + Rego Source                             │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 6:       │  Rego Compilation                                      │
│  │  Rego Compile   │  → Rego Bundle (JSON)                                  │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 7:       │  Rego → WASM (optional, for edge deployment)          │
│  │  WASM Compile   │  → WASM Module (.wasm)                                 │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 8:       │  Bundle Packaging                                      │
│  │  Packaging      │  → OPA Bundle (tar.gz) + Manifest                     │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  Deployed Policy Bundle                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Stage 1: Cedar Parsing

**Input:** Cedar source file (`.cedar`)  
**Output:** Cedar AST (Rust `cedar_policy::ast::Policy`)

```rust
// Rust implementation using cedar-policy crate
use cedar_policy::{PolicySet, Schema, Authorizer};

pub fn parse_cedar(source: &str) -> Result<CedarAst, ParseError> {
    let policy_set = PolicySet::from_str(source)?;
    let schema = Schema::from_str(&GRC_SCHEMA)?;
    
    // Validate against schema
    for policy in policy_set.policies() {
        policy.validate(&schema)?;
    }
    
    Ok(CedarAst::from(policy_set))
}
```

**Error Handling:**
- Syntax errors: line/column, expected tokens, suggestion
- Schema violations: unknown entity types, invalid attributes
- Semantic errors: conflicting permit/forbid on same scope

### 4.3 Stage 2: Schema Validation

**Input:** Cedar AST  
**Output:** Validated Cedar AST with type annotations

The GRC_Claw schema defines the entity types and their attributes:

```cedar
// GRC_Claw Entity Schema
entity Agent {
    id: String,
    name: String,
    clearance: Long,
    role: String,
    trust_score: Double,
    risk_tier: String,
    capabilities: Set<String>,
    owner: String,
    environment: String,
    session_id: String,
    delegation_chain: Set<String>,
};

entity Action {
    name: String,
    tool: String,
    resource: String,
    parameters: String,
    classification: String,
};

entity DataClass {
    id: String,
    classification: Long,
    containsPii: Boolean,
    owner: String,
    jurisdiction: String,
};

entity Context {
    time: DateTime,
    environment: String,
    approval_ticket: Option<ApprovalTicket>,
    request_origin: String,
    data_residency: String,
};

entity ApprovalTicket {
    id: String,
    status: String,
    approver: String,
    expires_at: DateTime,
};
```

### 4.4 Stage 3: Cedar → IR Translation

**Input:** Validated Cedar AST  
**Output:** GRC-IR (Intermediate Representation)

The IR is a language-agnostic representation that captures the semantics of both Cedar and Rego policies:

```rust
/// GRC Intermediate Representation
#[derive(Debug, Clone)]
pub enum IrNode {
    // Effect nodes
    Permit(IrPrincipal, IrAction, IrResource, Vec<IrCondition>),
    Forbid(IrPrincipal, IrAction, IrResource, Vec<IrCondition>),
    
    // Condition nodes
    And(Box<IrNode>, Box<IrNode>),
    Or(Box<IrNode>, Box<IrNode>),
    Not(Box<IrNode>),
    Comparison(IrValue, ComparisonOp, IrValue),
    Membership(IrValue, IrValue),
    Contains(IrValue, IrValue),
    
    // Value nodes
    Literal(IrLiteral),
    EntityRef { entity_type: String, entity_id: String },
    ContextRef { path: Vec<String> },
    FunctionCall { name: String, args: Vec<IrNode> },
    
    // GRC extensions
    Rule {
        name: String,
        condition: Box<IrNode>,
        effect: IrEffect,
        priority: i32,
        approvers: Vec<String>,
        rate_limit: Option<IrRateLimit>,
    },
    Scope {
        agents: ScopeFilter,
        resources: ScopeFilter,
        environments: Vec<String>,
        risk_tiers: Vec<String>,
        time_window: Option<IrTimeWindow>,
    },
}

#[derive(Debug, Clone)]
pub enum IrEffect {
    Allow,
    Deny,
    Warn,
    RequireApproval,
    Transform { rules: Vec<IrTransformRule> },
    Escalate { target: String },
    Throttle { limit: String },
    Log { level: String },
}

#[derive(Debug, Clone)]
pub enum IrLiteral {
    String(String),
    Long(i64),
    Double(f64),
    Bool(bool),
    Ip(String),
    DateTime(String),
    Duration(String),
    Set(Vec<IrLiteral>),
    Record(Vec<(String, IrLiteral)>),
}
```

### 4.5 Stage 4: IR Optimization

**Input:** GRC-IR  
**Output:** Optimized GRC-IR

Optimization passes:

| Pass | Description | Example |
|------|-------------|---------|
| **Constant Folding** | Evaluate constant sub-expressions at compile time | `6 <= 22` → `true` |
| **Dead Code Elimination** | Remove unreachable conditions | `if false then X else Y` → `Y` |
| **Condition Reordering** | Reorder AND/OR branches by selectivity | Most selective first |
| **Common Subexpression Elimination** | Deduplicate repeated expressions | `a && (b \|\| a)` → `a && b` |
| **Range Merging** | Merge overlapping range conditions | `x > 5 && x > 3` → `x > 5` |
| **Entity Resolution** | Resolve entity references to IDs | `Agent::"data-analyst"` → `agent-42` |

### 4.6 Stage 5: IR → Rego Translation

**Input:** Optimized GRC-IR  
**Output:** Rego AST + Rego source

Translation rules:

| Cedar Construct | Rego Equivalent |
|----------------|-----------------|
| `permit(p, a, r) when { c }` | `allow if { c }` (with input mapping) |
| `forbid(p, a, r) unless { c }` | `deny contains "reason" if { not c }` |
| `principal in Agent::"x"` | `input.principal.id == "x"` |
| `action == Action::"read"` | `input.action == "read"` |
| `resource in DataClass::"pii"` | `input.resource.classification == 4` |
| `context.time.hour >= 6` | `time.now_ns() >= ...` |
| `&&` | `;` (implicit AND in Rego) |
| `\|\|` | Multiple rules with same name |
| `!` | `not` |
| `a in b` | `b[_] == a` or `contains(b, a)` |

**Translation Example:**

```cedar
// Cedar Source
permit(
  principal in Agent::"data-analyst",
  action == Action::"read",
  resource in DataClass::"public"
) when {
  resource.classification <= principal.clearance &&
  context.time.hour >= 6 && context.time.hour <= 22
};
```

```rego
// Compiled Rego
package grc.agent.data_access

import future.keywords.if
import future.keywords.in

default allow := false

allow if {
    input.principal.id == "data-analyst"
    input.action == "read"
    input.resource.classification <= 2
    input.resource.classification <= input.principal.clearance
    time.now_ns() >= time.parse_rfc3339_ns("2026-10-01T06:00:00Z")
    time.now_ns() <= time.parse_rfc3339_ns("2026-10-01T22:00:00Z")
}
```

### 4.7 Stage 6: Rego Compilation

**Input:** Rego source  
**Output:** Rego bundle (JSON)

```bash
# OPA compile command
opa compile --bundle --output bundle.tar.gz \
  --optimization-level 2 \
  policies/
```

The bundle contains:
- `data.json` — compiled policy data
- `policy.rego` — human-readable Rego source
- `manifest.json` — bundle metadata (revision, roots)

### 4.8 Stage 7: WASM Compilation (Optional)

**Input:** Rego source  
**Output:** WASM module (`.wasm`)

```bash
# OPA WASM compilation
opa build --target wasm --output policy.wasm \
  --optimization-level 2 \
  policies/
```

The WASM module is loaded into a Wasmtime runtime for edge deployment:

```rust
use wasmtime::{Engine, Module, Store, Instance};

pub fn load_wasm_policy(wasm_bytes: &[u8]) -> Result<PolicyInstance, Error> {
    let engine = Engine::default();
    let module = Module::new(&engine, wasm_bytes)?;
    let mut store = Store::new(&engine, ());
    let instance = Instance::new(&mut store, &module, &[])?;
    
    Ok(PolicyInstance { store, instance })
}

impl PolicyInstance {
    pub fn evaluate(&mut self, input: &serde_json::Value) -> Result<Decision, Error> {
        let eval = self.instance.get_typed_func::<(i32, i32), i32>(
            &mut self.store, "eval"
        )?;
        // ... marshal input, call eval, unmarshal output
    }
}
```

### 4.9 Stage 8: Bundle Packaging

**Input:** Compiled Rego bundle + WASM module  
**Output:** Deployable OPA bundle

```
bundle.tar.gz
├── data.json              # Compiled policy data
├── policy.rego            # Human-readable Rego source
├── policy.wasm            # WASM module (optional)
├── manifest.json          # Bundle metadata
│   {
│     "revision": "20261001.143000",
│     "roots": ["grc/agent"],
│     "wasm": {
│       "module": "policy.wasm",
│       "sha256": "abc123..."
│     }
│   }
└── signature.json         # Bundle signature (ECDSA P-256)
    {
      "algorithm": "ECDSA-P256",
      "public_key": "-----BEGIN PUBLIC KEY-----\n...",
      "signature": "base64-encoded-signature",
      "timestamp": "2026-10-01T14:30:00Z"
    }
```

### 4.10 Compilation Pipeline API

```python
class PolicyCompiler:
    """Compiles Cedar policies through the full pipeline."""
    
    def compile(
        self,
        cedar_source: str,
        options: CompileOptions = None
    ) -> CompilationResult:
        """
        Compile a Cedar policy through the full pipeline.
        
        Args:
            cedar_source: Cedar policy source code
            options: Compilation options (optimization level, target, etc.)
            
        Returns:
            CompilationResult with all intermediate and final artifacts
        """
        # Stage 1: Parse Cedar
        cedar_ast = self._parse_cedar(cedar_source)
        
        # Stage 2: Validate schema
        validated_ast = self._validate_schema(cedar_ast)
        
        # Stage 3: Translate to IR
        ir = self._cedar_to_ir(validated_ast)
        
        # Stage 4: Optimize IR
        optimized_ir = self._optimize_ir(ir, options.optimization_level)
        
        # Stage 5: Translate to Rego
        rego_source = self._ir_to_rego(optimized_ir)
        
        # Stage 6: Compile Rego
        rego_bundle = self._compile_rego(rego_source)
        
        # Stage 7: Compile WASM (optional)
        wasm_module = None
        if options.target == "wasm":
            wasm_module = self._compile_wasm(rego_source)
        
        # Stage 8: Package bundle
        bundle = self._package_bundle(rego_bundle, wasm_module)
        
        return CompilationResult(
            cedar_ast=cedar_ast,
            ir=optimized_ir,
            rego_source=rego_source,
            rego_bundle=rego_bundle,
            wasm_module=wasm_module,
            bundle=bundle,
            warnings=self._collect_warnings(),
            errors=self._collect_errors(),
        )
```

---

## 5. Policy Conflict Detection

### 5.1 Conflict Taxonomy

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFLICT TAXONOMY                             │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Level 1: Syntactic Conflicts                            │  │
│  │  • Duplicate policy IDs                                  │  │
│  │  • Duplicate rule names within a policy                  │  │
│  │  • Type mismatches in conditions                         │  │
│  │  • Unknown entity references                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Level 2: Semantic Conflicts                              │  │
│  │  • Direct contradiction (permit + forbid on same scope)   │  │
│  │  • Implicit contradiction (conditions cannot both be true)│  │
│  │  • Priority inversion (lower priority overrides higher)   │  │
│  │  • Scope overlap with contradictory effects               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Level 3: Temporal Conflicts                              │  │
│  │  • Effective date overlap with contradictory effects      │  │
│  │  • Policy version rollback creating conflicts             │  │
│  │  • Scheduled policy activation conflicts                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Level 4: Cross-Policy Conflicts                          │  │
│  │  • Inheritance chain contradictions                       │  │
│  │  • Multi-agent policy conflicts                           │  │
│  │  • Framework mapping conflicts                            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Conflict Detection Algorithm

The conflict detection engine uses a three-phase approach:

#### Phase 1: Syntactic Analysis (AST-based)

```python
class SyntacticConflictDetector:
    """Detects conflicts at the AST level."""
    
    def detect(self, policies: list[Policy]) -> list[Conflict]:
        conflicts = []
        
        # Check 1: Duplicate policy IDs
        conflicts.extend(self._check_duplicate_ids(policies))
        
        # Check 2: Duplicate rule names within policies
        conflicts.extend(self._check_duplicate_rules(policies))
        
        # Check 3: Type mismatches
        conflicts.extend(self._check_type_mismatches(policies))
        
        # Check 4: Unknown entity references
        conflicts.extend(self._check_unknown_entities(policies))
        
        return conflicts
    
    def _check_duplicate_ids(self, policies):
        seen = {}
        conflicts = []
        for policy in policies:
            key = (policy.id, policy.version)
            if key in seen:
                conflicts.append(Conflict(
                    type=ConflictType.DUPLICATE_ID,
                    severity=Severity.ERROR,
                    message=f"Duplicate policy ID: {policy.id} v{policy.version}",
                    policies=[seen[key], policy],
                ))
            else:
                seen[key] = policy
        return conflicts
```

#### Phase 2: Semantic Analysis (SAT/SMT-based)

```python
class SemanticConflictDetector:
    """Detects semantic conflicts using SMT solving."""
    
    def __init__(self):
        self.solver = z3.Solver()
    
    def detect(self, policies: list[Policy]) -> list[Conflict]:
        conflicts = []
        
        # Build constraint model for each policy pair
        for i, p1 in enumerate(policies):
            for p2 in policies[i+1:]:
                # Check if policies have overlapping scopes
                if not self._scopes_overlap(p1, p2):
                    continue
                
                # Check for direct contradiction
                conflict = self._check_direct_contradiction(p1, p2)
                if conflict:
                    conflicts.append(conflict)
                
                # Check for implicit contradiction
                conflict = self._check_implicit_contradiction(p1, p2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_direct_contradiction(self, p1, p2):
        """
        Check if p1 permits what p2 forbids (or vice versa)
        on the same scope.
        """
        # Extract conditions
        c1 = self._extract_permit_conditions(p1)
        c2 = self._extract_forbid_conditions(p2)
        
        # Check if conditions can both be true
        self.solver.push()
        self.solver.add(c1, c2)
        
        if self.solver.check() == z3.sat:
            model = self.solver.model()
            self.solver.pop()
            return Conflict(
                type=ConflictType.DIRECT_CONTRADICTION,
                severity=Severity.ERROR,
                message=f"Policy {p1.id} permits what {p2} forbids",
                policies=[p1, p2],
                witness=model,  # Concrete example of conflicting input
            )
        
        self.solver.pop()
        return None
    
    def _check_implicit_contradiction(self, p1, p2):
        """
        Check if two policies have conditions that cannot
        both be satisfied simultaneously.
        """
        # Convert conditions to SMT-LIB
        smt1 = self._to_smt(p1.condition)
        smt2 = self._to_smt(p2.condition)
        
        self.solver.push()
        self.solver.add(z3.Not(z3.And(smt1, smt2)))
        
        if self.solver.check() == z3.sat:
            # Conditions are mutually exclusive — not a conflict
            # but worth noting as a warning
            self.solver.pop()
            return Conflict(
                type=ConflictType.MUTUALLY_EXCLUSIVE,
                severity=Severity.WARNING,
                message=f"Policies {p1.id} and {p2.id} have mutually exclusive conditions",
                policies=[p1, p2],
            )
        
        self.solver.pop()
        return None
```

#### Phase 3: Temporal Analysis

```python
class TemporalConflictDetector:
    """Detects conflicts arising from effective date overlaps."""
    
    def detect(self, policies: list[Policy]) -> list[Conflict]:
        conflicts = []
        
        # Sort policies by effective date
        sorted_policies = sorted(policies, key=lambda p: p.effective_from)
        
        # Check for overlapping effective periods with contradictory effects
        for i, p1 in enumerate(sorted_policies):
            for p2 in sorted_policies[i+1:]:
                if not self._time_overlap(p1, p2):
                    continue
                
                if self._effects_contradict(p1, p2):
                    conflicts.append(Conflict(
                        type=ConflictType.TEMPORAL_OVERLAP,
                        severity=Severity.WARNING,
                        message=f"Policies {p1.id} and {p2.id} overlap in time with contradictory effects",
                        policies=[p1, p2],
                        overlap_window=self._compute_overlap(p1, p2),
                    ))
        
        return conflicts
```

### 5.3 Conflict Resolution Strategies

| Strategy | Description | When Applied |
|----------|-------------|--------------|
| **deny_overrides** | Any deny rule wins over any allow rule | Default for security policies |
| **allow_overrides** | Any allow rule wins over any deny rule | Default for operational policies |
| **first_match** | First matching rule in priority order wins | When explicit ordering is defined |
| **priority_order** | Highest priority rule wins | When rules have explicit priorities |
| **most_specific** | Most specific scope wins | When policies have overlapping scopes |
| **temporal_latest** | Most recently activated policy wins | When policies have overlapping time windows |

### 5.4 Conflict Detection API

```python
class ConflictDetectionEngine:
    """Main entry point for conflict detection."""
    
    def __init__(self):
        self.syntactic_detector = SyntacticConflictDetector()
        self.semantic_detector = SemanticConflictDetector()
        self.temporal_detector = TemporalConflictDetector()
    
    def analyze(
        self,
        policies: list[Policy],
        options: ConflictOptions = None
    ) -> ConflictReport:
        """
        Run full conflict detection analysis.
        
        Returns:
            ConflictReport with all detected conflicts and recommendations
        """
        # Phase 1: Syntactic analysis
        syntactic_conflicts = self.syntactic_detector.detect(policies)
        
        # Phase 2: Semantic analysis
        semantic_conflicts = self.semantic_detector.detect(policies)
        
        # Phase 3: Temporal analysis
        temporal_conflicts = self.temporal_detector.detect(policies)
        
        # Aggregate and deduplicate
        all_conflicts = self._deduplicate(
            syntactic_conflicts + semantic_conflicts + temporal_conflicts
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_conflicts)
        
        return ConflictReport(
            conflicts=all_conflicts,
            recommendations=recommendations,
            summary=ConflictSummary(
                total=len(all_conflicts),
                errors=len([c for c in all_conflicts if c.severity == Severity.ERROR]),
                warnings=len([c for c in all_conflicts if c.severity == Severity.WARNING]),
                info=len([c for c in all_conflicts if c.severity == Severity.INFO]),
            ),
        )
```

---

## 6. Policy Impact Analysis

### 6.1 Impact Analysis Overview

Impact analysis answers: **"What happens if I deploy this policy?"**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IMPACT ANALYSIS PIPELINE                                  │
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │  Input:         │  New/Modified Policy                                   │
│  │  • Policy diff  │  Current active policies                              │
│  │  • Agent list   │  Historical decision data                             │
│  │  • Action log   │                                                       │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 1:       │  Blast Radius Calculation                              │
│  │  Blast Radius   │  → Which agents are affected?                         │
│  │                 │  → Which resources are affected?                      │
│  │                 │  → Which actions are affected?                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 2:       │  Decision Simulation                                   │
│  │  Simulation     │  → Replay historical actions through new policy       │
│  │                 │  → Compare old vs. new decisions                      │
│  │                 │  → Identify decision flips                            │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 3:       │  Dependency Analysis                                  │
│  │  Dependencies   │  → Which policies depend on this one?                 │
│  │                 │  → Which policies does this one depend on?            │
│  │                 │  → Cascading impact assessment                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Stage 4:       │  Risk Assessment                                      │
│  │  Risk           │  → False positive rate estimation                     │
│  │                 │  → False negative rate estimation                     │
│  │                 │  → Compliance gap analysis                            │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │  Output:        │  Impact Report                                         │
│  │  • Affected agents count                                                │
│  │  • Decision distribution (allow/deny/approval)                          │
│  │  • Decision flips (old→new)                                             │
│  │  • Risk score                                                              │
│  │  • Recommendations                                                      │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Blast Radius Calculation

```python
class BlastRadiusCalculator:
    """Calculates the blast radius of a policy change."""
    
    def calculate(
        self,
        new_policy: Policy,
        active_policies: list[Policy],
        agents: list[Agent],
    ) -> BlastRadius:
        """
        Calculate which agents, resources, and actions are affected.
        """
        # Step 1: Determine policy scope
        scope = new_policy.scope
        
        # Step 2: Filter agents by scope
        affected_agents = [
            agent for agent in agents
            if self._agent_in_scope(agent, scope)
        ]
        
        # Step 3: Determine affected actions
        affected_actions = self._extract_actions(new_policy)
        
        # Step 4: Determine affected resources
        affected_resources = self._extract_resources(new_policy)
        
        # Step 5: Calculate overlap with existing policies
        overlapping_policies = [
            p for p in active_policies
            if self._policies_overlap(new_policy, p)
        ]
        
        # Step 6: Estimate decision distribution
        decision_distribution = self._estimate_decisions(
            new_policy, affected_agents, affected_actions
        )
        
        return BlastRadius(
            affected_agents=affected_agents,
            affected_agent_count=len(affected_agents),
            affected_actions=affected_actions,
            affected_resources=affected_resources,
            overlapping_policies=overlapping_policies,
            decision_distribution=decision_distribution,
            risk_score=self._calculate_risk_score(
                new_policy, affected_agents, decision_distribution
            ),
        )
    
    def _agent_in_scope(self, agent: Agent, scope: PolicyScope) -> bool:
        """Check if an agent falls within the policy scope."""
        if scope.agents != "all":
            if agent.id not in scope.agents:
                return False
        
        if scope.environments and agent.environment not in scope.environments:
            return False
        
        if scope.risk_tiers and agent.risk_tier not in scope.risk_tiers:
            return False
        
        return True
```

### 6.3 Decision Simulation Engine

```python
class DecisionSimulationEngine:
    """Simulates policy decisions against historical action data."""
    
    def simulate(
        self,
        new_policy: Policy,
        historical_actions: list[AgentAction],
        current_policies: list[Policy],
    ) -> SimulationResult:
        """
        Replay historical actions through the new policy and
        compare decisions with the current policy set.
        """
        results = []
        flips = []
        
        for action in historical_actions:
            # Evaluate with current policies
            old_decision = self._evaluate(action, current_policies)
            
            # Evaluate with new policy added
            new_decision = self._evaluate(
                action, current_policies + [new_policy]
            )
            
            result = SimulationResultItem(
                action=action,
                old_decision=old_decision,
                new_decision=new_decision,
                flipped=old_decision.verdict != new_decision.verdict,
            )
            results.append(result)
            
            if result.flipped:
                flips.append(result)
        
        # Compute statistics
        total = len(results)
        allowed = sum(1 for r in results if r.new_decision.verdict == "ALLOW")
        denied = sum(1 for r in results if r.new_decision.verdict == "DENY")
        require_approval = sum(1 for r in results if r.new_decision.verdict == "REQUIRE_APPROVAL")
        
        return SimulationResult(
            total_actions=total,
            decision_distribution=DecisionDistribution(
                allowed=allowed,
                denied=denied,
                require_approval=require_approval,
                other=total - allowed - denied - require_approval,
            ),
            flips=flips,
            flip_rate=len(flips) / total if total > 0 else 0,
            flip_breakdown=self._categorize_flips(flips),
        )
```

### 6.4 Dependency Graph Analysis

```python
class DependencyAnalyzer:
    """Analyzes policy dependencies using graph traversal."""
    
    def __init__(self, graph_db: Neo4jClient):
        self.graph = graph_db
    
    def analyze_impact(self, policy_id: str) -> DependencyImpact:
        """
        Analyze the cascading impact of changing a policy.
        """
        # Find all policies that depend on this policy
        dependents = self.graph.query("""
            MATCH (p:Policy {id: $policy_id})<-[:DEPENDS_ON]-(dependent:Policy)
            RETURN dependent
        """, policy_id=policy_id)
        
        # Find all policies this policy depends on
        dependencies = self.graph.query("""
            MATCH (p:Policy {id: $policy_id})-[:DEPENDS_ON]->(dep:Policy)
            RETURN dep
        """, policy_id=policy_id)
        
        # Find conflicting policies
        conflicts = self.graph.query("""
            MATCH (p:Policy {id: $policy_id})-[:CONFLICTS_WITH]->(conflict:Policy)
            RETURN conflict
        """, policy_id=policy_id)
        
        # Calculate transitive impact
        transitive_dependents = self._transitive_closure(policy_id, "DEPENDS_ON")
        
        return DependencyImpact(
            direct_dependents=dependents,
            transitive_dependents=transitive_dependents,
            dependencies=dependencies,
            conflicts=conflicts,
            blast_radius=len(transitive_dependents) + 1,
            risk_level=self._assess_risk(transitive_dependents, conflicts),
        )
```

### 6.5 Impact Analysis API

```python
class ImpactAnalysisEngine:
    """Main entry point for policy impact analysis."""
    
    def __init__(self):
        self.blast_radius_calc = BlastRadiusCalculator()
        self.simulation_engine = DecisionSimulationEngine()
        self.dependency_analyzer = DependencyAnalyzer()
    
    def analyze(
        self,
        policy: Policy,
        context: AnalysisContext,
    ) -> ImpactReport:
        """
        Run full impact analysis for a policy change.
        
        Args:
            policy: The new or modified policy
            context: Analysis context (active policies, agents, historical data)
            
        Returns:
            ImpactReport with complete analysis results
        """
        # Stage 1: Blast radius
        blast_radius = self.blast_radius_calc.calculate(
            policy, context.active_policies, context.agents
        )
        
        # Stage 2: Decision simulation
        simulation = self.simulation_engine.simulate(
            policy, context.historical_actions, context.active_policies
        )
        
        # Stage 3: Dependency analysis
        dependencies = self.dependency_analyzer.analyze_impact(policy.id)
        
        # Stage 4: Risk assessment
        risk = self._assess_risk(blast_radius, simulation, dependencies)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            blast_radius, simulation, dependencies, risk
        )
        
        return ImpactReport(
            policy_id=policy.id,
            blast_radius=blast_radius,
            simulation=simulation,
            dependencies=dependencies,
            risk_assessment=risk,
            recommendations=recommendations,
            timestamp=datetime.utcnow(),
        )
```

---

## 7. Policy Testing Framework

### 7.1 Testing Framework Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POLICY TESTING FRAMEWORK                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Unit Tests (pytest)                                        │   │
│  │  • Parser tests (valid/invalid syntax)                               │   │
│  │  • Compiler tests (Cedar→IR→Rego)                                    │   │
│  │  • Evaluator tests (decision correctness)                            │   │
│  │  • Conflict detector tests                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: Property-Based Tests (Hypothesis)                          │   │
│  │  • Decision monotonicity                                             │   │
│  │  • Conflict detection completeness                                   │   │
│  │  • Compilation roundtrip (Cedar→Rego→Cedar)                          │   │
│  │  • Scope narrowing invariance                                        │   │
│  │  • Priority ordering consistency                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Integration Tests                                          │   │
│  │  • OPA bundle deployment + evaluation                                │   │
│  │  • Cedar SDK evaluation                                              │   │
│  │  • WASM module evaluation                                            │   │
│  │  • PDP-PEP end-to-end                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 4: Performance Benchmarks                                     │   │
│  │  • Evaluation latency (p50, p99, p999)                               │   │
│  │  • Compilation time                                                  │   │
│  │  • Memory usage                                                      │   │
│  │  • Throughput (decisions/second)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 5: Fuzzing Tests                                              │   │
│  │  • Random policy generation                                          │   │
│  │  • Random input generation                                           │   │
│  │  • Differential testing (Cedar vs. Rego vs. WASM)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Unit Tests

```python
# tests/test_policy_compiler.py

import pytest
from grcclaw.policy import PolicyCompiler, CompileOptions

class TestPolicyCompiler:
    """Unit tests for the policy compilation pipeline."""
    
    @pytest.fixture
    def compiler(self):
        return PolicyCompiler()
    
    def test_simple_permit_policy(self, compiler):
        """Test compilation of a simple permit policy."""
        cedar_source = """
        permit(
            principal in Agent::"data-analyst",
            action == Action::"read",
            resource in DataClass::"
        );
        """
        
        result = compiler.compile(cedar_source)
        
        assert result.success
        assert result.rego_source is not None
        assert "allow" in result.rego_source
        assert "data-analyst" in result.rego_source
    
    def test_forbid_with_unless_clause(self, compiler):
        """Test compilation of forbid with unless clause."""
        cedar_source = """
        forbid(
            principal,
            action == Action::"read",
            resource in DataClass::"pii"
        ) unless {
            context.approval_ticket exists &&
            context.approval_ticket.status == "approved"
        };
        """
        
        result = compiler.compile(cedar_source)
        
        assert result.success
        assert "deny" in result.rego_source
        assert "approval_ticket" in result.rego_source
    
    def test_complex_condition(self, compiler):
        """Test compilation of complex boolean conditions."""
        cedar_source = """
        permit(
            principal,
            action == Action::"read",
            resource
        ) when {
            (resource.classification <= principal.clearance &&
             context.time.hour >= 6 && context.time.hour <= 22) ||
            (principal.role == "admin" &&
             context.environment == "production")
        };
        """
        
        result = compiler.compile(cedar_source)
        
        assert result.success
        # Verify both branches are present in Rego
        assert result.rego_source.count("allow") >= 2
    
    def test_invalid_syntax(self, compiler):
        """Test that invalid Cedar syntax is rejected."""
        cedar_source = """
        permit(
            principal in Agent::"data-analyst",
            action == Action::"read"
            // Missing resource expression
        ) when {
            resource.classification <= principal.clearance
        };
        """
        
        result = compiler.compile(cedar_source)
        
        assert not result.success
        assert len(result.errors) > 0
        assert "resource" in result.errors[0].message.lower()
    
    def test_unknown_entity_type(self, compiler):
        """Test that unknown entity types are rejected."""
        cedar_source = """
        permit(
            principal in UnknownEntity::"foo",
            action == Action::"read",
            resource
        );
        """
        
        result = compiler.compile(cedar_source)
        
        assert not result.success
        assert any("UnknownEntity" in e.message for e in result.errors)
    
    def test_wasm_compilation(self, compiler):
        """Test WASM compilation for edge deployment."""
        cedar_source = """
        permit(
            principal in Agent::"data-analyst",
            action == Action::"read",
            resource in DataClass::"public"
        ) when {
            resource.classification <= principal.clearance
        };
        """
        
        result = compiler.compile(cedar_source, CompileOptions(
            target="wasm",
            optimization_level=2,
        ))
        
        assert result.success
        assert result.wasm_module is not None
        assert len(result.wasm_module.bytes) > 0
```

### 7.3 Property-Based Tests

```python
# tests/test_policy_properties.py

from hypothesis import given, settings, strategies as st
from grcclaw.policy import PolicyCompiler, PolicyEvaluator

class TestPolicyProperties:
    """Property-based tests for policy engine invariants."""
    
    @given(
        clearance=st.integers(min_value=0, max_value=5),
        classification=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=1000)
    def test_clearance_monotonicity(self, clearance, classification):
        """
        Property: If clearance >= classification, read is allowed.
        If clearance < classification, read is denied.
        """
        cedar_source = f"""
        permit(
            principal in Agent::"test-agent",
            action == Action::"read",
            resource in DataClass::"test-data"
        ) when {{
            resource.classification <= principal.clearance
        }};
        """
        
        evaluator = PolicyEvaluator(cedar_source)
        
        result = evaluator.evaluate(
            principal={"id": "test-agent", "clearance": clearance},
            action="read",
            resource={"id": "test-data", "classification": classification},
            context={},
        )
        
        if clearance >= classification:
            assert result.verdict == "ALLOW"
        else:
            assert result.verdict == "DENY"
    
    @given(
        amount=st.floats(min_value=0, max_value=10000),
        has_approval=st.booleans(),
    )
    @settings(max_examples=500)
    def test_refund_approval_threshold(self, amount, has_approval):
        """
        Property: Refunds over $500 require approval.
        Refunds under $500 are allowed.
        """
        cedar_source = """
        permit(
            principal,
            action == Action::"refund",
            resource
        ) when {
            context.amount <= 500
        };
        
        forbid(
            principal,
            action == Action::"refund",
            resource
        ) when {
            context.amount > 500 &&
            !context.approval_ticket exists
        };
        """
        
        evaluator = PolicyEvaluator(cedar_source)
        
        context = {"amount": amount}
        if has_approval:
            context["approval_ticket"] = {"status": "approved"}
        
        result = evaluator.evaluate(
            principal={"id": "agent-1"},
            action="refund",
            resource={"id": "order-1"},
            context=context,
        )
        
        if amount <= 500:
            assert result.verdict == "ALLOW"
        elif has_approval:
            assert result.verdict == "ALLOW"
        else:
            assert result.verdict == "DENY"
    
    @given(
        policies=st.lists(
            st.sampled_from([
                'permit(principal, action == "read", resource);',
                'forbid(principal, action == "read", resource);',
                'permit(principal, action == "write", resource);',
                'forbid(principal, action == "write", resource);',
            ]),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=200)
    def test_conflict_detection_completeness(self, policies):
        """
        Property: If a permit and forbid exist for the same action,
        conflict detection must find it.
        """
        from grcclaw.policy import ConflictDetectionEngine
        
        policy_sources = [f"policy_{i}: {p}" for i, p in enumerate(policies)]
        
        detector = ConflictDetectionEngine()
        report = detector.analyze(policy_sources)
        
        has_permit_read = any("permit" in p and "read" in p for p in policies)
        has_forbid_read = any("forbid" in p and "read" in p for p in policies)
        
        if has_permit_read and has_forbid_read:
            assert len(report.conflicts) > 0
        else:
            assert len(report.conflicts) == 0
    
    @given(
        cedar_source=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
            min_size=10,
            max_size=500,
        ),
    )
    @settings(max_examples=100)
    def test_compilation_never_crashes(self, cedar_source):
        """
        Property: Compilation never crashes, regardless of input.
        Either succeeds with valid output or fails with errors.
        """
        compiler = PolicyCompiler()
        result = compiler.compile(cedar_source)
        
        # Must have a definite outcome
        assert result.success or len(result.errors) > 0
        
        # If successful, must have valid Rego output
        if result.success:
            assert result.rego_source is not None
            assert len(result.rego_source) > 0
    
    @given(
        priority_a=st.integers(min_value=0, max_value=1000),
        priority_b=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=500)
    def test_priority_ordering_consistency(self, priority_a, priority_b):
        """
        Property: Higher priority rules always win over lower priority rules.
        """
        cedar_source = f"""
        rule "rule-a" {{
            when {{ action == "read" }},
            effect = "deny",
            priority = {priority_a},
        }};
        
        rule "rule-b" {{
            when {{ action == "read" }},
            effect = "allow",
            priority = {priority_b},
        }};
        """
        
        evaluator = PolicyEvaluator(cedar_source)
        result = evaluator.evaluate(
            principal={"id": "agent-1"},
            action="read",
            resource={"id": "res-1"},
            context={},
        )
        
        if priority_a > priority_b:
            assert result.verdict == "DENY"
        elif priority_b > priority_a:
            assert result.verdict == "ALLOW"
        # Equal priority: deny_overrides default
        else:
            assert result.verdict == "DENY"
```

### 7.4 Integration Tests

```python
# tests/test_policy_integration.py

import pytest
import subprocess
import json
import tempfile
import os

class TestOPAIntegration:
    """Integration tests with OPA server."""
    
    @pytest.fixture
    def opa_server(self):
        """Start a temporary OPA server for testing."""
        # Create temporary policy file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.rego', delete=False
        ) as f:
            f.write("""
                package grc.test
                
                default allow := false
                
                allow if {
                    input.action == "read"
                    input.principal.clearance >= input.resource.classification
                }
            """)
            policy_file = f.name
        
        # Start OPA server
        proc = subprocess.Popen(
            ['opa', 'run', '--server', '--addr', ':8181', policy_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait for server to start
        import time
        time.sleep(2)
        
        yield proc
        
        # Cleanup
        proc.terminate()
        proc.wait()
        os.unlink(policy_file)
    
    def test_opa_evaluation(self, opa_server):
        """Test policy evaluation through OPA server."""
        import requests
        
        response = requests.post(
            'http://localhost:8181/v1/data/grc/test/allow',
            json={
                "input": {
                    "action": "read",
                    "principal": {"clearance": 3},
                    "resource": {"classification": 2},
                }
            },
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("result") is True
    
    def test_opa_denial(self, opa_server):
        """Test policy denial through OPA server."""
        import requests
        
        response = requests.post(
            'http://localhost:8181/v1/data/grc/test/allow',
            json={
                "input": {
                    "action": "read",
                    "principal": {"clearance": 1},
                    "resource": {"classification": 4},
                }
            },
        )
        
        assert response.status_code == 200
        result = response.json()
        # When deny, result is undefined (not present)
        assert "result" not in result or result["result"] is False


class TestCedarSDKIntegration:
    """Integration tests with Cedar Rust SDK via FFI."""
    
    def test_cedar_evaluation(self):
        """Test policy evaluation through Cedar SDK."""
        from grcclaw.policy.cedar import CedarEngine
        
        engine = CedarEngine()
        
        engine.load_policy("""
            permit(
                principal in Agent::"data-analyst",
                action == Action::"read",
                resource in DataClass::"public"
            ) when {
                resource.classification <= principal.clearance
            };
        """)
        
        result = engine.evaluate(
            principal="Agent::\"data-analyst\"",
            action="Action::\"read\"",
            resource="DataClass::\"public\"",
            context={"clearance": 3, "classification": 2},
        )
        
        assert result.is_allowed
    
    def test_cedar_denial(self):
        """Test policy denial through Cedar SDK."""
        from grcclaw.policy.cedar import CedarEngine
        
        engine = CedarEngine()
        
        engine.load_policy("""
            permit(
                principal in Agent::"data-analyst",
                action == Action::"read",
                resource in DataClass::"public"
            ) when {
                resource.classification <= principal.clearance
            };
        """)
        
        result = engine.evaluate(
            principal="Agent::\"data-analyst\"",
            action="Action::\"read\"",
            resource="DataClass::\"public\"",
            context={"clearance": 1, "classification": 4},
        )
        
        assert not result.is_allowed
```

### 7.5 Fuzzing Tests

```python
# tests/test_policy_fuzzing.py

from hypothesis import given, settings, strategies as st
import random

class TestPolicyFuzzing:
    """Fuzzing tests for robustness."""
    
    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z", "S"),
            ),
            min_size=1,
            max_size=1000,
        ),
    )
    @settings(max_examples=500, deadline=None)
    def test_parser_robustness(self, random_input):
        """
        Fuzz the parser with random input.
        Must never crash — only return errors.
        """
        compiler = PolicyCompiler()
        result = compiler.compile(random_input)
        
        # Must have a definite outcome
        assert result.success or result.errors is not None
    
    @given(
        st.dictionaries(
            st.sampled_from(["principal", "action", "resource", "context"]),
            st.dictionaries(
                st.text(alphabet="abc123_", min_size=1, max_size=10),
                st.one_of(
                    st.integers(),
                    st.text(alphabet="abc123_", min_size=1, max_size=20),
                    st.booleans(),
                    st.lists(st.integers(), max_size=5),
                ),
                min_size=0,
                max_size=5,
            ),
            min_size=1,
            max_size=4,
        ),
    )
    @settings(max_examples=200, deadline=None)
    def test_evaluator_robustness(self, random_input):
        """
        Fuzz the evaluator with random input documents.
        Must never crash.
        """
        cedar_source = """
        permit(
            principal,
            action == Action::"read",
            resource
        ) when {
            resource.classification <= principal.clearance
        };
        """
        
        evaluator = PolicyEvaluator(cedar_source)
        
        try:
            result = evaluator.evaluate(
                principal=random_input.get("principal", {}),
                action=random_input.get("action", "read"),
                resource=random_input.get("resource", {}),
                context=random_input.get("context", {}),
            )
            # Must return a valid verdict
            assert result.verdict in [
                "ALLOW", "DENY", "REQUIRE_APPROVAL",
                "ALLOW_WITH_REDACTION", "QUARANTINE",
            ]
        except EvaluationError:
            # Evaluation errors are acceptable for malformed input
            pass
    
    @given(
        num_policies=st.integers(min_value=2, max_value=20),
        seed=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=50, deadline=None)
    def test_differential_testing(self, num_policies, seed):
        """
        Differential testing: Cedar, Rego, and WASM must
        produce identical decisions for the same input.
        """
        random.seed(seed)
        
        # Generate random policies
        policies = []
        for i in range(num_policies):
            clearance = random.randint(0, 5)
            classification = random.randint(0, 5)
            policies.append(f"""
                permit(
                    principal in Agent::"agent-{i}",
                    action == Action::"read",
                    resource in DataClass::"data-{i}"
                ) when {{
                    resource.classification <= {clearance}
                }};
            """)
        
        # Generate random test inputs
        test_inputs = []
        for _ in range(100):
            test_inputs.append({
                "principal_id": f"agent-{random.randint(0, num_policies-1)}",
                "clearance": random.randint(0, 5),
                "resource_id": f"data-{random.randint(0, num_policies-1)}",
                "classification": random.randint(0, 5),
            })
        
        # Evaluate through all three engines
        cedar_engine = PolicyEvaluator("\n".join(policies))
        rego_engine = RegoEvaluator("\n".join(policies))
        wasm_engine = WasmEvaluator("\n".join(policies))
        
        for inp in test_inputs:
            cedar_result = cedar_engine.evaluate(
                principal={"id": inp["principal_id"], "clearance": inp["clearance"]},
                action="read",
                resource={"id": inp["resource_id"], "classification": inp["classification"]},
                context={},
            )
            
            rego_result = rego_engine.evaluate(inp)
            wasm_result = wasm_engine.evaluate(inp)
            
            # All three must agree
            assert cedar_result.verdict == rego_result.verdict == wasm_result.verdict, \
                f"Mismatch for input {inp}: " \
                f"Cedar={cedar_result.verdict}, " \
                f"Rego={rego_result.verdict}, " \
                f"WASM={wasm_result.verdict}"
```

### 7.6 Performance Benchmarks

```python
# tests/test_policy_performance.py

import pytest
import time
import statistics

class TestPolicyPerformance:
    """Performance benchmarks for the policy engine."""
    
    @pytest.fixture
    def simple_policy(self):
        return """
        permit(
            principal in Agent::"data-analyst",
            action == Action::"read",
            resource in DataClass::"public"
        ) when {
            resource.classification <= principal.clearance
        };
        """
    
    @pytest.fixture
    def complex_policy(self):
        return """
        permit(
            principal,
            action == Action::"read",
            resource
        ) when {
            (resource.classification <= principal.clearance &&
             context.time.hour >= 6 && context.time.hour <= 22 &&
             principal.trust_score >= 0.5 &&
             principal.risk_tier in ["limited", "minimal"] &&
             !resource.containsPii) ||
            (principal.role == "admin" &&
             context.environment == "production" &&
             context.approval_ticket exists)
        };
        """
    
    def test_simple_evaluation_latency(self, simple_policy, benchmark):
        """Benchmark simple policy evaluation latency."""
        evaluator = PolicyEvaluator(simple_policy)
        
        result = benchmark(
            evaluator.evaluate,
            principal={"id": "data-analyst", "clearance": 3},
            action="read",
            resource={"id": "public-data", "classification": 2},
            context={"time": "2026-10-01T14:30:00Z"},
        )
        
        # p99 must be under 50ms
        assert benchmark.stats.stats.max < 0.050
    
    def test_complex_evaluation_latency(self, complex_policy, benchmark):
        """Benchmark complex policy evaluation latency."""
        evaluator = PolicyEvaluator(complex_policy)
        
        result = benchmark(
            evaluator.evaluate,
            principal={
                "id": "agent-1",
                "clearance": 3,
                "trust_score": 0.8,
                "risk_tier": "limited",
                "role": "analyst",
            },
            action="read",
            resource={"id": "data-1", "classification": 2, "containsPii": False},
            context={
                "time": "2026-10-01T14:30:00Z",
                "environment": "production",
            },
        )
        
        # p99 must be under 100ms
        assert benchmark.stats.stats.max < 0.100
    
    def test_compilation_time(self, benchmark):
        """Benchmark policy compilation time."""
        compiler = PolicyCompiler()
        
        cedar_source = """
        permit(
            principal in Agent::"data-analyst",
            action == Action::"read",
            resource in DataClass::"public"
        ) when {
            resource.classification <= principal.clearance &&
            context.time.hour >= 6 && context.time.hour <= 22
        };
        """
        
        result = benchmark(compiler.compile, cedar_source)
        
        # Compilation must complete in under 5 seconds
        assert benchmark.stats.stats.max < 5.0
    
    def test_throughput(self, simple_policy):
        """Benchmark decision throughput."""
        evaluator = PolicyEvaluator(simple_policy)
        
        iterations = 10000
        start = time.monotonic()
        
        for i in range(iterations):
            evaluator.evaluate(
                principal={"id": "data-analyst", "clearance": 3},
                action="read",
                resource={"id": "public-data", "classification": 2},
                context={"time": "2026-10-01T14:30:00Z"},
            )
        
        elapsed = time.monotonic() - start
        throughput = iterations / elapsed
        
        # Must handle at least 10,000 decisions/second
        assert throughput > 10000
```

---

## 8. Policy Performance Optimization

### 8.1 Optimization Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE OPTIMIZATION STRATEGIES                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy 1: Decision Caching                                       │   │
│  │  • Cache key: hash(principal, action, resource, context, policy_set)│   │
│  │  • TTL: 300s (configurable per policy)                              │   │
│  │  • Invalidation: on policy update, on agent trust score change      │   │
│  │  • Expected hit rate: 80-95% for repeated actions                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy 2: Policy Indexing                                        │   │
│  │  • Index policies by (principal_type, action, resource_type)        │   │
│  │  • Reduces evaluation from O(N) to O(K) where K << N               │   │
│  │  • Automatic index selection based on query patterns                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy 3: Lazy Evaluation                                        │   │
│  │  • Short-circuit evaluation: deny_overrides stops at first deny     │   │
│  │  • Condition reordering: most selective conditions first           │   │
│  │  • Skip irrelevant policies based on scope matching                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy 4: Pre-computation                                        │   │
│  │  • Pre-compute decisions for known action patterns                  │   │
│  │  • Materialized views for frequent queries                          │   │
│  │  • Background refresh on policy update                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy 5: Compilation Optimization                               │   │
│  │  • Constant folding at compile time                                 │   │
│  │  • Dead code elimination                                            │   │
│  │  • Condition reordering by selectivity                              │   │
│  │  • Common subexpression elimination                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy 6: Runtime Optimization                                   │   │
│  │  • WASM compilation for edge deployment (< 1ms)                     │   │
│  │  • Cedar Rust SDK for native evaluation (< 0.1ms)                   │   │
│  │  • Connection pooling for PDP-PEP communication                    │   │
│  │  • Batch evaluation for multiple decisions                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy 7: Memory Optimization                                    │   │
│  │  • Policy deduplication (shared subtrees)                          │   │
│  │  • Compact AST representation                                       │   │
│  │  • LRU cache for compiled policies                                  │   │
│  │  • Memory-mapped policy storage                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Decision Caching

```python
class DecisionCache:
    """Redis-backed decision cache with TTL and invalidation."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    def get(
        self,
        principal: dict,
        action: str,
        resource: dict,
        context: dict,
        policy_set_hash: str,
    ) -> Optional[Decision]:
        """Retrieve cached decision if available."""
        cache_key = self._compute_key(
            principal, action, resource, context, policy_set_hash
        )
        
        cached = self.redis.get(cache_key)
        if cached:
            return Decision.from_json(cached)
        return None
    
    def put(
        self,
        principal: dict,
        action: str,
        resource: dict,
        context: dict,
        policy_set_hash: str,
        decision: Decision,
        ttl: int = None,
    ) -> None:
        """Cache a decision with TTL."""
        cache_key = self._compute_key(
            principal, action, resource, context, policy_set_hash
        )
        
        self.redis.setex(
            cache_key,
            ttl or self.default_ttl,
            decision.to_json(),
        )
    
    def invalidate(self, policy_id: str) -> None:
        """Invalidate all cached decisions for a policy."""
        # Pattern-based invalidation
        pattern = f"decision:*:policy:{policy_id}:*"
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
    
    def _compute_key(self, principal, action, resource, context, policy_set_hash):
        """Compute deterministic cache key."""
        # Normalize and hash
        key_data = json.dumps({
            "p": principal,
            "a": action,
            "r": resource,
            "c": context,
            "ps": policy_set_hash,
        }, sort_keys=True, separators=(",", ":"))
        
        return f"decision:{hashlib.sha256(key_data.encode()).hexdigest()}"
```

### 8.3 Policy Indexing

```python
class PolicyIndex:
    """Inverted index for fast policy lookup."""
    
    def __init__(self):
        # Index: (principal_type, action, resource_type) → [policy_ids]
        self.triple_index: dict[tuple, set[str]] = {}
        
        # Index: principal_type → [policy_ids]
        self.principal_index: dict[str, set[str]] = {}
        
        # Index: action → [policy_ids]
        self.action_index: dict[str, set[str]] = {}
        
        # Index: resource_type → [policy_ids]
        self.resource_index: dict[str, set[str]] = {}
    
    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the index."""
        triples = self._extract_triples(policy)
        
        for triple in triples:
            self.triple_index.setdefault(triple, set()).add(policy.id)
        
        # Update secondary indexes
        for pt in self._extract_principal_types(policy):
            self.principal_index.setdefault(pt, set()).add(policy.id)
        
        for action in self._extract_actions(policy):
            self.action_index.setdefault(action, set()).add(policy.id)
        
        for rt in self._extract_resource_types(policy):
            self.resource_index.setdefault(rt, set()).add(policy.id)
    
    def lookup(
        self,
        principal_type: str,
        action: str,
        resource_type: str,
    ) -> set[str]:
        """Find policies matching the given triple."""
        # Start with the most specific index
        triple_key = (principal_type, action, resource_type)
        if triple_key in self.triple_index:
            return self.triple_index[triple_key]
        
        # Fall back to secondary indexes and intersect
        candidates = None
        
        if principal_type in self.principal_index:
            candidates = self.principal_index[principal_type].copy()
        
        if action in self.action_index:
            action_matches = self.action_index[action]
            if candidates is not None:
                candidates &= action_matches
            else:
                candidates = action_matches.copy()
        
        if resource_type in self.resource_index:
            resource_matches = self.resource_index[resource_type]
            if candidates is not None:
                candidates &= resource_matches
            else:
                candidates = resource_matches.copy()
        
        return candidates or set()
```

### 8.4 Lazy Evaluation

```python
class LazyEvaluator:
    """Implements short-circuit and lazy evaluation optimizations."""
    
    def evaluate(
        self,
        action: AgentAction,
        policies: list[Policy],
        context: dict,
    ) -> Decision:
        """
        Evaluate policies with lazy evaluation optimizations.
        
        Optimizations:
        1. Sort policies by priority (highest first)
        2. For deny_overrides: stop at first deny
        3. For each policy: evaluate conditions lazily (short-circuit)
        4. Skip policies whose scope doesn't match
        """
        # Sort by priority (descending)
        sorted_policies = sorted(
            policies, key=lambda p: p.priority, reverse=True
        )
        
        decisions = []
        
        for policy in sorted_policies:
            # Scope check — skip if not applicable
            if not self._scope_matches(policy, action, context):
                continue
            
            # Lazy condition evaluation
            condition_result = self._evaluate_conditions_lazy(
                policy.conditions, action, context
            )
            
            if condition_result:
                decision = Decision(
                    verdict=policy.effect,
                    policy_id=policy.id,
                    matched=True,
                )
                decisions.append(decision)
                
                # Short-circuit: deny_overrides stops at first deny
                if policy.effect == "deny" and self._strategy == "deny_overrides":
                    return decision
        
        # Aggregate decisions
        return self._aggregate(decisions)
    
    def _evaluate_conditions_lazy(
        self,
        conditions: list[Condition],
        action: AgentAction,
        context: dict,
    ) -> bool:
        """
        Evaluate conditions with short-circuiting.
        
        Order conditions by selectivity (most selective first)
        to minimize evaluation cost.
        """
        # Sort by selectivity (estimated)
        sorted_conditions = sorted(
            conditions, key=lambda c: self._estimate_selectivity(c)
        )
        
        for condition in sorted_conditions:
            if not self._evaluate_condition(condition, action, context):
                return False  # Short-circuit on first false
        
        return True
```

### 8.5 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cedar evaluation (p99) | < 0.1 ms | Rust SDK |
| Rego evaluation (p99) | < 10 ms | OPA server |
| WASM evaluation (p99) | < 1 ms | Wasmtime |
| Cached decision (p99) | < 0.5 ms | Redis lookup |
| Policy compilation | < 5 s | Cedar → Rego → WASM |
| Conflict detection (100 policies) | < 2 s | Full analysis |
| Impact analysis (1000 agents) | < 10 s | Full simulation |
| Throughput | > 10,000 decisions/sec | Aggregate |
| Cache hit rate | > 80% | Production target |

---

## 9. Data Models

### 9.1 Policy Engine ER Diagram

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│     Policy       │     │   PolicyRule     │     │  PolicyVersion   │
│                  │     │                  │     │                  │
│ id (PK)          │◄────│ policy_id (FK)   │     │ policy_id (FK)   │
│ policy_key       │     │ id (PK)          │     │ version          │
│ name             │     │ name             │     │ status           │
│ description      │     │ condition        │     │ change_summary   │
│ category         │     │ effect           │     │ created_at       │
│ status           │     │ priority         │     │ created_by       │
│ version          │     │ approvers        │     └──────────────────┘
│ cedar_source     │     │ rate_limit       │
│ rego_source      │     │ metadata         │     ┌──────────────────┐
│ wasm_module      │     └──────────────────┘     │  PolicyDependency│
│ scope            │                              │                  │
│ framework_tags   │     ┌──────────────────┐     │ source_id (FK)   │
│ effective_from   │     │  ConflictRecord  │     │ target_id (FK)   │
│ effective_until  │     │                  │     │ relation_type    │
│ owner_id         │     │ id (PK)          │     │ description      │
│ metadata         │     │ policy_a (FK)    │     └──────────────────┘
│ created_at       │     │ policy_b (FK)    │
│ updated_at       │     │ conflict_type    │     ┌──────────────────┐
│ created_by       │     │ severity         │     │  ImpactReport    │
│ updated_by       │     │ description      │     │                  │
└──────────────────┘     │ witness          │     │ id (PK)          │
                         │ resolution       │     │ policy_id (FK)   │
                         │ detected_at      │     │ blast_radius     │
                         └──────────────────┘     │ simulation_result│
                                                  │ risk_score       │
┌──────────────────┐     ┌──────────────────┐     │ recommendations   │
│  Compilation     │     │  TestSuite       │     │ created_at       │
│  Artifact        │     │                  │     └──────────────────┘
│                  │     │ id (PK)          │
│ id (PK)          │     │ policy_id (FK)   │
│ policy_id (FK)   │     │ name             │
│ stage            │     │ type             │
│ input_hash       │     │ status           │
│ output           │     │ passed           │
│ duration_ms      │     │ failed           │
│ warnings         │     │ skipped          │
│ errors           │     │ duration_ms      │
│ created_at       │     │ executed_at      │
└──────────────────┘     └──────────────────┘
```

### 9.2 Database Schema

```sql
-- Policy Engine Tables

CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    version VARCHAR(50) NOT NULL,
    cedar_source TEXT,
    rego_source TEXT,
    wasm_module BYTEA,
    scope JSONB DEFAULT '{}',
    framework_tags JSONB DEFAULT '[]',
    effective_from TIMESTAMPTZ,
    effective_until TIMESTAMPTZ,
    owner_id VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

CREATE TABLE policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    condition JSONB NOT NULL,
    effect VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 0,
    approvers JSONB DEFAULT '[]',
    rate_limit VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE policy_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    change_summary TEXT,
    cedar_source TEXT,
    rego_source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    UNIQUE(policy_id, version)
);

CREATE TABLE policy_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    target_policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_policy_id, target_policy_id, relation_type)
);

CREATE TABLE conflict_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_a_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    policy_b_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    conflict_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    witness JSONB,
    resolution TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(255)
);

CREATE TABLE compilation_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    stage VARCHAR(100) NOT NULL,
    input_hash VARCHAR(256) NOT NULL,
    output JSONB NOT NULL,
    duration_ms INTEGER,
    warnings JSONB DEFAULT '[]',
    errors JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE impact_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    blast_radius JSONB NOT NULL,
    simulation_result JSONB NOT NULL,
    risk_score DECIMAL(5,4),
    recommendations JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE test_suites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    suite_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    tests_passed INTEGER DEFAULT 0,
    tests_failed INTEGER DEFAULT 0,
    tests_skipped INTEGER DEFAULT 0,
    duration_ms INTEGER,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_category ON policies(category);
CREATE INDEX idx_policies_framework_tags ON policies USING GIN(framework_tags);
CREATE INDEX idx_policies_scope ON policies USING GIN(scope);
CREATE INDEX idx_policy_rules_policy ON policy_rules(policy_id);
CREATE INDEX idx_policy_versions_policy ON policy_versions(policy_id);
CREATE INDEX idx_conflict_records_policies ON conflict_records(policy_a_id, policy_b_id);
CREATE INDEX idx_impact_reports_policy ON impact_reports(policy_id);
```

---

## 10. API Contracts

### 10.1 Policy Compilation API

```
POST /v1.0/policies/{policy_id}/compile
```

**Request:**
```json
{
  "options": {
    "optimization_level": 2,
    "target": "rego",
    "include_wasm": false,
    "validate_only": false
  }
}
```

**Response:**
```json
{
  "policy_id": "pol-001",
  "compilation_status": "success",
  "stages": [
    {
      "stage": "parse",
      "status": "success",
      "duration_ms": 12,
      "warnings": []
    },
    {
      "stage": "validate",
      "status": "success",
      "duration_ms": 8,
      "warnings": []
    },
    {
      "stage": "ir_generate",
      "status": "success",
      "duration_ms": 15,
      "warnings": []
    },
    {
      "stage": "ir_optimize",
      "status": "success",
      "duration_ms": 5,
      "warnings": ["Constant folded: 6 <= 22 → true"]
    },
    {
      "stage": "rego_codegen",
      "status": "success",
      "duration_ms": 10,
      "warnings": []
    },
    {
      "stage": "rego_compile",
      "status": "success",
      "duration_ms": 120,
      "warnings": []
    }
  ],
  "rego_source": "package grc.agent.data_access\n\nimport future.keywords.if\n...",
  "rego_bundle_url": "https://api.grc-claw.io/v1.0/bundles/pol-001/bundle.tar.gz",
  "wasm_module_url": null,
  "total_duration_ms": 170,
  "warnings": ["Constant folded: 6 <= 22 → true"],
  "errors": [],
  "compiled_at": "2026-10-01T14:30:00Z"
}
```

### 10.2 Conflict Detection API

```
POST /v1.0/policies/conflict-check
```

**Request:**
```json
{
  "policy_ids": ["pol-001", "pol-002", "pol-003"],
  "options": {
    "include_syntactic": true,
    "include_semantic": true,
    "include_temporal": true,
    "generate_witness": true
  }
}
```

**Response:**
```json
{
  "analysis_id": "conflict-001",
  "status": "completed",
  "summary": {
    "total_conflicts": 3,
    "errors": 1,
    "warnings": 2,
    "info": 0
  },
  "conflicts": [
    {
      "conflict_id": "c-001",
      "type": "DIRECT_CONTRADICTION",
      "severity": "ERROR",
      "policies": ["pol-001", "pol-002"],
      "description": "Policy pol-001 permits what pol-002 forbids on overlapping scope",
      "witness": {
        "principal": {"id": "agent-42", "clearance": 3},
        "action": "read",
        "resource": {"id": "dataset-001", "classification": 2},
        "context": {"time": "2026-10-01T14:30:00Z"}
      },
      "recommendation": "Add priority to resolve: set pol-001 priority > pol-002 priority"
    },
    {
      "conflict_id": "c-002",
      "type": "TEMPORAL_OVERLAP",
      "severity": "WARNING",
      "policies": ["pol-001", "pol-003"],
      "description": "Policies overlap in effective period with contradictory effects",
      "overlap_window": {
        "start": "2026-10-01T00:00:00Z",
        "end": "2026-12-31T23:59:59Z"
      },
      "recommendation": "Adjust effective dates to avoid overlap"
    }
  ],
  "analyzed_at": "2026-10-01T14:30:00Z"
}
```

### 10.3 Impact Analysis API

```
POST /v1.0/policies/{policy_id}/impact-analysis
```

**Request:**
```json
{
  "options": {
    "include_blast_radius": true,
    "include_simulation": true,
    "include_dependencies": true,
    "historical_window_days": 30,
    "simulation_sample_size": 10000
  }
}
```

**Response:**
```json
{
  "policy_id": "pol-001",
  "analysis_status": "completed",
  "blast_radius": {
    "affected_agents": ["agent-42", "agent-43", "agent-44"],
    "affected_agent_count": 3,
    "affected_actions": ["read"],
    "affected_resources": ["s3://data/public/*"],
    "overlapping_policies": ["pol-000", "pol-002"],
    "risk_score": 0.35
  },
  "simulation": {
    "total_actions_analyzed": 50000,
    "decision_distribution": {
      "allowed": 42000,
      "denied": 6500,
      "require_approval": 1500
    },
    "flips": {
      "total": 1200,
      "rate": 0.024,
      "breakdown": {
        "allow_to_deny": 800,
        "deny_to_allow": 300,
        "allow_to_require_approval": 100
      }
    }
  },
  "dependencies": {
    "direct_dependents": ["pol-003"],
    "transitive_dependents": ["pol-003", "pol-004", "pol-005"],
    "dependencies": ["pol-000"],
    "conflicts": ["pol-002"],
    "blast_radius": 4
  },
  "risk_assessment": {
    "overall_risk": "low",
    "false_positive_rate": 0.015,
    "false_negative_rate": 0.002,
    "compliance_gaps": []
  },
  "recommendations": [
    {
      "type": "canary_deploy",
      "description": "Deploy to 10% of agents first to validate impact",
      "priority": "high"
    },
    {
      "type": "monitor",
      "description": "Monitor decision flip rate for 48 hours",
      "priority": "medium"
    }
  ],
  "analyzed_at": "2026-10-01T14:30:00Z"
}
```

### 10.4 Testing API

```
POST /v1.0/policies/{policy_id}/test
```

**Request:**
```json
{
  "test_types": ["unit", "property", "integration", "fuzz"],
  "options": {
    "property_examples": 1000,
    "fuzz_iterations": 500,
    "differential": true,
    "benchmark": true
  }
}
```

**Response:**
```json
{
  "policy_id": "pol-001",
  "test_run_id": "test-001",
  "status": "completed",
  "summary": {
    "total_tests": 1523,
    "passed": 1500,
    "failed": 2,
    "skipped": 21,
    "duration_ms": 45000
  },
  "results": {
    "unit": {
      "total": 50,
      "passed": 50,
      "failed": 0
    },
    "property": {
      "total": 1000,
      "passed": 998,
      "failed": 2,
      "failures": [
        {
          "property": "clearance_monotonicity",
          "input": {"clearance": 3, "classification": 5},
          "expected": "DENY",
          "actual": "ALLOW",
          "shrunk_input": {"clearance": 3, "classification": 5}
        }
      ]
    },
    "integration": {
      "total": 500,
      "passed": 500,
      "failed": 0
    },
    "fuzz": {
      "total": 23,
      "passed": 23,
      "failed": 0
    },
    "differential": {
      "total": 500,
      "passed": 500,
      "failed": 0,
      "engines_compared": ["cedar", "rego", "wasm"]
    }
  },
  "benchmarks": {
    "evaluation_latency_p50_ms": 0.05,
    "evaluation_latency_p99_ms": 0.12,
    "compilation_time_ms": 170,
    "throughput_decisions_per_sec": 15000
  },
  "executed_at": "2026-10-01T14:30:00Z"
}
```

---

## 11. Appendices

### Appendix A: Cedar to Rego Translation Reference

| Cedar Syntax | Rego Equivalent | Notes |
|-------------|-----------------|-------|
| `permit(p, a, r)` | `allow if { ... }` | Top-level rule |
| `forbid(p, a, r)` | `deny contains "reason" if { ... }` | Partial set rule |
| `when { c }` | `if { c }` | Condition block |
| `unless { c }` | `if { not c }` | Negated condition |
| `principal in Agent::"x"` | `input.principal.id == "x"` | Entity membership |
| `action == Action::"read"` | `input.action == "read"` | Action equality |
| `resource in DataClass::"pii"` | `input.resource.classification == 4` | Resource classification |
| `context.time.hour >= 6` | `time.now_ns() >= ...` | Time-based condition |
| `&&` | `;` (implicit AND) | Boolean AND |
| `\|\|` | Multiple rules | Boolean OR |
| `!` | `not` | Boolean NOT |
| `a in b` | `b[_] == a` | Set membership |
| `a.contains(b)` | `contains(a, b)` | String containment |
| `a.startsWith(b)` | `startswith(a, b)` | String prefix |
| `a.matches(b)` | `regex.match(b, a)` | Regex matching |

### Appendix B: Conflict Detection SMT-LIB Translation

```smtlib
; Example: Translating policy conditions to SMT-LIB for Z3

; Policy 1: permit read when clearance >= classification
(declare-const clearance Int)
(declare-const classification Int)
(assert (>= clearance classification))

; Policy 2: forbid read when classification > 3
(declare-const classification Int)
(assert (> classification 3))

; Check: can both conditions be true simultaneously?
(push)
(assert (and (>= clearance classification) (> classification 3)))
(check-sat)
; Result: sat — policies can conflict
; Witness: clearance=4, classification=4
(pop)
```

### Appendix C: Property-Based Test Strategies

```python
# Hypothesis strategies for policy testing

from hypothesis import strategies as st

# Strategy: Valid Cedar expressions
cedar_condition = st.recursive(
    st.booleans() | st.integers() | st.text(),
    lambda children: st.one_of(
        st.tuples(st.sampled_from(["&&", "||"]), children, children),
        st.tuples(st.sampled_from(["==", "!=", "<", "<=", ">", ">="]), 
                  children, children),
        st.tuples(st.sampled_from(["in", "contains"]), children, children),
    ),
    max_leaves=10,
)

# Strategy: Valid policy documents
policy_document = st.fixed_dictionaries({
    "principal": st.text(alphabet="abc123_", min_size=1, max_size=20),
    "action": st.sampled_from(["read", "write", "execute", "delete"]),
    "resource": st.text(alphabet="abc123_", min_size=1, max_size=20),
    "conditions": st.lists(cedar_condition, min_size=0, max_size=5),
    "effect": st.sampled_from(["allow", "deny", "require_approval"]),
})

# Strategy: Agent actions
agent_action = st.fixed_dictionaries({
    "principal": st.fixed_dictionaries({
        "id": st.text(alphabet="abc123_", min_size=1, max_size=20),
        "clearance": st.integers(min_value=0, max_value=5),
        "trust_score": st.floats(min_value=0.0, max_value=1.0),
        "risk_tier": st.sampled_from(["prohibited", "high", "limited", "minimal"]),
    }),
    "action": st.sampled_from(["read", "write", "execute", "delete"]),
    "resource": st.fixed_dictionaries({
        "id": st.text(alphabet="abc123_", min_size=1, max_size=20),
        "classification": st.integers(min_value=0, max_value=5),
        "containsPii": st.booleans(),
    }),
    "context": st.fixed_dictionaries({
        "time": st.datetimes(),
        "environment": st.sampled_from(["production", "staging", "development"]),
    }),
})
```

### Appendix D: Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial specification |

---

*End of Policy Engine Specification*
