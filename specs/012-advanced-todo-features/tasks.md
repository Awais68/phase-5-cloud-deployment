# Tasks: Advanced Todo Features

**Input**: Design documents from `/specs/012-advanced-todo-features/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Feature**: Advanced time management features including due dates with natural language parsing and browser notifications, recurring tasks with automatic rescheduling, task history with audit trail and restoration, event-driven architecture with Kafka, multiple microservices (notification, recurring task, audit log), Dapr integration, Helm charts, observability stack, cloud deployment (GKE/AKS/OKE), and CI/CD automation.

**Organization**: Tasks are grouped by feature area (Groups A-L) as requested, with user story labels for traceability.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1=Due Dates, US2=Recurring Tasks, US3=History Tab)
- Include exact file paths in descriptions

## Path Conventions

This is a web application with:
- Backend: `backend/src/`
- Frontend: `frontend/src/`
- Infrastructure: `kubernetes/`, `helm-charts/`
- Database migrations: `backend/src/database/migrations/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [ ] T001 Update backend/pyproject.toml with new dependencies: dateparser>=1.3.0, parsedatetime>=2.6, apscheduler>=3.10.0, pytz>=2024.1, aiokafka>=0.8.0, dapr>=1.10.0
- [ ] T002 [P] Update frontend/package.json with new dependencies: react-datepicker, date-fns for timezone formatting
- [ ] T003 [P] Create backend/src/utils/__init__.py directory for utilities
- [ ] T004 [P] Update backend/.env.example with scheduler config (DATABASE_URL, SCHEDULER_ENABLED=true)
- [ ] T005 [P] Update frontend public/ directory for service worker registration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Migrations (Sequential)

- [ ] T006 Create migration backend/src/database/migrations/001_extend_tasks.sql (add due_date, recurrence_pattern, is_recurring, reminder_minutes, next_occurrence columns to tasks table)
- [ ] T007 Create migration backend/src/database/migrations/002_task_history.sql (create task_history table with indexes)
- [ ] T008 Create migration backend/src/database/migrations/003_notif_prefs.sql (create notification_preferences table)
- [ ] T009 Create migration backend/src/database/migrations/004_apscheduler.sql (create apscheduler_jobs table for job persistence)
- [ ] T010 Create migration backend/src/database/migrations/005_kafka_topics.sql (metadata for Kafka topics if using database for topic management)

### Core Models (Parallel after migrations)

- [ ] T011 [P] Update backend/src/models/task.py to extend Task model with new fields (due_date, recurrence_pattern, is_recurring, reminder_minutes, next_occurrence) including validation methods
- [ ] T012 [P] Create backend/src/models/task_history.py for TaskHistory model with immutability constraints
- [ ] T013 [P] Create backend/src/models/notification_preference.py for NotificationPreference model with validation

### Core Utilities (Parallel after models)

- [ ] T014 [P] Create backend/src/utils/datetime_parser.py with DateTimeParser class (dual library: dateparser + parsedatetime) with 21 test cases from research.md
- [ ] T015 [P] Create backend/src/utils/recurrence_calculator.py with RecurrenceCalculator class for next occurrence calculation (5 patterns)

### Core Services (Sequential dependencies)

- [ ] T016 Create backend/src/services/scheduler_service.py with SchedulerService class (APScheduler with PostgreSQL jobstore, notification scheduling, recurring task scheduling, history cleanup scheduling)
- [ ] T017 [P] Create backend/src/services/history_service.py with HistoryService class for CRUD operations on TaskHistory
- [ ] T018 Update backend/src/services/task_service.py to add due date handling, recurrence logic, history creation on completion/deletion

### Backend Integration

- [ ] T019 Update backend/src/main.py to initialize SchedulerService on FastAPI startup and schedule daily history cleanup job
- [ ] T020 [P] Update backend/src/config/settings.py to add environment variables for scheduler, Kafka, and notification config

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Group A: Advanced Features (Due Dates, Recurring Tasks, Priorities, Tags, Search, Filter, Sort)

### Phase 3: User Story 1 - Due Dates & Reminders (Priority: P1) 🎯 MVP

**Goal**: Users can set due dates with natural language parsing and receive browser notifications for task deadlines

**Independent Test**: Create task "buy groceries tomorrow at 3pm", verify due date is set, confirm notification appears 15 minutes before and at due time

#### Backend API for Due Dates (US1)

