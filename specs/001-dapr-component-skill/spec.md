# Feature Specification: Dapr Component Configuration Skill

**Feature Branch**: `001-dapr-component-skill`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "Create a Dapr Component Skill that generates Dapr component configurations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Pub/Sub Component (Priority: P1)

A developer needs to configure Dapr pub/sub for event-driven communication between microservices. They provide the component type (pubsub), backend (Kafka/Redis), environment (local/staging/production), and namespace, and receive a ready-to-deploy Dapr component YAML with appropriate configuration for their environment.

**Why this priority**: Pub/Sub is the most common Dapr building block for microservices communication. This enables immediate value by allowing developers to establish event-driven architecture without manual YAML crafting.

**Independent Test**: Can be fully tested by generating a Kafka pubsub component YAML for production environment and validating it deploys successfully to Kubernetes, with services able to publish/subscribe to topics.

**Acceptance Scenarios**:

1. **Given** a request for Kafka pub/sub in production with namespace "default", **When** the skill generates the component, **Then** the YAML includes broker addresses, consumer group, authentication configuration, and proper scoping
2. **Given** a request for Redis pub/sub in local environment, **When** the skill generates the component, **Then** the YAML uses simplified configuration appropriate for local development
3. **Given** a generated pub/sub component, **When** deployed to Kubernetes, **Then** Dapr sidecars can successfully publish and subscribe to topics

---

### User Story 2 - Generate State Store Component (Priority: P2)

A developer needs persistent state management for their microservice. They specify the state store type (PostgreSQL/Redis), environment, and namespace, and receive a Dapr state store component YAML with connection configuration using Kubernetes secrets.

**Why this priority**: State management is essential for stateful microservices but less universally needed than pub/sub. This provides immediate value for services requiring data persistence without directly managing databases.

**Independent Test**: Can be tested by generating a PostgreSQL state store component, deploying it to Kubernetes, and verifying a service can save/retrieve state using Dapr SDK.

**Acceptance Scenarios**:

1. **Given** a request for PostgreSQL state store, **When** the skill generates the component, **Then** the YAML includes secretKeyRef for connection string and configured table name
2. **Given** a generated state store component, **When** a service uses Dapr SDK to save state, **Then** data persists correctly in the specified backend
3. **Given** different environments (local/production), **When** components are generated, **Then** configuration reflects appropriate settings (e.g., connection pooling for production)

---

### User Story 3 - Generate Secrets Component (Priority: P2)

A developer needs to manage application secrets securely through Dapr. They specify the secret store type (Kubernetes secrets/Azure Key Vault) and environment, and receive a Dapr secret store component YAML that enables secure secret retrieval.

**Why this priority**: Secret management is critical for security but typically configured once per environment. This enables secure configuration management across all services.

**Independent Test**: Can be tested by generating a Kubernetes secrets component, deploying it, and verifying services can retrieve secrets using Dapr SDK without direct Kubernetes API access.

**Acceptance Scenarios**:

1. **Given** a request for Kubernetes secret store, **When** the skill generates the component, **Then** the YAML correctly configures the secretstores.kubernetes type
2. **Given** production environment, **When** generating secret store, **Then** configuration includes Azure Key Vault integration instead of Kubernetes secrets
3. **Given** a deployed secret store component, **When** a service requests a secret, **Then** Dapr retrieves and provides the secret securely

---

### User Story 4 - Generate Bindings Component (Priority: P3)

A developer needs to schedule recurring tasks using cron bindings. They specify the binding type (cron), schedule expression, and target service, and receive a Dapr binding component YAML that triggers the service on schedule.

**Why this priority**: Bindings enable external system integration and scheduled tasks but are less commonly needed than core communication patterns. Provides value for batch processing and scheduled operations.

**Independent Test**: Can be tested by generating a cron binding with a 1-minute schedule, deploying it, and verifying the target service receives trigger events at the expected interval.

**Acceptance Scenarios**:

1. **Given** a cron schedule "*/5 * * * *", **When** the skill generates the binding, **Then** the YAML includes correct schedule metadata
2. **Given** a deployed cron binding, **When** the schedule triggers, **Then** the target service receives the binding event
3. **Given** different schedule expressions, **When** components are generated, **Then** schedules are correctly validated and configured

