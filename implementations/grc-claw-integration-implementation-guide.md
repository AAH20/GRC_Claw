# GRC_Claw Integration Implementation Guide

**Document ID:** GRC-IMPL-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**References:** GRC-INT-001 v2.0, GRC-API-001 v1.2  

---

## Table of Contents

1. [Event-Driven Architecture (Kafka)](#1-event-driven-architecture-kafka)
2. [Streaming Processing (Flink)](#2-streaming-processing-flink)
3. [CQRS Implementation](#3-cqrs-implementation)
4. [Saga Pattern](#4-saga-pattern)
5. [API Composition](#5-api-composition)
6. [Enterprise Connectors](#6-enterprise-connectors)
7. [Integration Testing](#7-integration-testing)

---

## 1. Event-Driven Architecture (Kafka)

### 1.1 Architecture Overview

GRC_Claw uses Apache Kafka as the primary event backbone for asynchronous, loosely-coupled communication between governance components. The architecture separates producers, the Kafka cluster, and consumers into distinct layers with a Schema Registry for contract enforcement.

```
Producer Layer → Event Gateway → Kafka Cluster → Consumer Layer
                  (Schema Registry,    (8 topics,      (SIEM, DWH, Compliance,
                   Validation,          RF=3)            Audit, Flink, Risk,
                   Enrichment)                           Alert, Ticketing, Cache)
```

### 1.2 Topic Design & Partitioning

| Topic | Partitions | Replication | Retention | Key | Partitioner |
|-------|-----------|-------------|-----------|-----|-------------|
| `grcclaw.enforcement` | 12 | 3 | 7 days | `agent_id` | `agent_id` hash |
| `grcclaw.evidence` | 12 | 3 | 30 days | `evidence_id` | `evidence_id` hash |
| `grcclaw.audit` | 6 | 3 | 1 year | `event_id` | `event_id` hash |
| `grcclaw.compliance` | 6 | 3 | 30 days | `framework_id` | `framework_id` hash |
| `grcclaw.risk` | 6 | 3 | 7 days | `risk_id` | `risk_id` hash |
| `grcclaw.agent` | 6 | 3 | 30 days | `agent_id` | `agent_id` hash |
| `grcclaw.policy` | 6 | 3 | 30 days | `policy_id` | `policy_id` hash |
| `grcclaw.assessment` | 6 | 3 | 30 days | `assessment_id` | `assessment_id` hash |
| `grcclaw.dlq` | 3 | 3 | 30 days | `original_key` | `original_key` hash |

**Partitioning rationale:**
- **Enforcement/Evidence**: High-throughput (10K–100K events/sec) → 12 partitions for parallel consumption
- **Audit**: Lower throughput but 1-year retention → 6 partitions balance parallelism with resources
- **Compliance/Risk/Agent/Policy/Assessment**: Moderate throughput → 6 partitions sufficient
- **DLQ**: Low volume → 3 partitions minimize overhead

### 1.3 Event Schema (CloudEvents + GRC_Claw Extensions)

All events conform to CloudEvents 1.0 with GRC_Claw-specific extensions:

```json
{
  "specversion": "1.0",
  "id": "uuid-v4",
  "source": "grc-claw/enforcement-engine",
  "type": "com.grcclaw.enforcement.decision",
  "subject": "agent-123",
  "time": "2026-10-01T12:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "decision_id": "uuid",
    "agent_id": "uuid",
    "policy_id": "uuid",
    "decision": "DENY",
    "reason": "Policy violation: data_handling",
    "confidence_score": 0.95,
    "evidence_ids": ["uuid-1", "uuid-2"]
  },
  "grcclaw": {
    "tenant_id": "org-123",
    "environment": "prod",
    "trace_id": "uuid",
    "span_id": "uuid",
    "compliance_frameworks": ["ISO-42001", "SOC2"],
    "risk_tier": "high",
    "event_version": "1.0",
    "schema_version": "1.0",
    "correlation_id": "uuid",
    "causation_id": "uuid"
  }
}
```

**GRC_Claw Extension Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | string | Yes | Multi-tenant isolation key |
| `environment` | enum | Yes | `prod`, `staging`, `dev` |
| `trace_id` | UUID | Yes | OpenTelemetry trace correlation |
| `span_id` | UUID | Yes | OpenTelemetry span correlation |
| `compliance_frameworks` | string[] | No | Related compliance frameworks |
| `risk_tier` | enum | No | `prohibited`, `high`, `limited`, `minimal` |
| `event_version` | string | Yes | Schema version for forward compatibility |
| `schema_version` | string | Yes | Data schema version |
| `correlation_id` | UUID | No | Groups related events across services |
| `causation_id` | UUID | No | Identifies the event that caused this event |

### 1.4 Event Types Catalog

| Event Type | Source | Consumers | Payload |
|------------|--------|-----------|---------|
| `com.grcclaw.enforcement.decision` | Enforcement Engine | SIEM, Ticketing, Notification | Enforcement decision |
| `com.grcclaw.evidence.collected` | Evidence Orchestrator | SIEM, Data Warehouse, Analytics | Evidence metadata |
| `com.grcclaw.evidence.verified` | Evidence Orchestrator | SIEM, Compliance | Verification result |
| `com.grcclaw.assessment.completed` | Assessment Engine | GRC, Reporting, Ticketing | Assessment results |
| `com.grcclaw.compliance.computed` | Compliance Engine | Reporting, Dashboard, SIEM | Compliance posture |
| `com.grcclaw.risk.detected` | Risk Engine | SIEM, Ticketing, Notification | Risk signal |
| `com.grcclaw.agent.registered` | Agent Registry | IAM, SIEM, Inventory | Agent metadata |
| `com.grcclaw.agent.terminated` | Agent Registry | IAM, SIEM, Inventory | Termination record |
| `com.grcclaw.policy.activated` | Policy Engine | Enforcement, Cache, Notification | Policy details |
| `com.grcclaw.policy.violated` | Enforcement Engine | SIEM, Ticketing, Notification | Violation details |
| `com.grcclaw.audit.event` | Audit Trail | SIEM, Blockchain, Archive | Audit event |
| `com.grcclaw.exception.created` | Exception Manager | GRC, Notification, Approval | Exception details |
| `com.grcclaw.finding.created` | Assessment Engine | GRC, Ticketing, Remediation | Finding details |
| `com.grcclaw.vendor.risk_changed` | Vendor Manager | GRC, Procurement, Notification | Risk change |

### 1.5 Producer Configuration

```yaml
kafka_producer:
  bootstrap_servers: ["kafka-1:9092", "kafka-2:9092", "kafka-3:9092"]
  security_protocol: SASL_SSL
  sasl_mechanism: SCRAM-SHA-512
  sasl_username: ${KAFKA_USERNAME}
  sasl_password: ${KAFKA_PASSWORD}
  
  # Performance
  acks: all                    # Wait for all replicas
  retries: 3
  retry_backoff_ms: 100
  batch_size: 16384
  linger_ms: 5
  compression_type: lz4
  max_in_flight_requests_per_connection: 5
  
  # Idempotency
  enable_idempotence: true    # Exactly-once semantics per partition
  
  # Delivery guarantee
  delivery_timeout_ms: 120000
  request_timeout_ms: 30000
  
  # Schema Registry
  schema_registry_url: http://schema-registry:8081
  auto_register_schemas: false
  use_latest_version: true
  
  # Interceptors
  interceptors:
    - class: io.confluent.monitoring.clients.interceptor.MonitoringProducerInterceptor
    - class: io.opentelemetry.instrumentation.kafkaclients.v2_6.TracingProducerInterceptor
```

### 1.6 Consumer Configuration

```yaml
kafka_consumer:
  bootstrap_servers: ["kafka-1:9092", "kafka-2:9092", "kafka-3:9092"]
  security_protocol: SASL_SSL
  sasl_mechanism: SCRAM-SHA-512
  
  # Consumer group
  group_id: grcclaw-siem-consumer
  client_id: siem-connector-1
  
  # Offset management
  auto_offset_reset: earliest
  enable_auto_commit: false    # Manual commit for exactly-once
  auto_commit_interval_ms: 5000
  
  # Performance
  max_poll_records: 500
  max_poll_interval_ms: 300000
  session_timeout_ms: 45000
  heartbeat_interval_ms: 15000
  
  # Partition assignment
  partition_assignment_strategy: org.apache.kafka.clients.consumer.CooperativeStickyAssignor
  
  # Deserialization
  key_deserializer: org.apache.kafka.common.serialization.StringDeserializer
  value_deserializer: io.confluent.kafka.serializers.KafkaAvroDeserializer
  specific_avro_reader: true
  
  # Error handling
  isolation_level: read_committed
  max_partition_fetch_bytes: 1048576
```

### 1.7 Consumer Group Design

| Consumer Group | Topic(s) | Purpose | Parallelism | Lag Alert |
|---------------|----------|---------|-------------|-----------|
| `grcclaw-siem` | enforcement, audit, risk | SIEM event forwarding | 12 | > 10K |
| `grcclaw-data-warehouse` | all | Data warehouse sync | 12 | > 50K |
| `grcclaw-compliance-engine` | evidence, assessment | Compliance recomputation | 6 | > 5K |
| `grcclaw-audit-trail` | all | Audit trail persistence | 6 | > 1K |
| `grcclaw-risk-engine` | enforcement, evidence | Risk scoring | 6 | > 5K |
| `grcclaw-cache-updater` | all | Cache invalidation | 6 | > 10K |
| `grcclaw-flink-stream` | all | Stream processing | 12 | > 100K |
| `grcclaw-alert-manager` | enforcement, risk, compliance | Alert generation | 6 | > 1K |
| `grcclaw-ticketing` | enforcement, assessment | Ticket creation | 6 | > 1K |

### 1.8 Event Delivery Semantics

| Semantics | Configuration | Use Case |
|-----------|--------------|----------|
| **At-most-once** | `enable.auto.commit=true`, `auto.offset_reset=latest` | Metrics, non-critical telemetry |
| **At-least-once** | `enable.auto.commit=false`, manual commit after processing | SIEM forwarding, audit trail, most consumers |
| **Exactly-once** | `enable.idempotence=true`, `isolation.level=read_committed`, transactional producer | Compliance state changes, financial audit events |

**GRC_Claw default:** At-least-once with idempotent consumers. Exactly-once for compliance-critical paths.

### 1.9 Dead Letter Queue (DLQ) Strategy

```yaml
dead_letter_queue:
  topic: grcclaw.dlq
  partitions: 3
  replication_factor: 3
  retention_ms: 2592000000  # 30 days
  
  max_redeliveries: 5
  retry_delays: [1000, 5000, 30000, 120000, 600000]  # 1s, 5s, 30s, 2m, 10m
  
  dlq_event:
    original_topic: string
    original_partition: int
    original_offset: int64
    original_key: string
    original_value: bytes
    error_class: string
    error_message: string
    stack_trace: string
    failed_at: timestamp
    retry_count: int
    consumer_group: string
    tenant_id: string
  
  replay:
    enabled: true
    tool: grcclaw-dlq-replay
    batch_size: 100
    dry_run_default: true
```

### 1.10 Event Versioning & Compatibility

```yaml
event_versioning:
  compatibility_mode: FORWARD  # New readers can read old data
  
  schema_evolution:
    - version: "1.0"
      date: "2026-10-01"
      changes: "Initial schema"
    
    - version: "1.1"
      date: "2027-01-15"
      changes: "Added redaction_details to enforcement events"
      backward_compatible: true
      forward_compatible: true
  
  migration:
    strategy: dual_write  # Write old and new schema during transition
    transition_period: 30d
    cleanup_after: 90d
```

### 1.11 Event Flow Patterns

**Pattern 1: Simple Event Notification**
```
Producer → Kafka Topic → Consumer(s) → Action
```
Used for: SIEM forwarding, cache invalidation, alert generation

**Pattern 2: Event Enrichment**
```
Producer → Kafka → Enrichment Service → Kafka (enriched topic) → Consumer
```
Used for: Adding compliance framework context, risk tier classification

**Pattern 3: Event Aggregation**
```
Multiple Producers → Kafka → Flink Window → Aggregated Topic → Consumer
```
Used for: Compliance score computation, risk trend analysis

**Pattern 4: Event Sourcing**
```
Command → Event Store (Kafka) → Projector → Read Model → Query
```
Used for: Audit trail, compliance state reconstruction

**Pattern 5: CQRS with Event-Driven Sync**
```
Command → Event Store → Kafka → Read Model Updater → Read DB → Query
```
Used for: Dashboard queries, reporting, analytics

### 1.12 Kafka Producer Implementation (Java)

```java
@Component
public class GrcClawEventProducer {
    
    private final KafkaTemplate<String, CloudEvent> kafkaTemplate;
    private final SchemaRegistryClient schemaRegistryClient;
    
    public GrcClawEventProducer(
            KafkaTemplate<String, CloudEvent> kafkaTemplate,
            SchemaRegistryClient schemaRegistryClient) {
        this.kafkaTemplate = kafkaTemplate;
        this.schemaRegistryClient = schemaRegistryClient;
    }
    
    /**
     * Publish an event to the appropriate topic based on event type.
     * Uses tenant_id + entity_id as the key for partition affinity.
     */
    public CompletableFuture<SendResult<String, CloudEvent>> publish(
            String topic, String key, CloudEvent event) {
        
        // Validate against schema registry before publishing
        validateSchema(topic, event);
        
        ProducerRecord<String, CloudEvent> record = 
            new ProducerRecord<>(topic, key, event);
        
        // Add GRC_Claw standard headers
        record.headers()
            .add("tenant_id", event.getExtension("tenant_id").toString().getBytes())
            .add("trace_id", event.getExtension("trace_id").toString().getBytes())
            .add("correlation_id", event.getExtension("correlation_id").toString().getBytes());
        
        return kafkaTemplate.send(record).completable();
    }
    
    /**
     * Publish with exactly-once semantics for compliance-critical events.
     */
    public CompletableFuture<SendResult<String, CloudEvent>> publishExactlyOnce(
            String topic, String key, CloudEvent event) {
        
        return kafkaTemplate.executeInTransaction(operations -> {
            validateSchema(topic, event);
            return operations.send(topic, key, event);
        });
    }
    
    private void validateSchema(String topic, CloudEvent event) {
        // Schema validation against Schema Registry
        String subject = topic + "-value";
        try {
            schemaRegistryClient.getLatestSchemaMetadata(subject);
            // Validate event conforms to latest schema
        } catch (Exception e) {
            throw new EventSchemaValidationException(
                "Event does not conform to schema for topic: " + topic, e);
        }
    }
}
```

### 1.13 Kafka Consumer Implementation (Java)

```java
@Component
public class GrcClawEventConsumer {
    
    private static final Logger log = LoggerFactory.getLogger(GrcClawEventConsumer.class);
    
    private final EventProcessor eventProcessor;
    private final DeadLetterQueueService dlqService;
    private final MeterRegistry meterRegistry;
    
    /**
     * Consumer for enforcement events with manual offset management
     * for at-least-once delivery semantics.
     */
    @KafkaListener(
        topics = "grcclaw.enforcement",
        groupId = "grcclaw-siem-consumer",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumeEnforcementEvents(
            ConsumerRecord<String, CloudEvent> record,
            Acknowledgment acknowledgment) {
        
        CloudEvent event = record.value();
        String tenantId = event.getExtension("tenant_id").toString();
        
        try {
            // Process event
            eventProcessor.processEnforcementEvent(event);
            
            // Manual commit after successful processing
            acknowledgment.acknowledge();
            
            meterRegistry.counter("grcclaw.events.consumed", 
                "topic", "grcclaw.enforcement",
                "tenant", tenantId).increment();
            
        } catch (RetryableException e) {
            log.warn("Retryable error processing event: {}", event.getId(), e);
            // Don't acknowledge — will be redelivered
            throw e;
        } catch (Exception e) {
            log.error("Non-retryable error processing event: {}", event.getId(), e);
            // Send to DLQ
            dlqService.sendToDLQ(record, e, "grcclaw-siem-consumer");
            // Ack to prevent infinite redelivery
            acknowledgment.acknowledge();
            
            meterRegistry.counter("grcclaw.events.dlq", 
                "topic", "grcclaw.enforcement",
                "error", e.getClass().getSimpleName()).increment();
        }
    }
    
    /**
     * Consumer for audit events with exactly-once semantics.
     */
    @KafkaListener(
        topics = "grcclaw.audit",
        groupId = "grcclaw-audit-trail",
        containerFactory = "exactlyOnceKafkaListenerContainerFactory"
    )
    public void consumeAuditEvents(ConsumerRecord<String, CloudEvent> record) {
        CloudEvent event = record.value();
        eventProcessor.processAuditEvent(event);
        // Offset managed by transactional producer
    }
}
```

### 1.14 Event Enrichment Service

```java
@Service
public class EventEnrichmentService {
    
    private final ComplianceFrameworkClient frameworkClient;
    private final RiskEngineClient riskClient;
    private final KafkaTemplate<String, CloudEvent> kafkaTemplate;
    
    /**
     * Consumes raw events, enriches with compliance and risk context,
     * and publishes to enriched topic.
     */
    @KafkaListener(
        topics = "grcclaw.enforcement",
        groupId = "grcclaw-event-enricher"
    )
    public void enrichEnforcementEvent(ConsumerRecord<String, CloudEvent> record) {
        CloudEvent event = record.value();
        
        // Enrich with compliance framework context
        Set<String> frameworks = frameworkClient
            .getFrameworksForPolicy(event.getExtension("policy_id").toString());
        
        // Enrich with risk tier
        RiskTier riskTier = riskClient
            .getRiskTierForAgent(event.getExtension("agent_id").toString());
        
        // Build enriched event
        CloudEvent enrichedEvent = CloudEventBuilder.v1()
            .withId(event.getId())
            .withSource(event.getSource())
            .withType(event.getType())
            .withSubject(event.getSubject())
            .withTime(event.getTime())
            .withDataContentType(event.getDataContentType())
            .withData(event.getData())
            .withExtension("tenant_id", event.getExtension("tenant_id"))
            .withExtension("environment", event.getExtension("environment"))
            .withExtension("trace_id", event.getExtension("trace_id"))
            .withExtension("compliance_frameworks", frameworks)
            .withExtension("risk_tier", riskTier.name())
            .withExtension("enriched_at", Instant.now().toString())
            .build();
        
        // Publish to enriched topic
        kafkaTemplate.send("grcclaw.enforcement.enriched", 
            record.key(), enrichedEvent);
    }
}
```

---

## 2. Streaming Processing (Flink)

### 2.1 Architecture Overview

GRC_Claw uses Apache Flink for real-time stream processing of governance events. Flink jobs consume from Kafka topics, perform complex event processing (CEP), windowed aggregations, and real-time compliance scoring.

```
Kafka Source Topics → Flink Cluster → Flink Sinks
  (enforcement,         (5 jobs)        (Kafka, TimescaleDB,
   evidence, risk,                       Elasticsearch, Redis,
   audit, compliance,                     Alert Manager, S3)
   agent)
```

### 2.2 Flink Job Definitions

#### Job 1: Real-Time Compliance Scoring

```java
/**
 * Computes compliance scores in real-time from evidence and assessment streams.
 * 
 * Source: grcclaw.evidence, grcclaw.assessment
 * Sink: grcclaw.compliance (real-time updates), TimescaleDB (time-series)
 * 
 * Windows: Tumbling 1min (real-time), Sliding 5min (trend), Tumbling 1h (stable)
 */
public class ComplianceScoringJob {
    
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // Checkpointing for exactly-once
        env.enableCheckpointing(60000);  // 1 minute
        env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
        env.getCheckpointConfig().setMinPauseBetweenCheckpoints(30000);
        env.getCheckpointConfig().setCheckpointTimeout(120000);
        env.setStateBackend(new RocksDBStateBackend("s3://grcclaw-checkpoints/compliance"));
        
        // Source: Evidence stream
        DataStream<EvidenceEvent> evidenceStream = env
            .fromSource(
                KafkaSource.<EvidenceEvent>builder()
                    .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                    .setTopics("grcclaw.evidence")
                    .setGroupId("flink-compliance-scoring")
                    .setStartingOffsets(OffsetsInitializer.committedOffsets(OffsetResetStrategy.EARLIEST))
                    .setDeserializer(new EvidenceEventDeserializer())
                    .build(),
                WatermarkStrategy
                    .<EvidenceEvent>forBoundedOutOfOrderness(Duration.ofSeconds(30))
                    .withTimestampAssigner((event, timestamp) -> event.getTimestamp()),
                "evidence-source"
            );
        
        // Source: Assessment stream
        DataStream<AssessmentEvent> assessmentStream = env
            .fromSource(
                KafkaSource.<AssessmentEvent>builder()
                    .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                    .setTopics("grcclaw.assessment")
                    .setGroupId("flink-compliance-scoring")
                    .setStartingOffsets(OffsetsInitializer.committedOffsets(OffsetResetStrategy.EARLIEST))
                    .setDeserializer(new AssessmentEventDeserializer())
                    .build(),
                WatermarkStrategy
                    .<AssessmentEvent>forBoundedOutOfOrderness(Duration.ofSeconds(30))
                    .withTimestampAssigner((event, timestamp) -> event.getTimestamp()),
                "assessment-source"
            );
        
        // Compute compliance scores per framework per window
        DataStream<ComplianceScore> scores = evidenceStream
            .keyBy(EvidenceEvent::getFrameworkId)
            .window(TumblingEventTimeWindows.of(Time.minutes(1)))
            .aggregate(new ComplianceScoreAggregateFunction())
            .name("compliance-score-1min");
        
        // Compute 5-minute sliding window for trend
        DataStream<ComplianceTrend> trends = scores
            .keyBy(ComplianceScore::getFrameworkId)
            .window(SlidingEventTimeWindows.of(Time.minutes(5), Time.minutes(1)))
            .aggregate(new ComplianceTrendAggregateFunction())
            .name("compliance-trend-5min");
        
        // Sink to Kafka for downstream consumers
        scores.sinkTo(
            KafkaSink.<ComplianceScore>builder()
                .setBootstrapServers("kafka-1:9092,kafka-2:9092,kafka-3:9092")
                .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                    .setTopic("grcclaw.compliance.realtime")
                    .setValueSerializationSchema(new ComplianceScoreSerializer())
                    .build())
                .setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)
                .setTransactionalIdPrefix("flink-compliance-")
                .build()
        ).name("kafka-compliance-sink");
        
        // Sink to TimescaleDB for time-series storage
        scores.addSink(new TimescaleDBSink<>(
            "jdbc:postgresql://timescale:5432/grcclaw",
            "compliance_score",
            ComplianceScore::toSql
        )).name("timescale-sink");
        
        env.execute("Real-Time Compliance Scoring");
    }
}
```

#### Job 2: Risk Signal Detection (CEP)

```java
/**
 * Detects risk patterns in real-time using Flink CEP.
 * 
 * Patterns detected:
 * 1. Repeated policy violations by same agent within time window
 * 2. Compliance score rapid decline
 * 3. Evidence verification failure spike
 * 4. Agent trust score degradation pattern
 * 
 * Source: grcclaw.enforcement, grcclaw.evidence, grcclaw.agent
 * Sink: grcclaw.risk (risk alerts), Alert Manager
 */
public class RiskSignalDetectionJob {
    
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(30000);
        
        // Source: Enforcement decisions
        DataStream<EnforcementEvent> enforcementStream = env
            .fromSource(kafkaSource("grcclaw.enforcement", "flink-risk-detection"),
                WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofSeconds(10)),
                "enforcement-source"
            );
        
        // Pattern 1: Repeated violations by same agent (3+ DENY in 5 minutes)
        Pattern<EnforcementEvent, ?> repeatedViolations = Pattern
            .<EnforcementEvent>begin("first")
            .where(evt -> evt.getDecision().equals("DENY"))
            .next("second")
            .where(evt -> evt.getDecision().equals("DENY"))
            .next("third")
            .where(evt -> evt.getDecision().equals("DENY"))
            .within(Time.minutes(5));
        
        // Pattern 2: Escalation cascade (DENY → REQUIRE_APPROVAL → QUARANTINE in 10 min)
        Pattern<EnforcementEvent, ?> escalationCascade = Pattern
            .<EnforcementEvent>begin("deny")
            .where(evt -> evt.getDecision().equals("DENY"))
            .next("approval")
            .where(evt -> evt.getDecision().equals("REQUIRE_APPROVAL"))
            .next("quarantine")
            .where(evt -> evt.getDecision().equals("QUARANTINE"))
            .within(Time.minutes(10));
        
        // Pattern 3: High-risk agent with increasing violation rate
        Pattern<EnforcementEvent, ?> highRiskAgent = Pattern
            .<EnforcementEvent>begin("start")
            .where(evt -> evt.getRiskTier().equals("high") || evt.getRiskTier().equals("prohibited"))
            .timesOrMore(5)
            .within(Time.minutes(15));
        
        // Apply patterns
        DataStream<RiskAlert> violationAlerts = CEP.pattern(
            enforcementStream.keyBy(EnforcementEvent::getAgentId),
            repeatedViolations
        ).process(new PatternHandler("REPEATED_VIOLATIONS", RiskTier.HIGH));
        
        DataStream<RiskAlert> cascadeAlerts = CEP.pattern(
            enforcementStream.keyBy(EnforcementEvent::getAgentId),
            escalationCascade
        ).process(new PatternHandler("ESCALATION_CASCADE", RiskTier.CRITICAL));
        
        DataStream<RiskAlert> highRiskAlerts = CEP.pattern(
            enforcementStream.keyBy(EnforcementEvent::getAgentId),
            highRiskAgent
        ).process(new PatternHandler("HIGH_RISK_BEHAVIOR", RiskTier.HIGH));
        
        // Union all risk alerts
        DataStream<RiskAlert> allAlerts = violationAlerts
            .union(cascadeAlerts, highRiskAlerts);
        
        // Sink to risk topic and alert manager
        allAlerts.sinkTo(kafkaSink("grcclaw.risk.alerts"));
        allAlerts.addSink(new AlertManagerSink());
        
        env.execute("Risk Signal Detection");
    }
}
```

#### Job 3: Evidence Stream Processing

```java
/**
 * Real-time evidence validation, verification level upgrading, and cross-validation.
 * 
 * Source: grcclaw.evidence
 * Sink: grcclaw.evidence.verified, grcclaw.evidence.enriched
 */
public class EvidenceStreamProcessingJob {
    
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(60000);
        
        DataStream<EvidenceEvent> evidenceStream = env
            .fromSource(kafkaSource("grcclaw.evidence", "flink-evidence-processing"),
                WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofSeconds(30)),
                "evidence-source"
            );
        
        // Step 1: Schema validation
        DataStream<ValidatedEvidence> validated = evidenceStream
            .map(new SchemaValidationMapper())
            .filter(ValidatedEvidence::isValid)
            .name("schema-validation");
        
        // Step 2: Hash verification
        DataStream<VerifiedEvidence> verified = validated
            .map(new HashVerificationMapper())
            .name("hash-verification");
        
        // Step 3: Cross-validation (join with existing evidence for same control)
        DataStream<CrossValidatedEvidence> crossValidated = verified
            .keyBy(VerifiedEvidence::getControlId)
            .window(TumblingEventTimeWindows.of(Time.minutes(5)))
            .process(new CrossValidationFunction())
            .name("cross-validation");
        
        // Step 4: Verification level upgrading
        DataStream<EnrichedEvidence> enriched = crossValidated
            .map(new VerificationLevelUpgrader())
            .name("level-upgrade");
        
        // Sink
        enriched.sinkTo(kafkaSink("grcclaw.evidence.verified"));
        enriched.addSink(new EvidenceStoreSink());
        
        env.execute("Evidence Stream Processing");
    }
}
```

### 2.3 Windowing Strategy

| Window Type | Size | Slide | Use State | Use Case |
|-------------|------|-------|-----------|----------|
| Tumbling | 1 min | — | 1 min | Real-time compliance score |
| Tumbling | 5 min | — | 5 min | Stable compliance snapshot |
| Tumbling | 1 hour | — | 1 hour | Hourly compliance report |
| Sliding | 5 min | 1 min | 5 min | Compliance trend detection |
| Sliding | 1 hour | 5 min | 1 hour | Risk trend analysis |
| Session | 30 min gap | — | Variable | Agent behavior session analysis |
| Global | — | — | Unlimited | Audit trail Merkle tree |

### 2.4 State Management

```yaml
flink_state:
  backend: rocksdb
  storage: s3://grcclaw-checkpoints/flink
  
  checkpoints:
    interval: 60s
    timeout: 120s
    min_pause: 30s
    max_concurrent: 1
    retain_on_cancellation: true
  
  savepoints:
    interval: 3600s  # Hourly
    storage: s3://grcclaw-savepoints/flink
  
  state_ttl:
    compliance_scores: 7d
    risk_signals: 30d
    evidence_cache: 1d
    agent_sessions: 24h
  
  incremental_checkpoints: true
  local_recovery: true
  unaligned_checkpoints: false
```

### 2.5 Flink Deployment

```yaml
flink_deployment:
  mode: native_kubernetes
  
  job_manager:
    replicas: 2
    resources:
      memory: 4Gi
      cpu: 2
  
  task_manager:
    replicas: 6
    slots: 4
    resources:
      memory: 8Gi
      cpu: 4
  
  parallelism:
    default: 12
    compliance_scoring: 12
    risk_detection: 12
    evidence_processing: 12
    audit_aggregation: 6
    agent_analytics: 6
  
  restart_strategy:
    type: exponential_delay
    initial_backoff: 1s
    max_backoff: 60s
    reset_backoff_after: 10
    max_restarts_per_hour: 10
```

### 2.6 Stream Processing SLAs

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-end latency (p99) | < 5 seconds | Kafka source to sink |
| Checkpoint duration | < 30 seconds | Per checkpoint |
| Recovery time | < 2 minutes | From checkpoint |
| Watermark lag | < 30 seconds | Behind real-time |
| State size per job | < 10 GB | RocksDB on S3 |
| Processing throughput | 100K events/sec | Per job |

---

## 3. CQRS Implementation

### 3.1 Architecture Overview

GRC_Claw employs CQRS (Command Query Responsibility Segregation) and Event Sourcing to separate write and read models, enabling optimized query performance, temporal queries, and full audit reconstruction.

```
Command Side (Write Model)          Event Bus (Kafka)         Query Side (Read Model)
┌─────────────────────┐           ┌──────────────┐           ┌─────────────────────┐
│ REST/gRPC/GraphQL   │           │ grcclaw.     │           │ Projectors (Flink)  │
│ → Command Handler   │           │ commands     │           │ → Compliance Read DB│
│ → Aggregate Root    │           │ grcclaw.     │           │ → Evidence Search   │
│ → Event Store       │──────────▶│ events       │──────────▶│ → Agent Cache       │
│   (Kafka + DB)      │           │ grcclaw.     │           │ → Audit Time-Series │
│                     │           │ projections  │           │ → Risk Graph DB     │
└─────────────────────┘           └──────────────┘           └─────────────────────┘
```

### 3.2 Command Side

**Command Definition:**

```java
public interface Command {
    String getCommandId();
    String getAggregateId();
    String getTenantId();
    Instant getTimestamp();
    String getUserId();
}

// Example commands
public record CreatePolicyCommand(
    String commandId,
    String aggregateId,  // policy_id
    String tenantId,
    Instant timestamp,
    String userId,
    String name,
    String description,
    String category,
    String cedarPolicy,
    Map<String, String> metadata
) implements Command {}

public record ActivatePolicyCommand(
    String commandId,
    String aggregateId,
    String tenantId,
    Instant timestamp,
    String userId,
    String reason
) implements Command {}

public record SubmitEvidenceCommand(
    String commandId,
    String aggregateId,  // evidence_id
    String tenantId,
    Instant timestamp,
    String userId,
    String policyId,
    String controlId,
    String framework,
    EvidenceContent content,
    EvidenceSource source
) implements Command {}
```

**Command Handler:**

```java
@Component
public class PolicyCommandHandler {
    
    private final EventStore eventStore;
    private final PolicyAggregateRepository repository;
    
    @Transactional
    public List<DomainEvent> handle(CreatePolicyCommand command) {
        // 1. Load aggregate
        PolicyAggregate aggregate = repository.findById(command.aggregateId())
            .orElse(new PolicyAggregate(command.aggregateId()));
        
        // 2. Execute business logic
        List<DomainEvent> events = aggregate.createPolicy(
            command.name(),
            command.description(),
            command.category(),
            command.cedarPolicy(),
            command.metadata(),
            command.userId()
        );
        
        // 3. Persist events
        eventStore.append(events);
        
        return events;
    }
    
    @Transactional
    public List<DomainEvent> handle(ActivatePolicyCommand command) {
        PolicyAggregate aggregate = repository.findById(command.aggregateId())
            .orElseThrow(() -> new AggregateNotFoundException(command.aggregateId()));
        
        List<DomainEvent> events = aggregate.activatePolicy(
            command.reason(),
            command.userId()
        );
        
        eventStore.append(events);
        return events;
    }
}
```

### 3.3 Event Store Schema

```sql
-- Event Store (PostgreSQL)
CREATE TABLE event_store (
    event_id UUID PRIMARY KEY,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    event_type VARCHAR(200) NOT NULL,
    event_version INTEGER NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sequence_number BIGSERIAL NOT NULL,
    correlation_id UUID,
    causation_id UUID,
    payload JSONB NOT NULL,
    metadata JSONB,
    
    UNIQUE (aggregate_id, event_version)
);

CREATE INDEX idx_event_store_aggregate ON event_store (aggregate_id, event_version);
CREATE INDEX idx_event_store_tenant ON event_store (tenant_id, timestamp);
CREATE INDEX idx_event_store_type ON event_store (event_type, timestamp);
CREATE INDEX idx_event_store_correlation ON event_store (correlation_id);

-- Snapshot Table (for performance)
CREATE TABLE aggregate_snapshots (
    aggregate_id UUID PRIMARY KEY,
    aggregate_type VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    state JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Event Store (Kafka topic for distribution)
-- Topic: grcclaw.events
-- Partitions: 12
-- Key: aggregate_id
-- Value: Avro-serialized DomainEvent
```

### 3.4 Domain Events

```java
public interface DomainEvent {
    String getEventId();
    String getAggregateId();
    String getAggregateType();
    String getEventType();
    int getEventVersion();
    String getTenantId();
    Instant getTimestamp();
    UUID getCorrelationId();
    UUID getCausationId();
}

// Policy Events
public record PolicyCreatedEvent(
    String eventId,
    String aggregateId,
    int eventVersion,
    String tenantId,
    Instant timestamp,
    UUID correlationId,
    UUID causationId,
    String name,
    String description,
    String category,
    String cedarPolicy,
    String createdBy
) implements DomainEvent {
    public String getAggregateType() { return "Policy"; }
    public String getEventType() { return "PolicyCreated"; }
}

public record PolicyActivatedEvent(
    String eventId,
    String aggregateId,
    int eventVersion,
    String tenantId,
    Instant timestamp,
    UUID correlationId,
    UUID causationId,
    String activatedBy,
    Instant effectiveDate
) implements DomainEvent {
    public String getAggregateType() { return "Policy"; }
    public String getEventType() { return "PolicyActivated"; }
}

// Evidence Events
public record EvidenceSubmittedEvent(
    String eventId,
    String aggregateId,
    int eventVersion,
    String tenantId,
    Instant timestamp,
    UUID correlationId,
    UUID causationId,
    String policyId,
    String controlId,
    String framework,
    EvidenceContent content,
    EvidenceSource source,
    String submittedBy
) implements DomainEvent {
    public String getAggregateType() { return "Evidence"; }
    public String getEventType() { return "EvidenceSubmitted"; }
}

public record EvidenceVerifiedEvent(
    String eventId,
    String aggregateId,
    int eventVersion,
    String tenantId,
    Instant timestamp,
    UUID correlationId,
    UUID causationId,
    VerificationLevel newLevel,
    String verifiedBy,
    boolean hashMatch,
    boolean chainIntact
) implements DomainEvent {
    public String getAggregateType() { return "Evidence"; }
    public String getEventType() { return "EvidenceVerified"; }
}
```

### 3.5 Aggregate Root Example

```java
public class PolicyAggregate {
    
    private String policyId;
    private String name;
    private String description;
    private String category;
    private String cedarPolicy;
    private PolicyStatus status;
    private int version;
    private String tenantId;
    private Instant createdAt;
    private Instant updatedAt;
    private String createdBy;
    private String updatedBy;
    
    private List<DomainEvent> uncommittedEvents = new ArrayList<>();
    
    // Command handlers
    public List<DomainEvent> createPolicy(String name, String description, 
            String category, String cedarPolicy, Map<String, String> metadata,
            String userId) {
        if (this.status != null) {
            throw new IllegalStateException("Policy already exists");
        }
        
        DomainEvent event = new PolicyCreatedEvent(
            UUID.randomUUID().toString(),
            this.policyId,
            1,
            this.tenantId,
            Instant.now(),
            UUID.randomUUID(),
            null,
            name,
            description,
            category,
            cedarPolicy,
            userId
        );
        
        uncommittedEvents.add(event);
        apply(event);
        return uncommittedEvents;
    }
    
    public List<DomainEvent> activatePolicy(String reason, String userId) {
        if (this.status != PolicyStatus.DRAFT && this.status != PolicyStatus.REVIEW) {
            throw new IllegalStateException(
                "Cannot activate policy from status: " + this.status);
        }
        
        DomainEvent event = new PolicyActivatedEvent(
            UUID.randomUUID().toString(),
            this.policyId,
            this.version + 1,
            this.tenantId,
            Instant.now(),
            UUID.randomUUID(),
            null,
            userId,
            Instant.now()
        );
        
        uncommittedEvents.add(event);
        apply(event);
        return uncommittedEvents;
    }
    
    // Event sourcing: state reconstruction
    public void apply(DomainEvent event) {
        switch (event) {
            case PolicyCreatedEvent e -> {
                this.name = e.name();
                this.description = e.description();
                this.category = e.category();
                this.cedarPolicy = e.cedarPolicy();
                this.status = PolicyStatus.DRAFT;
                this.version = e.eventVersion();
                this.createdAt = e.timestamp();
                this.createdBy = e.createdBy();
            }
            case PolicyActivatedEvent e -> {
                this.status = PolicyStatus.ACTIVE;
                this.version = e.eventVersion();
                this.updatedAt = e.timestamp();
                this.updatedBy = e.activatedBy();
            }
        }
    }
    
    // Rehydrate from event store
    public static PolicyAggregate rehydrate(List<DomainEvent> events) {
        PolicyAggregate aggregate = new PolicyAggregate();
        events.forEach(aggregate::apply);
        return aggregate;
    }
}
```

### 3.6 Read Model Projections

**Compliance Read Model:**

```sql
-- Compliance Read Model (PostgreSQL)
CREATE TABLE compliance_read_model (
    compliance_id UUID PRIMARY KEY,
    organization_id VARCHAR(100) NOT NULL,
    framework_id VARCHAR(100) NOT NULL,
    framework_name VARCHAR(200) NOT NULL,
    overall_status VARCHAR(50) NOT NULL,
    compliance_score DECIMAL(5,4) NOT NULL,
    trend VARCHAR(20) NOT NULL,
    total_controls INTEGER NOT NULL,
    compliant_controls INTEGER NOT NULL,
    partial_controls INTEGER NOT NULL,
    non_compliant_controls INTEGER NOT NULL,
    not_applicable_controls INTEGER NOT NULL,
    not_assessed_controls INTEGER NOT NULL,
    coverage_percentage DECIMAL(5,2) NOT NULL,
    last_computed_at TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    
    UNIQUE (organization_id, framework_id)
);

-- Compliance Control Read Model
CREATE TABLE compliance_control_read_model (
    id UUID PRIMARY KEY,
    compliance_id UUID REFERENCES compliance_read_model(compliance_id),
    control_id VARCHAR(100) NOT NULL,
    control_title VARCHAR(500) NOT NULL,
    control_family VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL,
    evidence_count INTEGER NOT NULL,
    last_verified TIMESTAMPTZ,
    next_due TIMESTAMPTZ,
    gap_description TEXT
);
```

**Agent Read Model (Redis):**

```json
{
  "agent_id": "agent-42",
  "name": "Data Analyst Agent",
  "type": "agent",
  "status": "active",
  "risk_tier": "limited",
  "trust_score": 0.85,
  "policy_count": 5,
  "active_policies": ["pol-001", "pol-002", "pol-003"],
  "enforcement_stats_24h": {
    "total": 150,
    "allowed": 140,
    "denied": 8,
    "require_approval": 2
  },
  "compliance_posture": {
    "SOC2": 0.92,
    "ISO-27001": 0.88,
    "NIST-800-53": 0.85
  },
  "last_updated": "2026-10-01T12:00:00Z"
}
```

### 3.7 Temporal Queries

Event sourcing enables temporal queries — reconstructing entity state at any point in time:

```java
@Service
public class TemporalQueryService {
    
    private final EventStore eventStore;
    
    /**
     * Reconstruct entity state at a specific point in time.
     */
    public Policy getStateAt(String policyId, Instant timestamp) {
        List<DomainEvent> events = eventStore
            .findByAggregateIdAndTimestamp(policyId, timestamp);
        
        PolicyAggregate aggregate = PolicyAggregate.rehydrate(events);
        return aggregate.toPolicy();
    }
    
    /**
     * Get all versions of an entity within a time range.
     */
    public List<PolicyVersion> getVersionsInTimeRange(
            String policyId, Instant from, Instant to) {
        List<DomainEvent> events = eventStore
            .findByAggregateIdAndTimeRange(policyId, from, to);
        
        return events.stream()
            .filter(e -> e instanceof PolicyCreatedEvent 
                      || e instanceof PolicyUpdatedEvent)
            .map(e -> new PolicyVersion(
                e.getEventVersion(),
                e.getEventType(),
                e.getTimestamp(),
                extractPolicyState(e)
            ))
            .collect(Collectors.toList());
    }
    
    /**
     * Compare entity state between two points in time.
     */
    public PolicyDiff compareStates(String policyId, 
            Instant time1, Instant time2) {
        Policy state1 = getStateAt(policyId, time1);
        Policy state2 = getStateAt(policyId, time2);
        
        return PolicyDiff.compare(state1, state2);
    }
}
```

### 3.8 CQRS Configuration

```yaml
cqrs:
  command_side:
    event_store:
      type: postgresql
      connection: ${EVENT_STORE_URL}
      pool_size: 20
    
    snapshot:
      enabled: true
      threshold: 10  # Create snapshot every 10 events
      retention: 5   # Keep last 5 snapshots
    
    outbox:
      enabled: true
      table: outbox_events
      poll_interval: 1s
      batch_size: 100
  
  query_side:
    projections:
      - name: compliance-projection
        source: grcclaw.events
        filter: "event_type LIKE 'Compliance%'"
        target: compliance_read_model
        projector: ComplianceProjector
      
      - name: evidence-projection
        source: grcclaw.events
        filter: "event_type LIKE 'Evidence%'"
        target: evidence_search_index
        projector: EvidenceProjector
      
      - name: agent-projection
        source: grcclaw.events
        filter: "event_type LIKE 'Agent%'"
        target: agent_cache
        projector: AgentProjector
      
      - name: audit-projection
        source: grcclaw.events
        filter: "event_type LIKE 'Audit%'"
        target: audit_timeseries
        projector: AuditProjector
    
    read_models:
      compliance:
        store: postgresql
        refresh_interval: 5s
        consistency: eventual
      
      evidence:
        store: elasticsearch
        refresh_interval: 1s
        consistency: eventual
      
      agent:
        store: redis
        refresh_interval: 1s
        consistency: eventual
      
      audit:
        store: timescaledb
        refresh_interval: 10s
        consistency: eventual
  
  consistency:
    strategy: eventual
    max_staleness: 30s
    read_your_writes: true  # Read from command side for own writes
```

---

## 4. Saga Pattern

### 4.1 Architecture Overview

GRC_Claw uses the Saga pattern to manage distributed transactions across multiple services. Each saga consists of a sequence of local transactions with compensating actions for rollback.

```
Saga Orchestrator
  ├── Step Executor (Invoke, Retry, Timeout)
  ├── Compensate Action (Reverse, Cleanup, Notify)
  └── State Store (Persist, Query, Audit)
```

### 4.2 Saga Definitions

**Saga: Policy Activation**
```
Step 1: Validate Policy ──▶ Policy Service
   └─ Compensate: None (read-only)

Step 2: Compile Policy ──▶ Policy Compiler
   └─ Compensate: Delete compiled rules

Step 3: Distribute Rules ──▶ Enforcement Engine
   └─ Compensate: Remove rules from enforcement

Step 4: Update Policy Status ──▶ Policy Service
   └─ Compensate: Revert status to DRAFT

Step 5: Publish Event ──▶ Kafka
   └─ Compensate: Publish cancellation event

Step 6: Update Cache ──▶ Redis
   └─ Compensate: Invalidate cache
```

**Saga: Evidence Collection & Verification**
```
Step 1: Collect Evidence ──▶ Evidence Collector
   └─ Compensate: Mark evidence as failed

Step 2: Normalize to OSCAL ──▶ Evidence Orchestrator
   └─ Compensate: Delete normalized evidence

Step 3: Validate Schema ──▶ Validation Service
   └─ Compensate: None (read-only)

Step 4: Store Evidence ──▶ Evidence Store
   └─ Compensate: Delete evidence

Step 5: Verify Hash ──▶ Verification Service
   └─ Compensate: Reset verification level

Step 6: Update Compliance ──▶ Compliance Engine
   └─ Compensate: Revert compliance score

Step 7: Publish Event ──▶ Kafka
   └─ Compensate: Publish cancellation event
```

**Saga: Agent Registration & Onboarding**
```
Step 1: Register Agent ──▶ Agent Registry
   └─ Compensate: Delete agent record

Step 2: Create Identity ──▶ IAM Service
   └─ Compensate: Revoke identity

Step 3: Issue Certificate ──▶ Certificate Authority
   └─ Compensate: Revoke certificate

Step 4: Bind Policies ──▶ Policy Engine
   └─ Compensate: Unbind policies

Step 5: Create Audit Trail ──▶ Audit Service
   └─ Compensate: Mark audit entry as cancelled

Step 6: Notify SIEM ──▶ SIEM Connector
   └─ Compensate: Send cancellation to SIEM

Step 7: Update Inventory ──▶ CMDB
   └─ Compensate: Remove from inventory
```

### 4.3 Saga Definition (YAML)

```yaml
sagas:
  - name: policy_activation
    description: Activate a policy and distribute to enforcement engines
    version: "1.0"
    
    steps:
      - id: validate_policy
        service: policy-service
        action: validate
        input: "${policy_id}"
        output: "${validation_result}"
        compensate:
          action: none  # Read-only step
        retry:
          max_attempts: 3
          backoff: exponential
        timeout: 10s
      
      - id: compile_policy
        service: policy-compiler
        action: compile
        input: "${policy_id}"
        output: "${compiled_rules}"
        compensate:
          action: delete_compiled_rules
          service: policy-compiler
          input: "${policy_id}"
        retry:
          max_attempts: 3
          backoff: exponential
        timeout: 30s
      
      - id: distribute_rules
        service: enforcement-engine
        action: load_rules
        input: "${compiled_rules}"
        compensate:
          action: remove_rules
          service: enforcement-engine
          input: "${policy_id}"
        retry:
          max_attempts: 5
          backoff: exponential
        timeout: 60s
      
      - id: update_status
        service: policy-service
        action: update_status
        input:
          policy_id: "${policy_id}"
          status: "active"
        compensate:
          action: update_status
          service: policy-service
          input:
            policy_id: "${policy_id}"
            status: "draft"
        retry:
          max_attempts: 3
          backoff: exponential
        timeout: 10s
      
      - id: publish_event
        service: kafka-producer
        action: publish
        input:
          topic: "grcclaw.policy"
          event_type: "PolicyActivated"
          payload: "${policy_id}"
        compensate:
          action: publish
          service: kafka-producer
          input:
            topic: "grcclaw.policy"
            event_type: "PolicyActivationCancelled"
            payload: "${policy_id}"
        retry:
          max_attempts: 3
          backoff: exponential
        timeout: 10s
      
      - id: update_cache
        service: redis
        action: set
        input:
          key: "policy:${policy_id}"
          value: "${policy_data}"
        compensate:
          action: delete
          service: redis
          input:
            key: "policy:${policy_id}"
        retry:
          max_attempts: 3
          backoff: exponential
        timeout: 5s
    
    on_success:
      - action: audit_log
        entry: "Policy ${policy_id} activated successfully"
      - action: notify
        channel: "policy-activations"
    
    on_failure:
      - action: audit_log
        entry: "Policy ${policy_id} activation failed at step ${failed_step}"
      - action: notify
        channel: "policy-activation-failures"
        severity: "high"
      - action: create_ticket
        system: "jira"
        template: "policy_activation_failure"
```

### 4.4 Saga Orchestrator Implementation

```java
@Component
public class SagaOrchestrator {
    
    private final SagaStateRepository stateRepository;
    private final StepExecutor stepExecutor;
    private final CompensateActionExecutor compensateExecutor;
    private final KafkaTemplate<String, SagaEvent> kafkaTemplate;
    
    @Transactional
    public SagaInstance startSaga(String sagaName, Map<String, Object> input) {
        SagaDefinition sagaDef = sagaRegistry.get(sagaName);
        
        SagaInstance instance = SagaInstance.builder()
            .sagaId(UUID.randomUUID().toString())
            .sagaName(sagaName)
            .status(SagaStatus.STARTED)
            .currentStep(0)
            .input(input)
            .startTime(Instant.now())
            .build();
        
        stateRepository.save(instance);
        executeNextStep(instance, sagaDef);
        
        return instance;
    }
    
    private void executeNextStep(SagaInstance instance, SagaDefinition sagaDef) {
        if (instance.getCurrentStep() >= sagaDef.getSteps().size()) {
            completeSaga(instance, sagaDef);
            return;
        }
        
        SagaStep step = sagaDef.getSteps().get(instance.getCurrentStep());
        
        try {
            // Execute step
            Map<String, Object> result = stepExecutor.execute(step, instance.getInput());
            
            // Update instance with step result
            instance.getStepResults().put(step.getId(), result);
            instance.getInput().putAll(result);
            instance.setCurrentStep(instance.getCurrentStep() + 1);
            stateRepository.save(instance);
            
            // Continue to next step
            executeNextStep(instance, sagaDef);
            
        } catch (StepExecutionException e) {
            // Step failed — start compensation
            log.error("Saga step failed: {}", step.getId(), e);
            compensateSaga(instance, sagaDef);
        }
    }
    
    private void compensateSaga(SagaInstance instance, SagaDefinition sagaDef) {
        instance.setStatus(SagaStatus.COMPENSATING);
        stateRepository.save(instance);
        
        // Compensate completed steps in reverse order
        List<SagaStep> completedSteps = sagaDef.getSteps().subList(
            0, instance.getCurrentStep());
        
        Collections.reverse(completedSteps);
        
        for (SagaStep step : completedSteps) {
            if (step.getCompensate() == null || 
                "none".equals(step.getCompensate().getAction())) {
                continue;  // No compensation needed
            }
            
            try {
                compensateExecutor.execute(step.getCompensate(), instance.getInput());
                instance.getCompensatedSteps().add(step.getId());
            } catch (CompensateException e) {
                // Compensation failure — requires manual intervention
                log.error("Compensation failed for step: {}", step.getId(), e);
                instance.setStatus(SagaStatus.COMPENSATION_FAILED);
                stateRepository.save(instance);
                
                // Alert operations team
                alertCompensationFailure(instance, step, e);
                return;
            }
        }
        
        instance.setStatus(SagaStatus.COMPENSATED);
        instance.setEndTime(Instant.now());
        stateRepository.save(instance);
        
        // Publish saga failed event
        kafkaTemplate.send("grcclaw.saga.events", new SagaFailedEvent(
            instance.getSagaId(),
            instance.getSagaName(),
            instance.getCurrentStep(),
            instance.getStepResults()
        ));
    }
    
    private void completeSaga(SagaInstance instance, SagaDefinition sagaDef) {
        instance.setStatus(SagaStatus.COMPLETED);
        instance.setEndTime(Instant.now());
        stateRepository.save(instance);
        
        // Execute success callbacks
        sagaDef.getOnSuccess().forEach(action -> executeCallback(action, instance));
        
        // Publish saga completed event
        kafkaTemplate.send("grcclaw.saga.events", new SagaCompletedEvent(
            instance.getSagaId(),
            instance.getSagaName(),
            instance.getStepResults()
        ));
    }
}
```

### 4.5 Saga State Store

```sql
CREATE TABLE saga_instances (
    saga_id UUID PRIMARY KEY,
    saga_name VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- STARTED, COMPLETED, COMPENSATING, COMPENSATED, COMPENSATION_FAILED
    current_step INTEGER NOT NULL DEFAULT 0,
    input JSONB NOT NULL,
    step_results JSONB NOT NULL DEFAULT '{}',
    compensated_steps TEXT[] DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    tenant_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_saga_status ON saga_instances (status, started_at);
CREATE INDEX idx_saga_tenant ON saga_instances (tenant_id, started_at);

CREATE TABLE saga_step_history (
    id BIGSERIAL PRIMARY KEY,
    saga_id UUID REFERENCES saga_instances(saga_id),
    step_id VARCHAR(200) NOT NULL,
    step_order INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,  -- SUCCESS, FAILED, COMPENSATED, COMPENSATION_FAILED
    input JSONB,
    output JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### 4.6 Saga Monitoring

```yaml
saga_monitoring:
  metrics:
    - name: saga_started_total
      type: counter
      labels: [saga_name]
    
    - name: saga_completed_total
      type: counter
      labels: [saga_name, status]
    
    - name: saga_step_duration_seconds
      type: histogram
      labels: [saga_name, step_id]
      buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60]
    
    - name: saga_compensation_total
      type: counter
      labels: [saga_name, step_id]
    
    - name: saga_compensation_failures_total
      type: counter
      labels: [saga_name, step_id]
  
  alerts:
    - name: HighSagaFailureRate
      condition: rate(saga_completed_total{status="COMPENSATION_FAILED"}[5m]) > 0.01
      duration: 5m
      severity: critical
    
    - name: SagaCompensationFailure
      condition: saga_compensation_failures_total > 0
      duration: 1m
      severity: critical
    
    - name: SagaStepSlow
      condition: histogram_quantile(0.99, saga_step_duration_seconds) > 30
      duration: 5m
      severity: warning
```

---

## 5. API Composition

### 5.1 Architecture Overview

GRC_Claw provides an API composition layer that aggregates data from multiple services into unified responses, reducing client-side round trips and enabling complex dashboard queries.

```
Client Requests → API Composition Gateway → Backend Services
                  (Query decomposition,    (Policy, Evidence,
                   Parallel calls,          Enforcement, Assessment,
                   Result aggregation,     Compliance, Agent,
                   Field-level merging,     Audit, Risk, Framework,
                   Error handling,          Custom)
                   Caching, Rate Limiting,
                   Circuit Breaker)
```

### 5.2 Composition Patterns

**Pattern 1: Sequential Composition**
```
Client → Gateway → Service A → Service B → Service C → Aggregated Response
```
Used when: Service B needs data from Service A's response

**Pattern 2: Parallel Composition**
```
Client → Gateway ──┬──→ Service A ──┐
                   ├──→ Service B ──┼──→ Aggregated Response
                   └──→ Service C ──┘
```
Used when: Services are independent, maximum parallelism

**Pattern 3: Fan-Out with Aggregation**
```
Client → Gateway → Service A → [A1, A2, A3] → Aggregated Response
```
Used when: Service A returns a list, and each item needs enrichment

**Pattern 4: Cached Composition**
```
Client → Gateway → Cache (hit) → Response
                     ↓ (miss)
                Services → Cache (store) → Response
```
Used when: Data changes infrequently, high read volume

### 5.3 Composition API Endpoints

```
# Dashboard Overview — Aggregates data from 6 services
GET /v1/composed/dashboard
Response: {
  "compliance_summary": { ... },      # From Compliance Service
  "active_agents": { ... },            # From Agent Service
  "recent_enforcements": { ... },      # From Enforcement Service
  "open_findings": { ... },            # From Assessment Service
  "risk_alerts": { ... },              # From Risk Service
  "audit_stats": { ... }               # From Audit Service
}

# Agent 360° View — Aggregates all data for a single agent
GET /v1/composed/agents/{agent_id}/360
Response: {
  "agent": { ... },                    # From Agent Service
  "policies": { ... },                 # From Policy Service
  "enforcements": { ... },             # From Enforcement Service
  "evidence": { ... },                 # From Evidence Service
  "assessments": { ... },              # From Assessment Service
  "compliance": { ... },               # From Compliance Service
  "risks": { ... },                    # From Risk Service
  "audit_trail": { ... }               # From Audit Service
}

# Compliance Report — Aggregates compliance data across frameworks
GET /v1/composed/compliance-report
Response: {
  "frameworks": [ ... ],               # From Framework Service
  "posture": { ... },                  # From Compliance Service
  "evidence_summary": { ... },         # From Evidence Service
  "findings": { ... },                 # From Assessment Service
  "gaps": { ... },                     # From Compliance Service
  "trends": { ... }                    # From TimescaleDB
}

# Executive Summary — High-level aggregated view
GET /v1/composed/executive-summary
Response: {
  "overall_compliance_score": 0.87,
  "framework_scores": { ... },
  "risk_posture": { ... },
  "agent_governance": { ... },
  "recent_activity": { ... },
  "open_items": { ... }
}
```

### 5.4 Composition Engine Implementation

```java
@Component
public class DashboardCompositionEngine {
    
    private final ComplianceServiceClient complianceClient;
    private final AgentServiceClient agentClient;
    private final EnforcementServiceClient enforcementClient;
    private final AssessmentServiceClient assessmentClient;
    private final RiskServiceClient riskClient;
    private final AuditServiceClient auditClient;
    private final RedisTemplate<String, Object> redisTemplate;
    
    private static final String CACHE_KEY = "composed:dashboard";
    private static final Duration CACHE_TTL = Duration.ofSeconds(30);
    
    public DashboardOverview composeDashboard(String tenantId) {
        // Check cache first
        String cacheKey = CACHE_KEY + ":" + tenantId;
        DashboardOverview cached = (DashboardOverview) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }
        
        // Parallel service calls using CompletableFuture
        CompletableFuture<ComplianceSummary> complianceFuture = CompletableFuture
            .supplyAsync(() -> complianceClient.getSummary(tenantId))
            .exceptionally(ex -> PartialResult.unavailable("compliance", ex));
        
        CompletableFuture<AgentSummary> agentsFuture = CompletableFuture
            .supplyAsync(() -> agentClient.getActiveSummary(tenantId))
            .exceptionally(ex -> PartialResult.unavailable("agents", ex));
        
        CompletableFuture<EnforcementSummary> enforcementsFuture = CompletableFuture
            .supplyAsync(() -> enforcementClient.getRecentSummary(tenantId))
            .exceptionally(ex -> PartialResult.unavailable("enforcements", ex));
        
        CompletableFuture<FindingsSummary> findingsFuture = CompletableFuture
            .supplyAsync(() -> assessmentClient.getOpenFindingsSummary(tenantId))
            .exceptionally(ex -> PartialResult.unavailable("findings", ex));
        
        CompletableFuture<RiskSummary> risksFuture = CompletableFuture
            .supplyAsync(() -> riskClient.getActiveAlertsSummary(tenantId))
            .exceptionally(ex -> PartialResult.unavailable("risks", ex));
        
        CompletableFuture<AuditSummary> auditFuture = CompletableFuture
            .supplyAsync(() -> auditClient.getStats(tenantId))
            .exceptionally(ex -> PartialResult.unavailable("audit", ex));
        
        // Wait for all to complete
        CompletableFuture.allOf(
            complianceFuture, agentsFuture, enforcementsFuture,
            findingsFuture, risksFuture, auditFuture
        ).join();
        
        // Aggregate results
        DashboardOverview dashboard = DashboardOverview.builder()
            .compliance(complianceFuture.join())
            .agents(agentsFuture.join())
            .enforcements(enforcementsFuture.join())
            .findings(findingsFuture.join())
            .risks(risksFuture.join())
            .audit(auditFuture.join())
            .composedAt(Instant.now())
            .build();
        
        // Cache result
        redisTemplate.opsForValue().set(cacheKey, dashboard, CACHE_TTL);
        
        return dashboard;
    }
}
```

### 5.5 Partial Failure Handling

```java
public class PartialResult<T> {
    
    private final T data;
    private final boolean available;
    private final String error;
    private final String serviceName;
    
    public static <T> PartialResult<T> unavailable(String serviceName, Throwable ex) {
        return new PartialResult<>(null, false, ex.getMessage(), serviceName);
    }
    
    public static <T> PartialResult<T> available(T data) {
        return new PartialResult<>(data, true, null, null);
    }
}

// In composition engine:
public DashboardOverview composeDashboard(String tenantId) {
    // ... parallel calls with exceptionally() ...
    
    DashboardOverview dashboard = new DashboardOverview();
    
    // Check each result and include partial failure info
    if (complianceResult.isAvailable()) {
        dashboard.setCompliance(complianceResult.getData());
    } else {
        dashboard.setCompliance(ComplianceSummary.unavailable());
        dashboard.addPartialFailure("compliance", complianceResult.getError());
    }
    
    // ... repeat for other services ...
    
    return dashboard;
}
```

### 5.6 Composition Caching Strategy

```yaml
api_composition:
  caching:
    enabled: true
    store: redis
    
    # Cache TTLs by endpoint
    ttls:
      dashboard: 30s
      agent_360: 60s
      compliance_report: 300s
      executive_summary: 60s
    
    # Cache invalidation
    invalidation:
      strategy: event_driven
      events:
        - com.grcclaw.compliance.computed → invalidate dashboard, compliance_report
        - com.grcclaw.agent.registered → invalidate dashboard, agent_360
        - com.grcclaw.enforcement.decision → invalidate dashboard, agent_360
        - com.grcclaw.assessment.completed → invalidate dashboard, compliance_report
        - com.grcclaw.risk.detected → invalidate dashboard, executive_summary
    
    # Field-level caching
    field_cache:
      enabled: true
      fields:
        - path: "compliance_summary"
          ttl: 300s
        - path: "active_agents"
          ttl: 60s
        - path: "recent_enforcements"
          ttl: 10s
        - path: "open_findings"
          ttl: 120s
  
  resilience:
    timeout:
      default: 5s
      compliance: 10s
      enforcement: 3s
    
    circuit_breaker:
      failure_threshold: 5
      recovery_timeout: 30s
      half_open_max_calls: 3
    
    bulkhead:
      max_concurrent_calls: 100
      max_queue_size: 1000
    
    retry:
      max_attempts: 2
      backoff: exponential
      retry_on: [TimeoutException, ServiceUnavailableException]
```

### 5.7 GraphQL as Composition Layer

GraphQL serves as the primary composition layer for complex, nested queries:

```graphql
query ExecutiveDashboard($tenantId: ID!) {
  # Compliance posture across all frameworks
  compliancePosture(tenantId: $tenantId) {
    overallScore
    frameworks {
      id
      name
      score
      status
      trend { direction change period }
      gaps { controlId severity }
    }
  }
  
  # Agent governance summary
  agentGovernance(tenantId: $tenantId) {
    totalAgents
    activeAgents
    highRiskAgents
    agentsByRiskTier { tier count }
    recentEnforcements {
      total
      allowed
      denied
      requireApproval
    }
  }
  
  # Risk summary
  riskSummary(tenantId: $tenantId) {
    openRisks
    criticalRisks
    risksByCategory { category count }
    recentAlerts { id severity title createdAt }
  }
  
  # Assessment summary
  assessmentSummary(tenantId: $tenantId) {
    inProgress
    completed
    overdue
    findings { total open critical }
  }
  
  # Audit summary
  auditSummary(tenantId: $tenantId) {
    events24h
    integrityStatus
    lastVerified
  }
}
```

---

## 6. Enterprise Connectors

### 6.1 Integration Architecture

```
GRC_Claw Unified API (REST / gRPC / GraphQL / MCP)
         │
Integration Gateway (Auth Adapter, Rate Limiter, Request Router, Cache, Audit)
         │
Connector Framework
  ├── SIEM Connectors (Splunk, Elastic, Sentinel, QRadar, Chronicle, Datadog, Sumo Logic)
  ├── GRC Connectors (ServiceNow, Archer, OneTrust, MetricStream, SAP GRC)
  ├── MLOps Connectors (MLflow, W&B, Kubeflow, SageMaker, Vertex AI, Azure ML, DVC, Feast)
  ├── Cloud Connectors (AWS, Azure, GCP, Databricks, Snowflake)
  ├── IAM Connectors (Okta, Azure AD, Keycloak, Auth0, Ping Identity, AWS IAM)
  ├── Ticketing Connectors (Jira, ServiceNow, Linear, Asana, Monday.com)
  ├── Data Warehouse Connectors (Snowflake, BigQuery, Redshift, Databricks, ClickHouse)
  ├── SSO Connectors (SAML, OIDC, CAS)
  ├── Webhook Connectors (Inbound/Outbound)
  └── Custom Connectors (REST, GraphQL, gRPC)
```

### 6.2 SIEM Integration

#### Supported SIEM Platforms

| SIEM | Integration Method | Direction | Data |
|------|-------------------|-----------|------|
| Splunk | HEC (HTTP Event Collector) | Push | Audit events, alerts, violations |
| Elastic Security | Elasticsearch API | Push | Audit events, evidence metadata |
| Microsoft Sentinel | Log Analytics API | Push | Audit events, compliance posture |
| IBM QRadar | Syslog/LEEF | Push | Security events, violations |
| Google Chronicle | SecOps API | Push | Audit events, risk signals |
| Datadog | Events API | Push | Metrics, audit events |
| Sumo Logic | HTTP Collector | Push | Audit events, compliance data |

#### SIEM Event Mapping

```yaml
siem_integration:
  splunk:
    endpoint: ${SPLUNK_HEC_URL}
    token: ${SPLUNK_HEC_TOKEN}
    index: grcclaw
    sourcetype: grcclaw:audit
    batch_size: 100
    flush_interval: 5s
    
    event_mapping:
      enforcement_decision:
        sourcetype: grcclaw:enforcement
        fields:
          decision: "$.data.decision"
          agent_id: "$.data.agent_id"
          policy_id: "$.data.policy_id"
          reason: "$.data.reason"
          confidence: "$.data.confidence_score"
      
      policy_violation:
        sourcetype: grcclaw:violation
        fields:
          severity: "high"
          agent_id: "$.data.agent_id"
          policy_id: "$.data.policy_id"
          violation_type: "$.data.violation_type"
      
      compliance_change:
        sourcetype: grcclaw:compliance
        fields:
          framework: "$.data.framework"
          old_score: "$.data.old_score"
          new_score: "$.data.new_score"
          status: "$.data.status"
      
      risk_alert:
        sourcetype: grcclaw:risk
        fields:
          risk_tier: "$.data.risk_tier"
          risk_score: "$.data.risk_score"
          affected_assets: "$.data.affected_assets"
  
  elastic:
    endpoints: ["${ELASTIC_URL}"]
    api_key: ${ELASTIC_API_KEY}
    index_pattern: "grcclaw-*"
    ilm_policy: grcclaw_ilm
```

#### SIEM Alert Rules

```yaml
siem_alerts:
  - name: "GRC_Claw Critical Policy Violation"
    condition: |
      sourcetype=grcclaw:violation severity=critical
    threshold: 1
    window: 5m
    action: create_ticket
    ticket_system: servicenow
  
  - name: "GRC_Claw Compliance Score Drop"
    condition: |
      sourcetype=grcclaw:compliance new_score < 0.75
    threshold: 1
    window: 1h
    action: send_alert
    notification: pagerduty
  
  - name: "GRC_Claw Agent Quarantine"
    condition: |
      sourcetype=grcclaw:enforcement decision=QUARANTINE
    threshold: 1
    window: 1m
    action: create_ticket
    ticket_system: jira
  
  - name: "GRC_Claw Audit Trail Integrity Failure"
    condition: |
      sourcetype=grcclaw:audit event_type=integrity_failure
    threshold: 1
    window: 1m
    action: send_alert
    notification: slack
```

### 6.3 GRC Platform Integration

#### Supported GRC Platforms

| GRC Platform | Integration Method | Direction | Data |
|-------------|-------------------|-----------|------|
| ServiceNow GRC | REST API | Bidirectional | Controls, risks, findings, assessments |
| Archer | REST API | Bidirectional | Control assessments, risk registers |
| OneTrust | REST API | Bidirectional | Policies, controls, incidents |
| MetricStream | REST API | Push | Compliance data, risk scores |
| SAP GRC | RFC/BAPI | Push | Control status, risk posture |
| ServiceNow IRM | REST API | Bidirectional | Risk assessments, control mappings |
| Custom GRC | REST/GraphQL | Bidirectional | All entities |

#### GRC Data Synchronization

```yaml
grc_integration:
  servicenow:
    instance: ${SN_INSTANCE}
    auth:
      type: oauth2
      client_id: ${SN_CLIENT_ID}
      client_secret: ${SN_CLIENT_SECRET}
    
    sync:
      # GRC_Claw → ServiceNow
      outbound:
        - entity: Finding
          target: sn_grc_finding
          mapping:
            short_description: "$.title"
            description: "$.description"
            severity: "$.severity"
            state: "$.status"
            assigned_to: "$.remediation.assigned_to"
            due_date: "$.remediation.due_date"
          filter: "status != 'resolved'"
        
        - entity: Risk
          target: sn_grc_risk
          mapping:
            short_description: "$.title"
            description: "$.description"
            risk_score: "$.risk_score"
            risk_tier: "$.risk_tier"
        
        - entity: Compliance
          target: sn_grc_compliance
          mapping:
            framework: "$.framework.name"
            compliance_score: "$.compliance_score"
            status: "$.overall_status"
      
      # ServiceNow → GRC_Claw
      inbound:
        - entity: sn_grc_control
          target: Control
          mapping:
            control_id: "$.number"
            title: "$.short_description"
            description: "$.description"
        
        - entity: sn_grc_risk_register
          target: Risk
          mapping:
            risk_id: "$.number"
            title: "$.short_description"
            risk_score: "$.risk_score"
    
    schedule:
      outbound: "*/15 * * * *"  # Every 15 minutes
      inbound: "*/30 * * * *"  # Every 30 minutes
```

### 6.4 MLOps Integration

#### Supported MLOps Platforms

| MLOps Platform | Integration Method | Direction | Data |
|---------------|-------------------|-----------|------|
| MLflow | REST API | Bidirectional | Model metadata, versions, governance state |
| Weights & Biases | REST API | Bidirectional | Model tracking, evaluation results |
| Kubeflow | Kubernetes API | Bidirectional | Pipeline metadata, model artifacts |
| SageMaker | AWS API | Bidirectional | Model registry, deployment status |
| Vertex AI | GCP API | Bidirectional | Model registry, evaluation metrics |
| Azure ML | Azure API | Bidirectional | Model registry, deployment status |
| DVC | Git API | Bidirectional | Data versioning, lineage |
| Feast | REST API | Bidirectional | Feature store metadata |

#### MLOps Data Flow

```yaml
mlops_integration:
  mlflow:
    tracking_uri: ${MLFLOW_TRACKING_URI}
    registry_uri: ${MLFLOW_REGISTRY_URI}
    
    sync:
      # MLflow → GRC_Claw
      inbound:
        - entity: mlflow_model
          target: Agent
          mapping:
            name: "$.name"
            version: "$.version"
            stage: "$.stage"
            tags: "$.tags"
            governance_metadata: "$.tags.grc_claw_metadata"
        
        - entity: mlflow_metric
          target: Evidence
          mapping:
            control_id: "MLFLOW-MODEL-METRIC"
            framework: "CUSTOM"
            content: "$.value"
      
      # GRC_Claw → MLflow
      outbound:
        - entity: Policy
          target: mlflow_tag
          mapping:
            tag_key: "grc_claw_policy"
            tag_value: "$.id"
        
        - entity: Assessment
          target: mlflow_tag
          mapping:
            tag_key: "grc_claw_assessment"
            tag_value: "$.id"
    
    webhooks:
      - event: model_version_created
        action: trigger_assessment
      - event: model_stage_changed
        action: update_compliance
      - event: model_deleted
        action: archive_evidence
```

### 6.5 Cloud Platform Integration

#### AWS Integration

```yaml
aws_integration:
  region: ${AWS_REGION}
  auth:
    type: iam_role
    role_arn: ${AWS_ROLE_ARN}
  
  services:
    cloudtrail:
      trail_name: ${CLOUDTRAIL_NAME}
      s3_bucket: ${CLOUDTRAIL_S3_BUCKET}
      sns_topic: ${CLOUDTRAIL_SNS_TOPIC}
      
      sync:
        schedule: "*/5 * * * *"  # Every 5 minutes
        source: cloudtrail_events
        target: evidence_store
        mapping:
          event_name: "$.eventName"
          event_source: "$.eventSource"
          event_time: "$.eventTime"
          user_identity: "$.userIdentity"
          resources: "$.resources"
          management_event: "$.managementEvent"
    
    config:
      config_rule_names: ${CONFIG_RULE_NAMES}
      
      sync:
        schedule: "*/15 * * * *"  # Every 15 minutes
        source: config_compliance
        target: evidence_store
        mapping:
          config_rule_name: "$.configRuleName"
          compliance_type: "$.complianceType"
          resource_id: "$.resourceId"
          resource_type: "$.resourceType"
          ordering_timestamp: "$.orderingTimestamp"
    
    guardduty:
      detector_id: ${GUARDDUTY_DETECTOR_ID}
      
      sync:
        schedule: "*/1 * * * *"  # Every minute
        source: guardduty_findings
        target: evidence_store
        mapping:
          finding_id: "$.id"
          severity: "$.severity"
          type: "$.type"
          resource: "$.resource"
          created_at: "$.createdAt"
    
    security_hub:
      standards: ["CIS", "PCI DSS", "NIST"]
      
      sync:
        schedule: "0 * * * *"  # Every hour
        source: security_hub_findings
        target: evidence_store
        mapping:
          finding_id: "$.Id"
          severity: "$.Severity.Label"
          compliance: "$.Compliance"
          resources: "$.Resources"
    
    iam:
      sync:
        schedule: "0 0 * * *"  # Daily
        source: iam_policies
        target: evidence_store
        mapping:
          policy_name: "$.PolicyName"
          policy_document: "$.PolicyDocument"
          attachment_count: "$.AttachmentCount"
  
  eventbridge:
    rules:
      - name: grcclaw-cloudtrail-event
        event_source: aws.cloudtrail
        event_pattern:
          detail-type: ["AWS API Call via CloudTrail"]
        target: grcclaw-event-bus
      
      - name: grcclaw-config-change
        event_source: aws.config
        event_pattern:
          detail-type: ["Config Configuration Item Change"]
        target: grcclaw-event-bus
      
      - name: grcclaw-guardduty-finding
        event_source: aws.guardduty
        event_pattern:
          detail-type: ["GuardDuty Finding"]
        target: grcclaw-event-bus
```

### 6.6 IAM Integration

```yaml
iam_integration:
  okta:
    domain: ${OKTA_DOMAIN}
    api_token: ${OKTA_API_TOKEN}
    
    sync:
      inbound:
        - entity: okta_user
          target: User
          mapping:
            user_id: "$.id"
            email: "$.profile.email"
            display_name: "$.profile.displayName"
            status: "$.status"
            groups: "$.groups"
        
        - entity: okta_group
          target: Role
          mapping:
            group_id: "$.id"
            name: "$.profile.name"
            description: "$.profile.description"
      
      outbound:
        - entity: Agent
          target: okta_app_user
          mapping:
            username: "$.name"
            display_name: "$.name"
            metadata: "$.metadata"
    
    schedule:
      inbound: "*/15 * * * *"
      outbound: "*/30 * * * *"
  
  azure_ad:
    tenant_id: ${AZURE_TENANT_ID}
    client_id: ${AZURE_CLIENT_ID}
    client_secret: ${AZURE_CLIENT_SECRET}
    
    sync:
      inbound:
        - entity: azure_user
          target: User
          mapping:
            user_id: "$.id"
            email: "$.userPrincipalName"
            display_name: "$.displayName"
        
        - entity: azure_group
          target: Role
          mapping:
            group_id: "$.id"
            name: "$.displayName"
        
        - entity: azure_service_principal
          target: Agent
          mapping:
            sp_id: "$.id"
            name: "$.displayName"
            app_id: "$.appId"
      
      outbound:
        - entity: Agent
          target: azure_app_registration
          mapping:
            name: "$.name"
            metadata: "$.metadata"
```

### 6.7 Ticketing Integration

```yaml
ticketing_integration:
  jira:
    base_url: ${JIRA_URL}
    auth:
      type: basic
      username: ${JIRA_USERNAME}
      token: ${JIRA_API_TOKEN}
    project_key: ${JIRA_PROJECT_KEY}
    
    sync:
      outbound:
        - entity: Finding
          target: jira_issue
          mapping:
            summary: "$.title"
            description: "$.description"
            issue_type: "Task"
            priority: "$.severity"
            labels: ["grc-claw", "finding"]
            assignee: "$.remediation.assigned_to"
            due_date: "$.remediation.due_date"
        
        - entity: Exception
          target: jira_issue
          mapping:
            summary: "Exception: $.title"
            description: "$.description"
            issue_type: "Task"
            priority: "high"
            labels: ["grc-claw", "exception"]
        
        - entity: Risk
          target: jira_issue
          mapping:
            summary: "Risk: $.title"
            description: "$.description"
            issue_type: "Risk"
            priority: "$.risk_tier"
            labels: ["grc-claw", "risk"]
      
      inbound:
        - entity: jira_issue
          target: Finding
          mapping:
            title: "$.fields.summary"
            description: "$.fields.description"
            status: "$.fields.status.name"
            severity: "$.fields.priority.name"
    
    webhooks:
      - event: issue_updated
        action: sync_finding_status
      - event: issue_commented
        action: add_finding_comment
  
  servicenow:
    instance: ${SN_INSTANCE}
    auth:
      type: oauth2
      client_id: ${SN_CLIENT_ID}
      client_secret: ${SN_CLIENT_SECRET}
    
    sync:
      outbound:
        - entity: Finding
          target: sn_grc_finding
        - entity: Risk
          target: sn_grc_risk
        - entity: Exception
          target: sn_grc_exception
        - entity: Incident
          target: sn_incident
      
      inbound:
        - entity: sn_grc_finding
          target: Finding
        - entity: sn_grc_risk
          target: Risk
    
    webhooks:
      - event: incident_created
        action: create_finding
      - event: incident_resolved
        action: update_finding_status
```

### 6.8 Data Warehouse Integration

#### Warehouse Schema (Star Schema)

```sql
-- Dimension Tables
CREATE TABLE dim_organization (
    organization_id STRING PRIMARY KEY,
    name STRING,
    industry STRING,
    region STRING,
    created_at TIMESTAMP
);

CREATE TABLE dim_agent (
    agent_id STRING PRIMARY KEY,
    name STRING,
    type STRING,
    status STRING,
    owner_id STRING,
    owning_team STRING,
    business_unit STRING,
    trust_score FLOAT,
    registered_at TIMESTAMP
);

CREATE TABLE dim_policy (
    policy_id STRING PRIMARY KEY,
    name STRING,
    version STRING,
    status STRING,
    category STRING,
    owner_id STRING,
    effective_date TIMESTAMP,
    framework_mappings ARRAY<STRING>
);

CREATE TABLE dim_control (
    control_id STRING PRIMARY KEY,
    title STRING,
    family STRING,
    framework STRING,
    framework_control_id STRING
);

CREATE TABLE dim_framework (
    framework_id STRING PRIMARY KEY,
    name STRING,
    version STRING,
    type STRING
);

CREATE TABLE dim_time (
    time_id STRING PRIMARY KEY,
    timestamp TIMESTAMP,
    date DATE,
    hour INT,
    day_of_week INT,
    week INT,
    month INT,
    quarter INT,
    year INT
);

-- Fact Tables
CREATE TABLE fact_enforcement (
    enforcement_id STRING PRIMARY KEY,
    time_id STRING REFERENCES dim_time(time_id),
    agent_id STRING REFERENCES dim_agent(agent_id),
    policy_id STRING REFERENCES dim_policy(policy_id),
    decision STRING,
    confidence_score FLOAT,
    evaluation_latency_ms INT,
    total_latency_ms INT,
    environment STRING,
    risk_tier STRING
);

CREATE TABLE fact_evidence (
    evidence_id STRING PRIMARY KEY,
    time_id STRING REFERENCES dim_time(time_id),
    agent_id STRING REFERENCES dim_agent(agent_id),
    control_id STRING REFERENCES dim_control(control_id),
    framework_id STRING REFERENCES dim_framework(framework_id),
    evidence_type STRING,
    verification_level STRING,
    source_system STRING,
    environment STRING
);

CREATE TABLE fact_compliance (
    compliance_id STRING PRIMARY KEY,
    time_id STRING REFERENCES dim_time(time_id),
    organization_id STRING REFERENCES dim_organization(organization_id),
    framework_id STRING REFERENCES dim_framework(framework_id),
    control_id STRING REFERENCES dim_control(control_id),
    status STRING,
    score FLOAT,
    evidence_count INT,
    gap_count INT
);

CREATE TABLE fact_risk (
    risk_id STRING PRIMARY KEY,
    time_id STRING REFERENCES dim_time(time_id),
    organization_id STRING REFERENCES dim_organization(organization_id),
    agent_id STRING REFERENCES dim_agent(agent_id),
    risk_category STRING,
    risk_tier STRING,
    risk_score FLOAT,
    treatment STRING,
    residual_risk FLOAT
);

CREATE TABLE fact_finding (
    finding_id STRING PRIMARY KEY,
    time_id STRING REFERENCES dim_time(time_id),
    organization_id STRING REFERENCES dim_organization(organization_id),
    control_id STRING REFERENCES dim_control(control_id),
    severity STRING,
    status STRING,
    identified_at TIMESTAMP,
    resolved_at TIMESTAMP,
    sla_breach BOOLEAN
);

CREATE TABLE fact_audit (
    audit_id STRING PRIMARY KEY,
    time_id STRING REFERENCES dim_time(time_id),
    organization_id STRING REFERENCES dim_organization(organization_id),
    event_type STRING,
    actor_type STRING,
    actor_id STRING,
    resource_type STRING,
    resource_id STRING,
    integrity_hash STRING
);
```

### 6.9 MCP Integration

```yaml
mcp_server:
  name: grc-claw-governance
  version: "1.0.0"
  transport: stdio  # or http, websocket
  
  tools:
    - name: evaluate_action
      description: Evaluate an agent action against governance policies
      input_schema:
        type: object
        properties:
          action_type:
            type: string
            enum: [tool_call, api_request, data_access, code_execution]
          tool_name:
            type: string
          resource:
            type: string
          parameters:
            type: object
      output_schema:
        type: object
        properties:
          decision:
            type: string
            enum: [ALLOW, ALLOW_WITH_REDACTION, REQUIRE_APPROVAL, DENY, QUARANTINE]
          reason:
            type: string
          confidence_score:
            type: number
    
    - name: query_compliance
      description: Query compliance posture for a framework
      input_schema:
        type: object
        properties:
          framework:
            type: string
          scope_id:
            type: string
      output_schema:
        type: object
        properties:
          status:
            type: string
          score:
            type: number
          gaps:
            type: array
    
    - name: submit_evidence
      description: Submit compliance evidence
      input_schema:
        type: object
        properties:
          control_id:
            type: string
          framework:
            type: string
          content:
            type: string
          source:
            type: string
      output_schema:
        type: object
        properties:
          evidence_id:
            type: string
          verification_level:
            type: string
    
    - name: get_agent_policies
      description: Get policies applicable to an agent
      input_schema:
        type: object
        properties:
          agent_id:
            type: string
      output_schema:
        type: object
        properties:
          policies:
            type: array
    
    - name: report_finding
      description: Report a governance finding
      input_schema:
        type: object
        properties:
          title:
            type: string
          description:
            type: string
          severity:
            type: string
          control_id:
            type: string
      output_schema:
        type: object
        properties:
          finding_id:
            type: string
          status:
            type: string
    
    - name: get_audit_trail
      description: Query audit trail
      input_schema:
        type: object
        properties:
          entity_type:
            type: string
          entity_id:
            type: string
          start_time:
            type: string
          end_time:
            type: string
      output_schema:
        type: object
        properties:
          events:
            type: array
  
  resources:
    - uri: grcclaw://policies
      name: Active Policies
      description: List of active governance policies
    
    - uri: grcclaw://agents
      name: Registered Agents
      description: List of registered agents
    
    - uri: grcclaw://compliance
      name: Compliance Posture
      description: Current compliance posture by framework
    
    - uri: grcclaw://evidence
      name: Evidence Store
      description: Evidence store statistics
  
  prompts:
    - name: compliance_summary
      description: Generate a compliance summary for a framework
      arguments:
        - name: framework
          description: Framework name
          required: true
    
    - name: risk_assessment
      description: Generate a risk assessment for an agent
      arguments:
        - name: agent_id
          description: Agent ID
          required: true
```

---

## 7. Integration Testing

### 7.1 Architecture Overview

GRC_Claw includes a comprehensive integration testing framework that validates all API endpoints, event flows, and cross-service interactions.

```
Test Orchestrator
  ├── Test Suite Runner
  ├── Test Case Builder
  ├── Test Data Factory
  ├── Assert Engine
  └── Report Generator

Test Environment
  ├── Docker Compose Stack (API, PostgreSQL, Kafka, Redis, Elasticsearch, Mocks)
  └── Service Virtualization (WireMock, TestContainers, Mountebank)

Test Layers
  ├── Contract Tests (Pact, Schema Validation)
  ├── API Tests (REST, gRPC, GraphQL)
  ├── Event Tests (Kafka, Flink Stream)
  ├── E2E Tests (Full Flow, Saga)
  └── Chaos Tests (Failure Injection, Recovery)
```

### 7.2 Test Categories

| Category | Scope | Tools | Frequency |
|----------|-------|-------|-----------|
| **Contract Tests** | API schema validation, consumer-driven contracts | Pact, JSON Schema | Every commit |
| **API Tests** | REST, gRPC, GraphQL endpoint validation | pytest, grpcurl, GraphQL client | Every commit |
| **Event Tests** | Kafka event production, consumption, schema validation | Kafka test harness, Avro validator | Every commit |
| **Stream Tests** | Flink job validation, windowing, state management | Flink test harness | Every commit |
| **Integration Tests** | Cross-service flows, saga execution, CQRS projections | TestContainers, Docker Compose | Every PR |
| **E2E Tests** | Full user journeys, dashboard flows, approval workflows | Selenium, Cypress | Nightly |
| **Chaos Tests** | Failure injection, recovery validation | Chaos Monkey, Gremlin | Weekly |
| **Performance Tests** | Load, stress, endurance | k6, Locust, JMeter | Weekly |
| **Security Tests** | AuthN/AuthZ, input validation, injection | OWASP ZAP, custom fuzzers | Weekly |

### 7.3 Test Data Factory

```java
@Component
public class TestDataFactory {
    
    private final Faker faker = new Faker();
    private final String tenantId = "test-tenant-001";
    
    public Policy createTestPolicy() {
        return Policy.builder()
            .id(UUID.randomUUID().toString())
            .name(faker.lorem().words(3))
            .description(faker.lorem().paragraph())
            .category("data_handling")
            .status("draft")
            .version("1.0.0")
            .tenantId(tenantId)
            .cedarPolicy("permit(principal, action, resource) when { true }")
            .metadata(Map.of("test", "true"))
            .createdAt(Instant.now())
            .build();
    }
    
    public Evidence createTestEvidence(String policyId) {
        return Evidence.builder()
            .id(UUID.randomUUID().toString())
            .policyId(policyId)
            .type("artifact")
            .title(faker.lorem().sentence())
            .content(EvidenceContent.builder()
                .format("application/json")
                .data("{\"test\": true}")
                .hash("sha256:" + faker.crypto().sha256())
                .build())
            .source(EvidenceSource.builder()
                .system("test-system")
                .location("test://location")
                .collectorId("test-collector")
                .collectedAt(Instant.now())
                .build())
            .controlMappings(List.of(ControlMapping.builder()
                .controlId("AC-2")
                .framework("NIST-800-53")
                .controlTitle("Account Management")
                .build()))
            .verificationLevel("L0")
            .tenantId(tenantId)
            .build();
    }
    
    public EnforcementEvent createTestEnforcementEvent(String agentId, String policyId) {
        return EnforcementEvent.builder()
            .eventId(UUID.randomUUID().toString())
            .agentId(agentId)
            .policyId(policyId)
            .decision(faker.options().option("ALLOW", "DENY", "REQUIRE_APPROVAL"))
            .reason(faker.lorem().sentence())
            .confidenceScore(faker.number().randomDouble(2, 0, 1))
            .tenantId(tenantId)
            .timestamp(Instant.now())
            .traceId(UUID.randomUUID().toString())
            .build();
    }
    
    public Agent createTestAgent() {
        return Agent.builder()
            .id(UUID.randomUUID().toString())
            .name(faker.name().firstName() + " Agent")
            .type("autonomous")
            .status("active")
            .riskTier(faker.options().option("minimal", "limited", "high"))
            .tenantId(tenantId)
            .registeredAt(Instant.now())
            .build();
    }
    
    public SagaDefinition createTestSaga() {
        return SagaDefinition.builder()
            .name("test_saga")
            .steps(List.of(
                SagaStep.builder()
                    .id("step_1")
                    .service("test-service")
                    .action("test_action")
                    .timeout(Duration.ofSeconds(5))
                    .build()
            ))
            .build();
    }
}
```

### 7.4 Contract Tests (Pact)

```java
@PactTestFor(providerName = "grc-claw-policy-service")
public class PolicyServiceContractTest {
    
    @Pact(consumer = "grc-claw-enforcement-service")
    public RequestResponsePact policyByIdPact(PactDslWithProvider builder) {
        return builder
            .given("a policy exists with ID pol-001")
            .uponReceiving("a request for policy pol-001")
            .path("/v1/policies/pol-001")
            .method("GET")
            .willRespondWith()
            .status(200)
            .body(new PactDslJsonBody()
                .stringType("id", "pol-001")
                .stringType("name", "Test Policy")
                .stringType("status", "active")
                .stringType("version", "1.0.0")
                .stringType("category", "data_handling")
                .stringType("tenantId", "test-tenant-001")
            )
            .toPact();
    }
    
    @Test
    @PactTestFor(pactMethod = "policyByIdPact")
    void testGetPolicyById(MockServer mockServer) {
        PolicyServiceClient client = new PolicyServiceClient(mockServer.getUrl());
        Policy policy = client.getPolicy("pol-001");
        
        assertThat(policy.getId()).isEqualTo("pol-001");
        assertThat(policy.getStatus()).isEqualTo("active");
    }
}
```

### 7.5 Event Flow Tests

```java
@SpringBootTest
@Testcontainers
public class EventFlowIntegrationTest {
    
    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.5.0"));
    
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
        DockerImageName.parse("postgres:16"));
    
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;
    
    @Autowired
    private PolicyRepository policyRepository;
    
    @Test
    void testPolicyActivationEventFlow() {
        // 1. Create policy
        Policy policy = testDataFactory.createTestPolicy();
        policyRepository.save(policy);
        
        // 2. Activate policy
        policy.setStatus("active");
        policyRepository.save(policy);
        
        // 3. Publish event
        PolicyActivatedEvent event = new PolicyActivatedEvent(
            UUID.randomUUID().toString(),
            policy.getId(),
            1,
            policy.getTenantId(),
            Instant.now(),
            UUID.randomUUID(),
            null,
            "test-user",
            Instant.now()
        );
        
        kafkaTemplate.send("grcclaw.policy", event.getAggregateId(), 
            objectMapper.writeValueAsString(event));
        
        // 4. Wait for event processing
        await().atMost(Duration.ofSeconds(10))
            .untilAsserted(() -> {
                // 5. Verify event was consumed and processed
                List<PolicyEvent> events = policyEventRepository
                    .findByAggregateId(policy.getId());
                
                assertThat(events)
                    .extracting(PolicyEvent::getEventType)
                    .contains("PolicyActivated");
            });
        
        // 6. Verify read model was updated
        PolicyReadModel readModel = policyReadModelRepository
            .findById(policy.getId());
        assertThat(readModel.getStatus()).isEqualTo("active");
    }
    
    @Test
    void testEnforcementEventFlow() {
        // 1. Create agent and policy
        Agent agent = testDataFactory.createTestAgent();
        Policy policy = testDataFactory.createTestPolicy();
        policy.setStatus("active");
        
        // 2. Publish enforcement event
        EnforcementEvent event = testDataFactory
            .createTestEnforcementEvent(agent.getId(), policy.getId());
        
        kafkaTemplate.send("grcclaw.enforcement", event.getAgentId(),
            objectMapper.writeValueAsString(event));
        
        // 3. Verify event was consumed by multiple consumers
        await().atMost(Duration.ofSeconds(10))
            .untilAsserted(() -> {
                // SIEM connector received event
                List<EnforcementEvent> siemEvents = siemConnectorTest
                    .getReceivedEvents();
                assertThat(siemEvents).isNotEmpty();
                
                // Audit trail received event
                List<AuditEvent> auditEvents = auditTrailTest
                    .getReceivedEvents();
                assertThat(auditEvents).isNotEmpty();
                
                // Risk engine received event
                List<EnforcementEvent> riskEvents = riskEngineTest
                    .getReceivedEvents();
                assertThat(riskEvents).isNotEmpty();
            });
    }
}
```

### 7.6 Saga Tests

```java
@SpringBootTest
@Testcontainers
public class SagaIntegrationTest {
    
    @Autowired
    private SagaOrchestrator sagaOrchestrator;
    
    @Autowired
    private SagaStateRepository sagaStateRepository;
    
    @Test
    void testPolicyActivationSaga_Success() {
        // 1. Start saga
        Map<String, Object> input = Map.of("policy_id", "pol-test-001");
        SagaInstance instance = sagaOrchestrator.startSaga("policy_activation", input);
        
        // 2. Wait for completion
        await().atMost(Duration.ofSeconds(30))
            .untilAsserted(() -> {
                SagaInstance result = sagaStateRepository
                    .findById(instance.getSagaId());
                assertThat(result.getStatus()).isEqualTo(SagaStatus.COMPLETED);
            });
        
        // 3. Verify all steps completed
        SagaInstance result = sagaStateRepository.findById(instance.getSagaId());
        assertThat(result.getStepResults()).containsKeys(
            "validate_policy", "compile_policy", "distribute_rules",
            "update_status", "publish_event", "update_cache"
        );
    }
    
    @Test
    void testPolicyActivationSaga_Compensation() {
        // 1. Configure a step to fail
        mockServiceConfigurator.makeStepFail("distribute_rules");
        
        // 2. Start saga
        Map<String, Object> input = Map.of("policy_id", "pol-test-002");
        SagaInstance instance = sagaOrchestrator.startSaga("policy_activation", input);
        
        // 3. Wait for compensation
        await().atMost(Duration.ofSeconds(30))
            .untilAsserted(() -> {
                SagaInstance result = sagaStateRepository
                    .findById(instance.getSagaId());
                assertThat(result.getStatus()).isIn(
                    SagaStatus.COMPENSATED, SagaStatus.COMPENSATION_FAILED);
            });
        
        // 4. Verify compensation was executed
        SagaInstance result = sagaStateRepository.findById(instance.getSagaId());
        if (result.getStatus() == SagaStatus.COMPENSATED) {
            assertThat(result.getCompensatedSteps()).contains("compile_policy");
        }
    }
}
```

### 7.7 Chaos Tests

```java
@SpringBootTest
public class ChaosIntegrationTest {
    
    @Autowired
    private ChaosMonkey chaosMonkey;
    
    @Autowired
    private PolicyServiceClient policyClient;
    
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;
    
    @Test
    void testKafkaOutage_Recovery() {
        // 1. Verify normal operation
        Policy policy = policyClient.createPolicy(testDataFactory.createTestPolicy());
        assertThat(policy).isNotNull();
        
        // 2. Kill Kafka broker
        chaosMonkey.killKafkaBroker();
        
        // 3. Verify graceful degradation
        assertThatThrownBy(() -> policyClient.createPolicy(
            testDataFactory.createTestPolicy()))
            .isInstanceOf(ServiceUnavailableException.class);
        
        // 4. Verify circuit breaker is open
        CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("policy-service");
        assertThat(cb.getState()).isEqualTo(CircuitBreaker.State.OPEN);
        
        // 5. Restart Kafka
        chaosMonkey.restartKafkaBroker();
        
        // 6. Wait for recovery
        await().atMost(Duration.ofSeconds(60))
            .untilAsserted(() -> {
                CircuitBreaker cb2 = circuitBreakerRegistry
                    .circuitBreaker("policy-service");
                assertThat(cb2.getState()).isEqualTo(CircuitBreaker.State.CLOSED);
            });
        
        // 7. Verify operation resumes
        Policy policy2 = policyClient.createPolicy(
            testDataFactory.createTestPolicy());
        assertThat(policy2).isNotNull();
    }
    
    @Test
    void testDatabaseOutage_Failover() {
        // 1. Verify normal operation
        Policy policy = policyClient.createPolicy(testDataFactory.createTestPolicy());
        
        // 2. Kill primary database
        chaosMonkey.killPrimaryDatabase();
        
        // 3. Verify failover to replica
        await().atMost(Duration.ofSeconds(30))
            .untilAsserted(() -> {
                Policy result = policyClient.getPolicy(policy.getId());
                assertThat(result).isNotNull();
            });
        
        // 4. Verify new primary is elected
        await().atMost(Duration.ofSeconds(60))
            .untilAsserted(() -> {
                DatabaseStatus status = chaosMonkey.getDatabaseStatus();
                assertThat(status.getPrimary()).isNotEqualTo(status.getPreviousPrimary());
            });
    }
}
```

### 7.8 Test Configuration

```yaml
integration_test:
  environment:
    type: docker_compose
    compose_file: docker-compose.test.yml
    
    services:
      grc-claw-api:
        image: grc-claw-api:test
        ports: ["8080:8080"]
        environment:
          - ENV=test
          - DB_URL=jdbc:postgresql://postgres:5432/grcclaw_test
          - KAFKA_BOOTSTRAP=kafka:9092
          - REDIS_URL=redis:6379
      
      postgres:
        image: postgres:16
        environment:
          POSTGRES_DB: grcclaw_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
      
      kafka:
        image: confluentinc/cp-kafka:7.5.0
        ports: ["9092:9092"]
      
      redis:
        image: redis:7
        ports: ["6379:6379"]
      
      elasticsearch:
        image: elasticsearch:8.11.0
        ports: ["9200:9200"]
      
      wiremock:
        image: wiremock/wiremock:3.3.1
        ports: ["8081:8081"]
        volumes:
          - ./test/mocks:/home/wiremock
  
  test_data:
    seed: true
    seed_file: test-data/seed.sql
    cleanup_after: true
    
    factories:
      policies: 100
      agents: 50
      evidence: 500
      enforcements: 1000
      assessments: 20
  
  coverage:
    minimum: 80
    report_format: [html, json, xml]
    fail_below_minimum: true
  
  execution:
    parallel: true
    max_parallel: 4
    timeout: 300s
    retry_failed: true
    max_retries: 2
```

### 7.9 CI/CD Integration

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run contract tests
        run: make test-contract
      - name: Publish pacts
        run: make pact-publish

  api-tests:
    runs-on: ubuntu-latest
    needs: contract-tests
    steps:
      - uses: actions/checkout@v4
      - name: Start test environment
        run: docker compose -f docker-compose.test.yml up -d
      - name: Run API tests
        run: make test-api
      - name: Upload test report
        uses: actions/upload-artifact@v4
        with:
          name: api-test-report
          path: test-reports/

  event-tests:
    runs-on: ubuntu-latest
    needs: contract-tests
    steps:
      - uses: actions/checkout@v4
      - name: Start test environment
        run: docker compose -f docker-compose.test.yml up -d
      - name: Run event flow tests
        run: make test-events
      - name: Run stream processing tests
        run: make test-streams

  integration-tests:
    runs-on: ubuntu-latest
    needs: [api-tests, event-tests]
    steps:
      - uses: actions/checkout@v4
      - name: Start full test environment
        run: docker compose -f docker-compose.test.yml up -d
      - name: Run integration tests
        run: make test-integration
      - name: Run saga tests
        run: make test-saga
      - name: Run CQRS tests
        run: make test-cqrs

  chaos-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Run chaos tests
        run: make test-chaos
      - name: Run recovery tests
        run: make test-recovery

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Run load tests
        run: make test-performance
      - name: Run endurance tests
        run: make test-endurance
```

---

## Appendix: Quick Reference

### API Selection Guide

| Use Case | Recommended API | Rationale |
|----------|----------------|-----------|
| CRUD operations | REST | Simple, cacheable, widely supported |
| Real-time enforcement | gRPC streaming | Low latency, bidirectional, flow control |
| Complex queries | GraphQL | Flexible, reduces over-fetching, single request |
| Event-driven integration | gRPC streaming | Push-based, efficient, backpressure |
| Webhook callbacks | REST | Simple, fire-and-forget |
| Bulk data transfer | gRPC client streaming | Efficient, flow control, single connection |
| Dashboard/UI | GraphQL | Flexible queries, subscriptions for live updates |
| SIEM integration | gRPC streaming | High throughput, low latency |
| MLOps pipeline | REST | Simple, synchronous, easy to embed |
| Agent SDK | gRPC | Low latency, streaming, type-safe |

### Real-Time SLAs

| Operation | Latency (p50) | Latency (p99) | Throughput | Availability |
|-----------|---------------|---------------|------------|--------------|
| Enforcement decision | < 10ms | < 100ms | 10K req/s | 99.99% |
| Policy evaluation | < 5ms | < 50ms | 50K req/s | 99.99% |
| Evidence verification | < 20ms | < 200ms | 5K req/s | 99.9% |
| Compliance score | < 50ms | < 500ms | 1K req/s | 99.9% |
| Audit event write | < 5ms | < 50ms | 100K events/s | 99.99% |
| Agent attestation | < 50ms | < 500ms | 1K req/s | 99.9% |

### Circuit Breaker Configuration

```yaml
circuit_breakers:
  enforcement_engine:
    failure_threshold: 5
    recovery_timeout: 30s
    half_open_max_calls: 3
    on_failure: fail_open
  
  policy_engine:
    failure_threshold: 3
    recovery_timeout: 10s
    half_open_max_calls: 1
    on_failure: fail_open
  
  evidence_store:
    failure_threshold: 10
    recovery_timeout: 60s
    half_open_max_calls: 5
    on_failure: fail_closed
  
  audit_trail:
    failure_threshold: 3
    recovery_timeout: 10s
    half_open_max_calls: 1
    on_failure: fail_open  # Never block enforcement for audit failure
```

---

**End of Document**