- [ ] T021 [P] [US1] Update backend/src/api/chat.py to accept due_date_text parameter in task creation, parse with DateTimeParser, store UTC timestamp
- [ ] T022 [P] [US1] Create backend/src/api/tasks.py with GET /tasks/by-due-date endpoint (filter: overdue, due-today, due-this-week, upcoming)
- [ ] T023 [US1] Update backend/src/services/task_service.py to schedule notification when task with due_date is created (via SchedulerService)

#### Frontend UI for Due Dates (US1)

- [ ] T024 [P] [US1] Create frontend/src/components/DateTimePicker.tsx component with date/time selection UI (use react-datepicker)
- [ ] T025 [P] [US1] Update frontend/src/components/ChatInterface.tsx to support natural language due date input and display parsed date confirmation
- [ ] T026 [US1] Update frontend/src/components/TaskList.tsx to display due date indicators (red=overdue, yellow=due today, blue=upcoming)
- [ ] T027 [P] [US1] Create frontend/src/utils/dateUtils.ts for timezone display formatting (UTC to browser local)

#### Browser Notifications (US1)

- [ ] T028 [P] [US1] Create frontend/src/hooks/useNotifications.ts with notification permission request, scheduling logic (setTimeout <1hr, service worker >1hr)
- [ ] T029 [US1] Create frontend/public/service-worker.js for background notifications when tab is closed
- [ ] T030 [P] [US1] Update frontend/src/types/task.ts to include new Task fields (due_date, reminder_minutes, recurrence_pattern)

**Checkpoint**: User Story 1 (Due Dates & Reminders) fully functional and testable independently

---

### Phase 4: User Story 2 - Recurring Tasks (Priority: P2)

**Goal**: Users can create tasks that auto-reschedule on completion with standard patterns (daily, weekly, monthly, yearly)

**Independent Test**: Create task "weekly standup every Monday at 9am", complete it, verify new task is created for next Monday at 9am

#### Backend Recurring Logic (US2)

- [ ] T031 [P] [US2] Update backend/src/services/task_service.py to detect recurring task completion, calculate next_occurrence using RecurrenceCalculator, create new task instance
- [ ] T032 [US2] Create backend/src/api/tasks.py POST /tasks/{id}/stop-recurrence endpoint to convert recurring task to one-time task
- [ ] T033 [US2] Update backend/src/services/scheduler_service.py to cancel scheduled notifications when recurring task is deleted

#### Frontend Recurring UI (US2)

- [ ] T034 [P] [US2] Update frontend/src/components/ChatInterface.tsx to parse recurrence patterns from natural language ("weekly meeting", "monthly report")
- [ ] T035 [P] [US2] Update frontend/src/components/TaskList.tsx to display recurrence indicators (icon + pattern text: "Repeats: Weekly on Monday")
- [ ] T036 [US2] Create frontend/src/components/RecurrenceEditor.tsx component for modifying recurrence patterns (pattern type, frequency, end date)

#### Priorities, Tags, Search, Filter, Sort Extensions

- [ ] T037 [P] Add priority field (high/medium/low) to Task model in backend/src/models/task.py
- [ ] T038 [P] Add tags array field to Task model in backend/src/models/task.py with many-to-many relationship
- [ ] T039 [P] Create backend/src/api/tasks.py GET /tasks/search endpoint with query parameters for title search, filters (priority, tags, due date range), sorting (due_date, created_at, priority)
- [ ] T040 [P] Create frontend/src/components/TaskFilters.tsx component for search, filter, and sort controls
- [ ] T041 Create database migration backend/src/database/migrations/006_priority_tags.sql to add priority column and tags table with junction table

**Checkpoint**: User Story 2 (Recurring Tasks) fully functional, priorities/tags/search/filter/sort operational

---

### Phase 5: User Story 3 - History Tab (Priority: P3)

**Goal**: Users can view completed/deleted tasks for 2 years with search, filter, and restore capability

**Independent Test**: Complete 5 tasks, delete 3 tasks, navigate to History tab, verify all 8 actions displayed with correct metadata, restore one deleted task

#### Backend History API (US3)

- [ ] T042 [P] [US3] Create backend/src/api/history.py with GET /users/{user_id}/history endpoint (pagination 50 per page, filters: completed/deleted/all, date range)
- [ ] T043 [P] [US3] Create backend/src/api/history.py with POST /users/{user_id}/history/{history_id}/restore endpoint to restore deleted tasks
- [ ] T044 [US3] Update backend/src/services/history_service.py to implement full-text search on task_history.title using PostgreSQL GIN index