---

### User Story 5 - Generate Configuration Component with Tracing (Priority: P3)

A developer needs to enable distributed tracing across their microservices. They specify the tracing backend (Zipkin/Jaeger) endpoint and sampling rate, and receive a Dapr configuration YAML that enables observability.

**Why this priority**: Observability configuration is essential for production but typically set up once per cluster. Provides value for debugging and monitoring distributed systems.

**Independent Test**: Can be tested by generating a configuration with Zipkin tracing, deploying it, and verifying traces appear in the tracing backend when services communicate.

**Acceptance Scenarios**:

1. **Given** a Jaeger endpoint and 100% sampling rate, **When** the skill generates configuration, **Then** the YAML includes correct tracing configuration
2. **Given** different environments, **When** configurations are generated, **Then** sampling rates reflect environment-appropriate values (100% local, 50% staging, 10% production)
3. **Given** a deployed tracing configuration, **When** services make Dapr calls, **Then** distributed traces are captured in the tracing backend

---

### User Story 6 - Generate Python SDK Integration Code (Priority: P2)

A developer has deployed Dapr components and needs to integrate them into their Python application. They receive ready-to-use Python code snippets showing how to publish events, subscribe to topics, save state, and retrieve secrets using the Dapr SDK.

**Why this priority**: SDK integration code accelerates development by providing working examples. This reduces the learning curve for developers new to Dapr.

**Independent Test**: Can be tested by copying the generated Python code, integrating it into a FastAPI service, and verifying pub/sub, state, and secrets operations work correctly.

**Acceptance Scenarios**:

1. **Given** a request for pub/sub integration code, **When** the skill generates the code, **Then** it includes proper imports, client initialization, and error handling
2. **Given** generated subscriber code, **When** integrated into a FastAPI app, **Then** the service correctly receives and processes published events
3. **Given** generated state management code, **When** used in a service, **Then** state operations (save/get/delete) work correctly with the configured state store

---

### User Story 7 - Update Deployment with Dapr Annotations (Priority: P1)

A developer has a Kubernetes deployment and needs to enable Dapr for their service. They receive updated deployment YAML with proper Dapr annotations (enabled, app-id, app-port, log-level) that enable sidecar injection.

**Why this priority**: Deployment annotations are required for any service to use Dapr. This is a critical enabling step that must be correct for Dapr to function.

**Independent Test**: Can be tested by applying the annotated deployment YAML and verifying the Dapr sidecar is injected and the service can use Dapr components.

**Acceptance Scenarios**:

1. **Given** an existing deployment YAML, **When** Dapr annotations are added, **Then** the deployment includes dapr.io/enabled, dapr.io/app-id, and dapr.io/app-port
2. **Given** an annotated deployment, **When** applied to Kubernetes, **Then** Dapr automatically injects the sidecar container
3. **Given** different service ports, **When** annotations are generated, **Then** app-port reflects the correct service port

---

### Edge Cases