#### Frontend History UI (US3)

- [ ] T045 [P] [US3] Create frontend/src/components/HistoryTab.tsx component with pagination, search bar, filter controls (status, date range)
- [ ] T046 [P] [US3] Create frontend/src/hooks/useTaskHistory.ts for fetching history data with filters and pagination state management
- [ ] T047 [P] [US3] Create frontend/src/services/history.ts API client for history endpoints
- [ ] T048 [US3] Update frontend/src/App.tsx to add History tab route and navigation link
- [ ] T049 [P] [US3] Create frontend/src/types/history.ts for TaskHistory type definitions

**Checkpoint**: All three user stories (US1, US2, US3) independently functional

---

## Group B: Event Architecture (Kafka Setup, Topics, Producers, Consumers)

**Purpose**: Event-driven architecture for task lifecycle events, reminder scheduling, and real-time sync

### Kafka Infrastructure

- [ ] T050 [P] Install and configure Kafka broker locally (or use Strimzi operator for Kubernetes) with 3 topics: task-events, scheduled-reminders, task-sync
- [ ] T051 Create backend/src/services/kafka_producer.py with event publishing for task creation, update, completion, deletion (publish to task-events topic)
- [ ] T052 [P] Create backend/src/services/kafka_consumer.py base class with consumer group management, error handling, and offset commit logic

### Event Producers

- [ ] T053 [P] Update backend/src/services/task_service.py to publish task-created, task-updated, task-completed, task-deleted events to task-events topic
- [ ] T054 [P] Create backend/src/services/reminder_producer.py to publish scheduled-reminder events when due_date is set or updated
- [ ] T055 Update backend/src/api/tasks.py endpoints to trigger event publishing after successful operations

### Event Consumers (will be implemented in Group C, D, E)

- [ ] T056 [P] Create backend/src/config/kafka_config.py with Kafka broker URLs, topic names, consumer group IDs, serialization config (JSON/Avro)

**Checkpoint**: Kafka infrastructure operational, producers publishing events

---

## Group C: Notification Service (8 tasks)

**Purpose**: Microservice for consuming reminder events and sending multi-channel notifications (email, push, WebSocket)

### Notification Service Structure

- [ ] T057 Create backend/src/services/notification_service/main.py FastAPI application for notification microservice
- [ ] T058 [P] Create backend/src/services/notification_service/kafka_consumer.py to consume scheduled-reminders topic
- [ ] T059 Create backend/src/services/notification_service/notification_handler.py with multi-channel dispatch (email via SMTP, push via Firebase Cloud Messaging, WebSocket for real-time)
- [ ] T060 [P] Create backend/src/services/notification_service/models.py for NotificationLog (track delivery status, retry attempts)

### Notification Channels

- [ ] T061 [P] Create backend/src/services/notification_service/channels/email_channel.py with SMTP integration for email reminders
- [ ] T062 [P] Create backend/src/services/notification_service/channels/push_channel.py with Firebase Cloud Messaging for mobile push notifications
- [ ] T063 [P] Create backend/src/services/notification_service/channels/websocket_channel.py for real-time browser notifications

### Rate Limiting & Preferences

- [ ] T064 Create backend/src/services/notification_service/rate_limiter.py to prevent notification spam (max 10 per user per hour)

**Checkpoint**: Notification service consuming events and sending multi-channel notifications

---

## Group D: Recurring Task Service (7 tasks)

**Purpose**: Microservice for handling automatic creation of recurring task instances on completion

### Recurring Task Service Structure

- [ ] T065 Create backend/src/services/recurring_task_service/main.py FastAPI application for recurring task microservice
- [ ] T066 [P] Create backend/src/services/recurring_task_service/kafka_consumer.py to consume task-events topic (filter action_type=completed where is_recurring=true)
- [ ] T067 Create backend/src/services/recurring_task_service/recurrence_handler.py with logic to create next task instance using RecurrenceCalculator
- [ ] T068 [P] Create backend/src/services/recurring_task_service/models.py for RecurrenceLog (track instance creation, skipped occurrences)

### Recurrence Patterns & Edge Cases

- [ ] T069 [P] Create backend/src/services/recurring_task_service/pattern_calculator.py with edge case handling (Feb 31→Feb 28/29, DST transitions)
- [ ] T070 Create backend/src/services/recurring_task_service/api.py with POST /skip-occurrence and POST /stop-recurrence endpoints
- [ ] T071 Update backend/src/services/recurring_task_service/recurrence_handler.py to handle user timezone conversions and validate recurrence end dates

**Checkpoint**: Recurring task service automatically creating next instances on completion

---

## Group E: Audit Log Service (8 tasks)

**Purpose**: Immutable audit trail consuming task-events for compliance and forensics

### Audit Log Service Structure

- [ ] T072 Create backend/src/services/audit_log_service/main.py FastAPI application with TimescaleDB connection
- [ ] T073 [P] Create backend/src/services/audit_log_service/kafka_consumer.py to consume task-events topic with idempotency (deduplicate by event_id)
- [ ] T074 Create backend/src/services/audit_log_service/models.py for AuditLog hypertable (partitioned by timestamp for time-series optimization)
- [ ] T075 [P] Create database migration for TimescaleDB hypertable: backend/src/database/migrations/007_audit_log_hypertable.sql

### Audit Queries & Retention

- [ ] T076 [P] Create backend/src/services/audit_log_service/api.py with GET /audit-logs endpoint (filters: user_id, action_type, date range, pagination)
- [ ] T077 Create backend/src/services/audit_log_service/retention_policy.py with automatic archival to cold storage after 90 days, deletion after 2 years
- [ ] T078 [P] Create backend/src/services/audit_log_service/compliance_reporter.py with monthly compliance report generation (all task deletions, user activity summary)
- [ ] T079 Create backend/src/services/audit_log_service/search.py with full-text search on audit log entries using PostgreSQL GIN indexes

**Checkpoint**: Audit log service capturing all task events with compliance reporting

---

## Group F: Dapr Integration (8 tasks)

**Purpose**: Replace direct Kafka/service calls with Dapr building blocks for resilience and observability

### Dapr Pub/Sub Integration

- [ ] T080 Install Dapr CLI and initialize Dapr locally with dapr init (creates Redis for state store, placement service)
- [ ] T081 [P] Create kubernetes/dapr-components/pubsub.yaml for Kafka pub/sub component configuration
- [ ] T082 Update backend/src/services/kafka_producer.py to use Dapr pub/sub API instead of direct Kafka client (publish via HTTP POST to localhost:3500/v1.0/publish)
- [ ] T083 Update notification service backend/src/services/notification_service/kafka_consumer.py to subscribe via Dapr pub/sub (configure subscription in app code)

### Dapr Service Invocation

- [ ] T084 [P] Create kubernetes/dapr-components/service-invocation.yaml for mTLS service-to-service communication
- [ ] T085 Update backend/src/services/task_service.py to invoke notification service via Dapr service invocation API (POST localhost:3500/v1.0/invoke/notification-service/method/send)
- [ ] T086 Update recurring task service to invoke task service via Dapr service invocation for creating next instances

### Dapr State Management

- [ ] T087 Create kubernetes/dapr-components/statestore.yaml for Redis state store configuration (cache notification preferences, recurring task metadata)

**Checkpoint**: Services using Dapr for pub/sub, service invocation, and state management

---

## Group G: Helm Charts (9 tasks)

**Purpose**: Package Kubernetes deployments with Helm for multi-environment deployment

### Helm Chart Structure

- [ ] T088 Create helm-charts/todo-app/Chart.yaml with chart metadata (version, appVersion, dependencies)
- [ ] T089 [P] Create helm-charts/todo-app/values.yaml with default values (image tags, replica counts, resource limits, environment variables)
- [ ] T090 [P] Create helm-charts/todo-app/values-dev.yaml for development environment overrides (lower resources, debug logging)
- [ ] T091 [P] Create helm-charts/todo-app/values-prod.yaml for production environment overrides (high availability, autoscaling, monitoring)

### Helm Templates for Services

- [ ] T092 [P] Create helm-charts/todo-app/templates/backend-deployment.yaml for main backend service with liveness/readiness probes
- [ ] T093 [P] Create helm-charts/todo-app/templates/notification-service-deployment.yaml with Kafka consumer configuration
- [ ] T094 [P] Create helm-charts/todo-app/templates/recurring-task-service-deployment.yaml with scheduler config
- [ ] T095 [P] Create helm-charts/todo-app/templates/audit-log-service-deployment.yaml with TimescaleDB connection

### Helm Templates for Infrastructure