- What happens when an invalid component type is requested (not pubsub/statestore/secretstore/binding/configuration)?
- How does the system handle environment-specific configuration differences (e.g., local vs production secret stores)?
- What happens when required parameters (namespace, backend, environment) are missing?
- How does the system handle different Dapr component versions (v1 vs v2)?
- What happens when generated YAML has invalid syntax or missing required fields?
- How does the system handle backend-specific configuration variations (Kafka vs Redis for pub/sub)?
- What happens when tracing sampling rates are outside valid range (0-1)?
- How does the system validate cron schedule expressions?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate Dapr pub/sub component YAML for Kafka and Redis backends
- **FR-002**: System MUST generate Dapr state store component YAML for PostgreSQL and Redis backends
- **FR-003**: System MUST generate Dapr secret store component YAML for Kubernetes secrets
- **FR-004**: System MUST generate Dapr bindings component YAML for cron schedules
- **FR-005**: System MUST generate Dapr configuration YAML with tracing (Zipkin/Jaeger) and metrics
- **FR-006**: System MUST provide Python SDK code snippets for publishing events
- **FR-007**: System MUST provide Python SDK code snippets for subscribing to topics using FastAPI DaprApp
- **FR-008**: System MUST provide Python SDK code snippets for state management (save/get/delete)
- **FR-009**: System MUST provide Python SDK code snippets for secret retrieval
- **FR-010**: System MUST generate Kubernetes deployment annotations for Dapr sidecar injection
- **FR-011**: System MUST adjust configuration based on environment (local/staging/production)
- **FR-012**: System MUST include authentication configuration for Kafka pub/sub (authType)
- **FR-013**: System MUST configure secret references for sensitive data (connection strings)
- **FR-014**: System MUST include component scoping (app-id restrictions)
- **FR-015**: System MUST validate required parameters (component type, backend, environment, namespace)
- **FR-016**: System MUST adjust tracing sampling rates based on environment (100% local, 50% staging, 10% production)
- **FR-017**: System MUST validate cron schedule expressions for binding components
- **FR-018**: System MUST provide environment-specific secret store selection (Kubernetes for staging, Azure Key Vault for production)
- **FR-019**: System MUST generate component metadata with broker addresses for Kafka pub/sub
- **FR-020**: System MUST include consumer group configuration for pub/sub components

### Key Entities

- **Dapr Component**: Represents a Dapr building block configuration (pubsub, statestore, secretstore, binding, configuration) with metadata, spec type, version, and component-specific metadata fields
- **Environment Configuration**: Represents environment-specific settings (local/staging/production) affecting component configuration, tracing sampling rates, and secret store selection
- **Component Backend**: Represents the underlying infrastructure (Kafka, Redis, PostgreSQL, Azure Key Vault) with backend-specific configuration requirements
- **SDK Integration**: Represents Python code patterns for interacting with Dapr components through the Dapr Python SDK
- **Deployment Annotation**: Represents Kubernetes deployment metadata required for Dapr sidecar injection

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can generate production-ready Dapr component YAMLs in under 1 minute
- **SC-002**: Generated components deploy successfully to Kubernetes without YAML syntax errors
- **SC-003**: Services using generated SDK code can successfully publish/subscribe to events within first attempt
- **SC-004**: Generated components work correctly across all supported environments (local/staging/production) without manual modification
- **SC-005**: 100% of generated components pass Kubernetes YAML validation (kubectl apply --dry-run)
- **SC-006**: Developers can enable Dapr for existing services by adding generated annotations in under 30 seconds
- **SC-007**: Generated Python SDK code snippets execute without import or syntax errors
- **SC-008**: Tracing configurations result in traces appearing in configured backends for 100% of service invocations
- **SC-009**: State operations using generated code successfully persist and retrieve data in 100% of test cases
- **SC-010**: Generated components reduce manual Dapr configuration time by 80% compared to reading documentation and writing YAML from scratch

## Assumptions

- Kubernetes cluster is already running with Dapr control plane installed
- Developers have kubectl access to the target namespace
- Backend infrastructure (Kafka, Redis, PostgreSQL) is already deployed and accessible
- Tracing backends (Jaeger/Zipkin) are deployed for observability configurations
- Python applications use FastAPI framework for pub/sub subscription examples
- Dapr version v1 components are standard (not v2 alpha features)
- Default table name "dapr_state" is acceptable for state stores
- Kubernetes secrets are the default secret store for local/staging, Azure Key Vault for production
- Cron binding schedules follow standard cron expression format
- Component scoping limits components to single app-id unless otherwise specified

## Out of Scope

- Deploying Dapr control plane to Kubernetes clusters
- Provisioning backend infrastructure (Kafka brokers, Redis clusters, databases)
- Setting up Kubernetes secrets or Azure Key Vault with actual secret values
- Configuring Dapr middleware (rate limiting, OAuth)
- Implementing Dapr workflows or actors
- Generating code for languages other than Python
- Configuring Dapr service invocation policies or retry policies
- Setting up Dapr observability backends (Prometheus, Grafana, Jaeger)
- Implementing Dapr input/output bindings beyond cron (e.g., HTTP, Kafka bindings)
- Configuring Dapr resiliency policies
- Implementing Dapr distributed lock