- [ ] T096 [P] Create helm-charts/todo-app/templates/ingress.yaml for HTTP routing with TLS termination (cert-manager integration)

**Checkpoint**: Helm chart ready for deployment to dev/staging/prod with environment-specific configurations

---

## Group H: Observability (8 tasks)

**Purpose**: Monitoring, logging, tracing, and alerting for production readiness

### Prometheus & Grafana

- [ ] T097 Create kubernetes/observability/prometheus-config.yaml with scrape configs for FastAPI metrics (backend, notification service, recurring task service, audit log service)
- [ ] T098 [P] Deploy Prometheus operator to Kubernetes cluster with persistent storage for metrics retention
- [ ] T099 Create kubernetes/observability/grafana-dashboards/todo-app-overview.json with KPIs (task creation rate, notification delivery success rate, recurring task instance creation, audit log throughput)
- [ ] T100 [P] Create kubernetes/observability/grafana-dashboards/service-health.json with service-specific metrics (latency p50/p95/p99, error rate, request rate)

### Loki & Jaeger

- [ ] T101 [P] Deploy Loki for log aggregation with promtail DaemonSet to scrape pod logs
- [ ] T102 [P] Deploy Jaeger for distributed tracing with OpenTelemetry instrumentation
- [ ] T103 Update backend/src/main.py and all microservices to instrument with OpenTelemetry (trace task operations, Kafka events, service-to-service calls)

### Alerting

- [ ] T104 Create kubernetes/observability/prometheus-alerts.yaml with alerting rules (high error rate, notification delivery failures, Kafka consumer lag, scheduler job failures, audit log service down)

**Checkpoint**: Full observability stack operational with metrics, logs, traces, and alerts

---

## Group I: Cloud Infrastructure (10 tasks)

**Purpose**: Provision production Kubernetes clusters on GKE/AKS/OKE with managed services

### Cloud Kubernetes Cluster Setup (choose one)

- [ ] T105 Provision GKE cluster on Google Cloud with autopilot mode (3 nodes, e2-standard-4 instances, auto-scaling enabled) OR provision AKS cluster on Azure with managed identity (3 nodes, Standard_D4s_v3 instances, Azure CNI networking) OR provision OKE cluster on Oracle Cloud with free tier (2 nodes, VM.Standard.E4.Flex instances, OCI load balancer)

### Managed Database Setup

- [ ] T106 [P] Create managed PostgreSQL instance for main database (Neon Serverless on cloud provider, connection pooling enabled)
- [ ] T107 [P] Create managed TimescaleDB instance for audit logs (or self-host TimescaleDB in Kubernetes with persistent volumes)

### Managed Kafka Setup

- [ ] T108 Deploy Strimzi Kafka operator to Kubernetes cluster and create Kafka cluster custom resource (3 broker replicas, persistent storage, TLS encryption)
- [ ] T109 [P] Create Kafka topics via Strimzi KafkaTopic CRDs: task-events (partitions=3, replication=2), scheduled-reminders (partitions=3, replication=2), task-sync (partitions=3, replication=2)

### Dapr on Kubernetes

- [ ] T110 Install Dapr control plane to Kubernetes cluster with dapr init --kubernetes (creates dapr-system namespace with sidecar injector, placement service, sentry for mTLS)
- [ ] T111 [P] Create Dapr component manifests in kubernetes/dapr-components/ for Kafka pub/sub, Redis state store, and configure namespace-scoped components

### Ingress & TLS

- [ ] T112 [P] Install NGINX Ingress Controller to Kubernetes cluster with LoadBalancer service
- [ ] T113 Install cert-manager for automatic TLS certificate provisioning (Let's Encrypt integration) and create ClusterIssuer resource
- [ ] T114 Create Ingress resource in kubernetes/ingress.yaml with TLS configuration for todo.example.com domain

**Checkpoint**: Cloud Kubernetes cluster operational with managed services (PostgreSQL, Kafka, Ingress, TLS)

---

## Group J: Cloud Deployment (6 tasks)

**Purpose**: Deploy application to production cloud environment with Helm

### Helm Deployment

- [ ] T115 Create Kubernetes namespace for production deployment: kubectl create namespace todo-prod
- [ ] T116 [P] Create Kubernetes secrets for sensitive data: database credentials, Kafka credentials, JWT signing keys, SMTP credentials (use kubectl create secret or sealed-secrets)
- [ ] T117 Deploy backend service with Helm: helm install todo-app helm-charts/todo-app -f helm-charts/todo-app/values-prod.yaml --namespace todo-prod
- [ ] T118 [P] Deploy notification service with Helm: helm upgrade --install notification-service helm-charts/notification-service --namespace todo-prod
- [ ] T119 [P] Deploy recurring task service with Helm: helm upgrade --install recurring-task-service helm-charts/recurring-task-service --namespace todo-prod
- [ ] T120 [P] Deploy audit log service with Helm: helm upgrade --install audit-log-service helm-charts/audit-log-service --namespace todo-prod

**Checkpoint**: All services deployed to production cloud environment and accessible via Ingress

---

## Group K: CI/CD (6 tasks)

**Purpose**: Automate build, test, and deployment pipelines with GitHub Actions

### CI Pipeline

- [ ] T121 Create .github/workflows/backend-ci.yaml with jobs: lint (ruff), test (pytest with coverage), build (Docker image), push to registry (Docker Hub or GCR/ACR/OCIR)
- [ ] T122 [P] Create .github/workflows/frontend-ci.yaml with jobs: lint (ESLint), test (Jest/Vitest), build (npm run build), Docker image build/push
- [ ] T123 [P] Create .github/workflows/microservices-ci.yaml with jobs for notification, recurring task, and audit log services (lint, test, Docker build/push)

### CD Pipeline

- [ ] T124 Create .github/workflows/deploy-dev.yaml triggered on push to develop branch: helm upgrade with values-dev.yaml to dev namespace
- [ ] T125 Create .github/workflows/deploy-staging.yaml triggered on push to staging branch: helm upgrade with values-staging.yaml to staging namespace
- [ ] T126 Create .github/workflows/deploy-prod.yaml triggered on manual approval or tag push: helm upgrade with values-prod.yaml to prod namespace, blue-green deployment strategy

**Checkpoint**: CI/CD pipelines operational with automated testing and deployment to dev/staging/prod

---

## Group L: Testing & Documentation (7 tasks)

**Purpose**: Comprehensive testing and documentation for production readiness

### Backend Testing

- [ ] T127 [P] Create backend/tests/unit/test_datetime_parser.py with 21 test cases from research.md (absolute dates, relative dates, timezone conversion)
- [ ] T128 [P] Create backend/tests/unit/test_recurrence_calculator.py with 5 pattern tests + edge cases (Feb 31, leap year, DST)
- [ ] T129 [P] Create backend/tests/integration/test_task_lifecycle.py with end-to-end task creation → due date → notification → completion → history flow
- [ ] T130 [P] Create backend/tests/integration/test_recurring_tasks.py with recurring task completion → next instance creation → notification scheduling

### Frontend Testing

- [ ] T131 [P] Create frontend/tests/components/HistoryTab.test.tsx with tests for pagination, search, filter, restore functionality
- [ ] T132 [P] Create frontend/tests/hooks/useNotifications.test.ts with mock notification permission and scheduling logic

### Documentation

- [ ] T133 Create specs/012-advanced-todo-features/quickstart.md with step-by-step integration guide: local development setup, running migrations, starting services, testing due dates, testing recurring tasks, testing history tab, running observability stack, deploying to cloud

**Checkpoint**: All tests passing, documentation complete for handoff

---

## Dependencies & Execution Order

### Phase Dependencies

1. **Phase 1 (Setup)**: No dependencies - can start immediately
2. **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories and feature groups
3. **Group A (Advanced Features)**: Depends on Phase 2 completion
   - User Story 1 (US1: Due Dates) → User Story 2 (US2: Recurring Tasks) → User Story 3 (US3: History)
4. **Group B (Event Architecture)**: Depends on Phase 2 completion, can run in parallel with Group A
5. **Groups C, D, E (Microservices)**: Depend on Group B completion (Kafka operational)
6. **Group F (Dapr Integration)**: Depends on Groups C, D, E completion (services operational)
7. **Group G (Helm Charts)**: Can be created in parallel with Group A, must be complete before Group J
8. **Group H (Observability)**: Can be deployed in parallel with Groups C, D, E
9. **Group I (Cloud Infrastructure)**: Can be provisioned in parallel with Groups F, G, H
10. **Group J (Cloud Deployment)**: Depends on Groups F, G, I completion
11. **Group K (CI/CD)**: Depends on Group J completion (manual deployment working first)
12. **Group L (Testing & Docs)**: Can run in parallel with all groups, final validation before production

### Critical Path

```
Phase 1 (Setup)
  → Phase 2 (Foundational - BLOCKS everything)
    → Group A (Advanced Features) → Group B (Event Architecture) → Groups C, D, E (Microservices)
    → Group G (Helm Charts) → Group I (Cloud Infrastructure) → Group J (Cloud Deployment) → Group K (CI/CD)
    → Group H (Observability - parallel)
    → Group F (Dapr Integration - after microservices)
    → Group L (Testing & Docs - parallel, final validation)
```

### Parallel Opportunities

- **Within Phase 1**: All tasks [P] can run in parallel (T002, T003, T004, T005)
- **Within Phase 2**: Models (T011, T012, T013), utilities (T014, T015), T020 can run in parallel after migrations complete
- **Group A Tasks**: Many [P] tasks within each user story can run in parallel (models, frontend components, utilities)
- **Group B**: T050, T052, T056 can run in parallel; producers (T053, T054) can run in parallel after T051
- **Groups C, D, E**: All three microservices can be developed in parallel after Group B
- **Group G**: All Helm template tasks (T092-T096) can run in parallel
- **Group H**: Prometheus (T098), Loki (T101), Jaeger (T102) deployments can run in parallel
- **Group I**: Managed database (T106), TimescaleDB (T107), NGINX Ingress (T112) can run in parallel
- **Group J**: Service deployments (T118, T119, T120) can run in parallel after T117
- **Group K**: CI pipelines (T121, T122, T123) can run in parallel
- **Group L**: All test tasks (T127-T132) can run in parallel

---

## Implementation Strategy

### MVP First (Group A - User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T020) - **CRITICAL GATE**
3. Complete Group A Phase 3: User Story 1 (T021-T030)
4. **STOP and VALIDATE**: Test due dates and reminders independently
5. Deploy/demo if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready
2. Add Group A US1 (Due Dates) → Test independently → Deploy/Demo (MVP!)
3. Add Group A US2 (Recurring Tasks) → Test independently → Deploy/Demo
4. Add Group A US3 (History Tab) → Test independently → Deploy/Demo
5. Add Group B (Event Architecture) → Kafka operational
6. Add Groups C, D, E (Microservices) → Event-driven architecture operational
7. Add Group F (Dapr Integration) → Resilience and observability improved
8. Add Group G + I + J (Helm + Cloud Deployment) → Production deployment ready
9. Add Group K (CI/CD) → Automated deployments
10. Add Group H + L (Observability + Testing) → Production-grade monitoring and testing

### Total Task Count

- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 15 tasks (T006-T020)
- **Group A (Advanced Features)**: 29 tasks (T021-T049, including US1/US2/US3 and extensions)
- **Group B (Event Architecture)**: 7 tasks (T050-T056)
- **Group C (Notification Service)**: 8 tasks (T057-T064)
- **Group D (Recurring Task Service)**: 7 tasks (T065-T071)
- **Group E (Audit Log Service)**: 8 tasks (T072-T079)
- **Group F (Dapr Integration)**: 8 tasks (T080-T087)
- **Group G (Helm Charts)**: 9 tasks (T088-T096)
- **Group H (Observability)**: 8 tasks (T097-T104)
- **Group I (Cloud Infrastructure)**: 10 tasks (T105-T114)
- **Group J (Cloud Deployment)**: 6 tasks (T115-T120)
- **Group K (CI/CD)**: 6 tasks (T121-T126)
- **Group L (Testing & Docs)**: 7 tasks (T127-T133)

**Total: 133 tasks across 12 groups + 2 foundational phases**

**Estimated Effort**:
- MVP (Phase 1-2 + Group A US1): ~12-16 hours
- Full Group A (all 3 user stories): ~20-24 hours
- Event Architecture + Microservices (Groups B-E): ~24-32 hours
- Cloud Deployment (Groups F-J): ~16-20 hours
- CI/CD + Testing (Groups K-L): ~8-12 hours
- **Total: 68-88 hours** for complete implementation

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] labels (US1, US2, US3) map tasks to user stories for traceability
- Each user story (US1, US2, US3) is independently completable and testable within Group A
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Group A (Advanced Features) is the core user-facing functionality
- Groups B-F are backend infrastructure for scalability and resilience
- Groups G-K are deployment and operational automation
- Group L ensures production readiness with testing and documentation
