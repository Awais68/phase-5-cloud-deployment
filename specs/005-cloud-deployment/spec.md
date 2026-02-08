# Feature Specification: Cloud Deployment with Advanced Features

**Feature Branch**: `005-cloud-deployment`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "Phase V: Cloud Deployment with Advanced Features, Event-Driven Architecture, and Dapr Integration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recurring Task Management (Priority: P1)

Users need to create tasks that repeat automatically based on schedules (daily, weekly, monthly, yearly), eliminating manual recreation of routine tasks.

**Why this priority**: Recurring tasks are a fundamental productivity feature requested by users. Without this, users must manually recreate routine tasks, leading to missed deadlines and user frustration.

**Independent Test**: Can be fully tested by creating a daily recurring task, marking it complete, and verifying the next instance is auto-created with the correct due date. Delivers immediate value by automating routine task management.

**Acceptance Scenarios**:

1. **Given** a user wants to create a recurring task, **When** they select "daily" recurrence and save the task, **Then** the task is created with recurrence metadata stored
2. **Given** a recurring task is marked complete, **When** the system processes the completion event, **Then** a new task instance is automatically created with the next due date calculated
3. **Given** a recurring task has an end date, **When** the end date is reached, **Then** no new instances are created after that date
4. **Given** a recurring task has a maximum occurrence count, **When** that count is reached, **Then** the recurrence stops automatically

---

### User Story 2 - Due Dates and Reminders (Priority: P1)

Users need to set due dates for tasks and receive timely notifications to avoid missing deadlines.

**Why this priority**: Time-sensitive task management is critical for productivity. Without reminders, users must constantly check their task list, defeating the purpose of a task management system.

**Independent Test**: Can be tested by creating a task with a due date 1 hour from now, setting a 15-minute advance reminder, and verifying browser/email notifications are delivered at the correct time.

**Acceptance Scenarios**:

1. **Given** a user creates a task, **When** they select a due date and time via the date/time picker, **Then** the due date is stored with timezone information
2. **Given** a task has a due date, **When** the user configures a reminder advance time (e.g., 1 hour before), **Then** the reminder is scheduled
3. **Given** a reminder time arrives, **When** the notification service processes the reminder event, **Then** the user receives a browser/push notification
4. **Given** a task is overdue, **When** the user views their task list, **Then** overdue tasks are visually highlighted
5. **Given** email notifications are enabled, **When** a reminder triggers, **Then** an email is sent to the user's registered email address

---

### User Story 3 - Task Prioritization and Categorization (Priority: P2)

Users need to organize tasks by priority and categories to focus on what matters most and group related tasks.

**Why this priority**: Prioritization helps users focus on critical tasks first. Categories enable organization of personal vs. work tasks. Essential for medium-to-large task lists.

**Independent Test**: Can be tested by creating tasks with different priorities (high, medium, low) and tags (work, personal), then filtering the task list to show only "high priority work tasks."

**Acceptance Scenarios**:

1. **Given** a user creates a task, **When** they assign a priority level (high/medium/low), **Then** the priority is stored and visually indicated with color coding
2. **Given** a user creates a task, **When** they add tags/categories (work, personal, shopping), **Then** the tags are stored and displayed on the task
3. **Given** tasks have different priorities, **When** the user views the task list, **Then** tasks can be sorted by priority with high-priority tasks appearing first
4. **Given** tasks have tags, **When** the user selects a category filter, **Then** only tasks with that tag are displayed

---

### User Story 4 - Advanced Search and Filtering (Priority: P2)

Users need to quickly find specific tasks among hundreds of entries using keyword search and multi-criteria filters.

**Why this priority**: As task lists grow, manual scanning becomes impractical. Search and filtering are essential for scalability and user efficiency.

**Independent Test**: Can be tested by creating 50 sample tasks with varied attributes, then searching for "meeting" and filtering by "high priority + work tag + due this week" to verify correct results.

**Acceptance Scenarios**:

1. **Given** a user has many tasks, **When** they enter a keyword in the search box, **Then** tasks matching the keyword in title or description are displayed
2. **Given** a user wants to narrow results, **When** they apply filters (status, priority, due date range, tags), **Then** only tasks matching all selected filters are shown
3. **Given** a user applies multiple filters, **When** they add a keyword search, **Then** results match both the keyword and all filters
4. **Given** a user has applied filters, **When** they clear filters, **Then** the full task list is restored

---

### User Story 5 - Flexible Task Sorting (Priority: P3)

Users need to sort tasks by different criteria (due date, priority, creation date, alphabetically) to view their task list in the most helpful order.

**Why this priority**: Different contexts require different sorting. Users planning their day need due-date sorting; users triaging need priority sorting. Enhances usability but not critical for MVP.

**Independent Test**: Can be tested by creating tasks with varied attributes, then switching between sort modes (due date ascending, priority descending, alphabetical) and verifying correct ordering.

**Acceptance Scenarios**:

1. **Given** a user views their task list, **When** they select "sort by due date (ascending)," **Then** tasks are ordered from earliest to latest due date, with undated tasks at the end
2. **Given** a user views their task list, **When** they select "sort by priority (descending)," **Then** high-priority tasks appear first, followed by medium and low
3. **Given** a user views their task list, **When** they select "sort alphabetically," **Then** tasks are ordered A-Z by title
4. **Given** a sort mode is active, **When** the user toggles ascending/descending, **Then** the order is reversed

---

### User Story 6 - Event-Driven Microservices Architecture (Priority: P1)

The system must publish events for all task operations to enable real-time features, audit trails, and service decoupling.

**Why this priority**: Event-driven architecture is foundational for scalability, real-time sync, audit logging, and microservices communication. Must be implemented early to avoid architectural debt.

**Independent Test**: Can be tested by creating a task, verifying the event is published to `task-events` topic with correct schema, and confirming the audit service logs the event.

**Acceptance Scenarios**:

1. **Given** a user creates a task, **When** the task is saved, **Then** a `TaskCreated` event is published to the `task-events` Kafka topic with standardized schema
2. **Given** a user updates a task, **When** the update is saved, **Then** a `TaskUpdated` event is published with before/after snapshots
3. **Given** a user deletes a task, **When** the deletion is confirmed, **Then** a `TaskDeleted` event is published
4. **Given** a reminder time arrives, **When** the scheduler triggers, **Then** a `ReminderDue` event is published to the `reminders` topic
5. **Given** an event is published, **When** consumers are unavailable, **Then** Kafka retains the event for reprocessing when consumers reconnect

---

### User Story 7 - Notification Service (Priority: P1)

Users must receive notifications via browser push, email, and in-app channels when reminders are due.

**Why this priority**: Notifications are the primary value of reminders. Without notifications, reminders are useless. Critical for user retention.

**Independent Test**: Can be tested by setting a task reminder for 2 minutes from now, then verifying browser push and email notifications are delivered within 10 seconds of the reminder time.

**Acceptance Scenarios**:

1. **Given** a `ReminderDue` event is published, **When** the notification service consumes the event, **Then** a browser push notification is sent to the user's active sessions
2. **Given** email notifications are enabled for the user, **When** a reminder triggers, **Then** an email is sent via the configured email service
3. **Given** a notification fails to deliver, **When** the failure is detected, **Then** the notification is retried up to 3 times with exponential backoff
4. **Given** a user has multiple active sessions, **When** a notification is sent, **Then** all sessions receive the notification

---

### User Story 8 - Recurring Task Service (Priority: P1)

When recurring tasks are completed, the system must automatically create the next instance without user intervention.

**Why this priority**: Automation is the core value of recurring tasks. Manual recreation defeats the purpose. This service is required for recurring tasks to function.

**Independent Test**: Can be tested by creating a weekly recurring task, marking it complete, and verifying the next instance is created with a due date exactly 7 days after the previous one.

**Acceptance Scenarios**:

1. **Given** a recurring task is marked complete, **When** the `TaskCompleted` event is published, **Then** the recurring task service consumes the event
2. **Given** the recurring task service processes the event, **When** the task has active recurrence rules, **Then** a new task instance is created with the next due date calculated
3. **Given** a new instance is created, **When** the instance is saved, **Then** a `TaskCreated` event is published for the new instance
4. **Given** a recurring task has reached its end date or max occurrences, **When** a completion event is processed, **Then** no new instance is created

---

### User Story 9 - Audit Log Service (Priority: P2)

The system must maintain an immutable audit trail of all task operations for compliance, debugging, and user history.

**Why this priority**: Audit trails are essential for enterprise compliance, debugging production issues, and providing users with a history of changes. Important but not blocking for MVP.

**Independent Test**: Can be tested by creating, updating, and deleting a task, then querying the audit log API to verify all three events are recorded with timestamps, user IDs, and event payloads.

**Acceptance Scenarios**:

1. **Given** any task event is published, **When** the audit log service consumes the event, **Then** the event is stored in an immutable time-series database
2. **Given** audit logs are stored, **When** a user queries their task history, **Then** all events for their tasks are returned in chronological order
3. **Given** audit logs are stored, **When** an administrator queries by user ID, **Then** all events for that user are returned
4. **Given** audit logs exceed retention period, **When** the retention policy runs, **Then** old logs are archived or deleted per compliance rules

---

### User Story 10 - Dapr Integration (Priority: P2)

The system must leverage Dapr building blocks for pub/sub, state management, secrets, and service-to-service communication.

**Why this priority**: Dapr abstracts infrastructure complexity, enables cloud portability, and provides mTLS, retries, and observability out-of-the-box. Important for production-grade deployment but can be phased in.

**Independent Test**: Can be tested by publishing a test event via Dapr pub/sub, verifying it's delivered to Kafka, then invoking a microservice via Dapr service invocation and confirming mTLS encryption.

**Acceptance Scenarios**:

1. **Given** the Task API publishes an event, **When** using Dapr pub/sub, **Then** the event is delivered to the configured Kafka topic via Dapr's pub/sub component
2. **Given** the Notification Service stores state, **When** using Dapr state store, **Then** state is persisted to PostgreSQL via Dapr's state component
3. **Given** services need secrets, **When** using Dapr secrets component, **Then** secrets are retrieved from Kubernetes Secrets without hardcoding
4. **Given** the Recurring Task Service invokes the Task API, **When** using Dapr service invocation, **Then** calls are encrypted with mTLS and include automatic retries
5. **Given** scheduled reminders are needed, **When** using Dapr bindings, **Then** cron-based triggers are configured to publish reminder events at specified times
6. **Given** recurring reminders are needed, **When** using Dapr Jobs API, **Then** jobs are scheduled to create reminder events at task due times

---

### Edge Cases

- What happens when a user deletes a recurring task? Should future instances also be deleted, or only the current one?
- How does the system handle clock skew or timezone changes for scheduled reminders?
- What happens when the Kafka broker is unavailable during event publishing? Should the API block or return success with eventual consistency?
- How does the system handle duplicate events (e.g., retry storms)? Are consumers idempotent?
- What happens when a user has thousands of overdue tasks? Does the UI degrade?
- How does the system handle concurrent updates to the same task from multiple clients?
- What happens when a reminder fires but the user's browser is closed or offline?
- How does the system handle very long task titles or descriptions that exceed display limits?
- What happens when a user sets a due date in the past? Is it allowed, or rejected?
- How does the system handle leap years, daylight saving time transitions, and end-of-month calculations for monthly/yearly recurring tasks?

## Requirements *(mandatory)*

### Functional Requirements

#### Part A: Advanced Features

**Recurring Tasks**
- **FR-001**: System MUST allow users to create recurring tasks with the following patterns: daily, weekly, biweekly, monthly, yearly
- **FR-002**: System MUST store recurrence rules including pattern, interval, end date (optional), and maximum occurrence count (optional)
- **FR-003**: System MUST automatically create the next task instance when a recurring task is marked complete
- **FR-004**: System MUST calculate the next due date based on the recurrence pattern and the completion timestamp
- **FR-005**: System MUST stop creating new instances when the end date is reached or maximum occurrence count is met
- **FR-006**: System MUST allow users to update recurrence rules for future instances without affecting past instances
- **FR-007**: System MUST allow users to skip a single occurrence without deleting the recurrence pattern. Skipped occurrences do NOT count toward the maximum occurrence limit (ensures users still get the full count of tasks they requested)

**Due Dates & Reminders**
- **FR-008**: System MUST provide date/time pickers for setting task due dates with timezone support
- **FR-009**: System MUST allow users to configure reminder advance time (e.g., 15 minutes, 1 hour, 1 day before due time)
- **FR-010**: System MUST send browser push notifications when reminders are due
- **FR-011**: System MUST send email notifications when reminders are due (if user has enabled email notifications)
- **FR-012**: System MUST visually highlight overdue tasks in the UI
- **FR-013**: System MUST store all timestamps in UTC and convert to user's local timezone for display
- **FR-014**: System MUST allow multiple reminders per task (e.g., 1 day before and 1 hour before)

**Priorities & Tags**
- **FR-015**: System MUST support three priority levels: high, medium, low
- **FR-016**: System MUST allow users to assign one priority level per task (default: medium)
- **FR-017**: System MUST support user-defined tags/categories (e.g., work, personal, shopping)
- **FR-018**: System MUST allow users to assign multiple tags to a single task
- **FR-019**: System MUST provide color coding for priority levels (high=red, medium=yellow, low=green as defaults)
- **FR-020**: System MUST allow users to create, rename, and delete custom tags

**Search & Filter**
- **FR-021**: System MUST provide keyword search across task titles and descriptions
- **FR-022**: System MUST support filtering by: status (pending/completed), priority, due date range, tags
- **FR-023**: System MUST support combining multiple filters (AND logic)
- **FR-024**: System MUST support combining keyword search with filters
- **FR-025**: System MUST return search results in real-time (as user types) with debouncing to avoid excessive queries

**Sorting**
- **FR-026**: System MUST support sorting by: due date, priority, creation date, title (alphabetically)
- **FR-027**: System MUST support ascending and descending order for each sort criterion
- **FR-028**: System MUST apply sorting to filtered results
- **FR-029**: System MUST persist user's preferred sort mode across sessions

#### Part B: Event-Driven Architecture

**Kafka Topics**
- **FR-030**: System MUST publish all task CRUD operations (create, read, update, delete, complete) to the `task-events` Kafka topic
- **FR-031**: System MUST publish reminder notifications to the `reminders` Kafka topic
- **FR-032**: System MUST publish real-time updates to the `task-updates` Kafka topic for client synchronization
- **FR-033**: System MUST use at least 3 partitions per topic for scalability
- **FR-034**: System MUST configure Kafka topics with appropriate retention policies (e.g., 7 days for task-events, 1 day for reminders)

**Event Schemas**
- **FR-035**: All task events MUST include: event_type (string), task_id (UUID), task_data (JSON object), user_id (UUID), timestamp (ISO8601), correlation_id (UUID)
- **FR-036**: All reminder events MUST include: task_id (UUID), title (string), due_at (ISO8601), remind_at (ISO8601), user_id (UUID), notification_channels (array)
- **FR-037**: System MUST validate event schemas before publishing to Kafka
- **FR-038**: System MUST include event versioning (schema_version field) for backwards compatibility

**Microservices**

*Notification Service*
- **FR-039**: Notification Service MUST consume events from the `reminders` Kafka topic
- **FR-040**: Notification Service MUST send browser push notifications using Web Push API
- **FR-041**: Notification Service MUST send email notifications using SMTP or email service provider API
- **FR-042**: Notification Service MUST implement retry logic with exponential backoff for failed notifications (max 3 retries)
- **FR-043**: Notification Service MUST log all notification attempts and outcomes for debugging

*Recurring Task Service*
- **FR-044**: Recurring Task Service MUST consume `TaskCompleted` events from the `task-events` Kafka topic
- **FR-045**: Recurring Task Service MUST calculate the next due date based on recurrence rules and completion timestamp
- **FR-046**: Recurring Task Service MUST create new task instances by calling the Task API
- **FR-047**: Recurring Task Service MUST respect recurrence end dates and max occurrence limits
- **FR-048**: Recurring Task Service MUST be idempotent (handle duplicate events without creating duplicate tasks)

*Audit Log Service*
- **FR-049**: Audit Log Service MUST consume all events from the `task-events` Kafka topic
- **FR-050**: Audit Log Service MUST store events in an immutable time-series database (e.g., TimescaleDB or append-only table)
- **FR-051**: Audit Log Service MUST provide a query API for retrieving audit logs by user_id, task_id, date range, and event_type
- **FR-052**: Audit Log Service MUST implement data retention policies with a 1-year retention period to meet enterprise-grade compliance requirements (GDPR, SOC2)
- **FR-053**: Audit Log Service MUST include indexes on user_id, task_id, and timestamp for query performance

#### Part C: Dapr Integration

**Pub/Sub Component**
- **FR-054**: System MUST configure Dapr pub/sub component to use Kafka as the message broker
- **FR-055**: Services MUST publish events via Dapr pub/sub API instead of directly to Kafka client libraries
- **FR-056**: Services MUST subscribe to topics via Dapr pub/sub API with automatic message acknowledgment
- **FR-057**: Dapr pub/sub MUST handle message retries and dead-letter queues for poison messages

**State Store Component**
- **FR-058**: System MUST configure Dapr state store component to use PostgreSQL for persistent state
- **FR-059**: Services MUST use Dapr state API for storing and retrieving application state (e.g., user preferences, notification delivery status)
- **FR-060**: Dapr state store MUST support transactional state operations (multi-item updates)
- **FR-061**: Dapr state store MUST support TTL (time-to-live) for ephemeral state

**Secrets Component**
- **FR-062**: System MUST configure Dapr secrets component to use Kubernetes Secrets as the secret store
- **FR-063**: Services MUST retrieve secrets (database passwords, API keys, SMTP credentials) via Dapr secrets API
- **FR-064**: Secrets MUST NOT be hardcoded in application code or environment variables
- **FR-065**: Dapr secrets component MUST support secret versioning and rotation

**Bindings Component**
- **FR-066**: System MUST configure Dapr cron bindings for scheduled reminder checks
- **FR-067**: Dapr cron binding MUST trigger the Reminder Scheduler service at configurable intervals (e.g., every minute)
- **FR-068**: Reminder Scheduler service MUST query for tasks with due reminders and publish `ReminderDue` events to the `reminders` topic

**Service Invocation**
- **FR-069**: Microservices MUST use Dapr service invocation API for inter-service communication (e.g., Recurring Task Service calling Task API)
- **FR-070**: Dapr service invocation MUST encrypt all traffic with mutual TLS (mTLS) automatically
- **FR-071**: Dapr service invocation MUST implement automatic retries with exponential backoff for transient failures
- **FR-072**: Dapr service invocation MUST integrate with distributed tracing (OpenTelemetry) for observability

**Dapr Jobs API**
- **FR-073**: System MUST use Dapr Jobs API for scheduling individual reminder jobs at specific times (as an alternative to cron polling)
- **FR-074**: When a task with a reminder is created/updated, a Dapr job MUST be scheduled to fire at the remind_at timestamp
- **FR-075**: Dapr job execution MUST publish a `ReminderDue` event to the `reminders` topic
- **FR-076**: When a task is deleted, the corresponding Dapr job MUST be cancelled. If the job has already fired and published a reminder event but notification is still pending, the Notification Service MUST check task existence before sending notifications and skip deleted tasks

### Key Entities

- **Task**: Represents a user's to-do item with attributes: id (UUID), user_id (UUID), title (string, max 200 chars), description (string, optional, max 2000 chars), status (enum: pending/completed), priority (enum: high/medium/low), due_at (timestamp, optional, timezone-aware), completed_at (timestamp, optional), created_at (timestamp), updated_at (timestamp), tags (array of strings), recurrence_rule (JSON object, optional)

- **RecurrenceRule**: Defines how a task repeats with attributes: pattern (enum: daily/weekly/biweekly/monthly/yearly), interval (integer, default 1), end_date (timestamp, optional), max_occurrences (integer, optional), parent_task_id (UUID, references the original recurring task), occurrence_count (integer, tracks current count)

- **Reminder**: Represents a scheduled notification with attributes: id (UUID), task_id (UUID, foreign key), user_id (UUID), remind_at (timestamp, timezone-aware), notification_channels (array: browser, email), status (enum: pending/sent/failed), created_at (timestamp), sent_at (timestamp, optional)

- **AuditLogEntry**: Immutable record of a task event with attributes: id (UUID), event_type (string), task_id (UUID), user_id (UUID), event_data (JSON, full event payload), timestamp (timestamp, indexed), correlation_id (UUID)

- **Tag**: User-defined category with attributes: id (UUID), user_id (UUID), name (string, unique per user, max 50 chars), color (string, hex color code), created_at (timestamp)

- **UserPreferences**: User settings with attributes: user_id (UUID, primary key), default_reminder_advance (integer, minutes), enable_email_notifications (boolean), enable_browser_notifications (boolean), default_sort_mode (string), default_filter (JSON object)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a recurring task and verify the next instance is auto-created within 5 seconds of marking the current instance complete
- **SC-002**: Users receive reminder notifications within 10 seconds of the scheduled remind_at time
- **SC-003**: Keyword search returns results in under 500ms for task lists up to 10,000 tasks per user
- **SC-004**: The system supports 1,000 concurrent users performing task operations without latency degradation (p95 < 1 second)
- **SC-005**: All task events are successfully published to Kafka with at-least-once delivery guarantee
- **SC-006**: All microservices achieve 99.9% uptime (measured over 30-day period)
- **SC-007**: Audit logs are queryable with results returned in under 2 seconds for date ranges up to 90 days
- **SC-008**: Dapr service invocation reduces inter-service communication failures by 80% compared to direct HTTP calls (due to automatic retries)
- **SC-009**: Zero secret exposure incidents (no secrets in logs, code, or environment variables)
- **SC-010**: The system correctly handles timezone conversions for users in at least 10 different timezones
- **SC-011**: Users can filter and sort task lists of 1,000+ tasks with no perceptible lag (< 300ms response time)
- **SC-012**: Recurring tasks with monthly patterns correctly handle end-of-month edge cases (e.g., Jan 31 → Feb 28/29 → Mar 31)
- **SC-013**: The notification service maintains a delivery success rate of 95% or higher for browser push notifications
- **SC-014**: Dapr components (pub/sub, state store, secrets, bindings) are successfully deployed and operational in Kubernetes cluster
- **SC-015**: All inter-service communication uses mTLS encryption (verified via Dapr sidecar logs and network traces)

## Assumptions

1. **User Authentication**: Assumes existing authentication system provides user_id for all requests
2. **Database**: Assumes PostgreSQL is the primary database for task data and Dapr state store
3. **Kafka Deployment**: Assumes Kafka cluster is deployed and accessible (Strimzi on Kubernetes recommended for Part D/E)
4. **Email Service**: Assumes SMTP server or email service provider (SendGrid, SES) is available for email notifications
5. **Browser Support**: Assumes modern browsers with Web Push API support (Chrome 50+, Firefox 44+, Safari 16+)
6. **Kubernetes**: Assumes Kubernetes cluster is available for microservices deployment
7. **Dapr**: Assumes Dapr control plane is deployed in Kubernetes cluster
8. **Timezone Handling**: Assumes all timestamps are stored in UTC and converted to user's timezone in the frontend
9. **Idempotency**: Assumes Kafka consumers implement idempotency using correlation_id or event_id to handle duplicate messages
10. **Scalability Target**: Assumes initial deployment targets 1,000 concurrent users; will scale horizontally for larger loads
11. **Retention Policy**: Assumes default 7-day retention for task-events, 1-day for reminders, and 1-year for audit logs (configurable)
12. **Search Implementation**: Assumes full-text search is implemented using database LIKE queries initially; Elasticsearch can be added later for advanced search
13. **Notification Channels**: Assumes browser push and email are sufficient; SMS and mobile push can be added in future phases
14. **Recurring Task Completion**: Assumes marking a recurring task complete does NOT complete all future instances (only the current one)
15. **Conflict Resolution**: Assumes last-write-wins for concurrent updates; optimistic locking can be added later if needed

## Dependencies

1. **Phase II Infrastructure**: Requires Next.js frontend, FastAPI backend, and Neon PostgreSQL database from Phase II
2. **Kafka Cluster**: Requires Kafka broker deployment (can use managed Kafka or Strimzi operator on Kubernetes)
3. **Dapr Installation**: Requires Dapr control plane and sidecars installed in Kubernetes cluster
4. **Notification Infrastructure**: Requires Web Push certificate (VAPID keys) and email service configuration
5. **Kubernetes Secrets**: Requires creation of Kubernetes Secrets for database passwords, Kafka credentials, email credentials, and API keys
6. **TimescaleDB Extension** (optional): If using TimescaleDB for audit logs, requires PostgreSQL extension installation
7. **Observability Stack** (recommended): Requires Prometheus, Grafana, and Jaeger for monitoring Dapr and microservices

## Out of Scope

1. **Mobile Applications**: Native iOS/Android apps are out of scope (web app only)
2. **Collaborative Task Sharing**: Sharing tasks between users is out of scope for Phase V
3. **Task Attachments**: File uploads/attachments are out of scope
4. **Advanced Recurrence Patterns**: Complex patterns like "last Friday of every month" or "every other Monday and Wednesday" are out of scope (only simple daily/weekly/monthly/yearly)
5. **Natural Language Task Creation**: Voice assistants or NLP-based task input are out of scope
6. **Offline Mode**: Full offline functionality with sync is out of scope (requires service worker implementation in future phase)
7. **Task Templates**: Pre-defined task templates are out of scope
8. **Subtasks**: Hierarchical task relationships (parent/child tasks) are out of scope
9. **Task Assignment**: Assigning tasks to other users is out of scope (single-user model only)
10. **Third-Party Integrations**: Calendar sync (Google Calendar, Outlook), Slack notifications, etc. are out of scope for Phase V
11. **AI-Powered Features**: AI task suggestions, auto-categorization, or natural language processing are out of scope (already covered in Phase III chatbot)
12. **Advanced Analytics**: Usage analytics, productivity reports, and dashboards are out of scope
13. **Custom Notification Sounds**: User-defined notification sounds are out of scope (browser default sounds only)
14. **Geofencing Reminders**: Location-based reminders are out of scope
15. **Multi-Tenancy**: Organization/team-level features are out of scope (single-user only)

## Risks & Mitigations

### Risk 1: Kafka Availability
**Description**: If Kafka broker becomes unavailable, event publishing will fail, breaking real-time features and audit logging.

**Impact**: High - Notification and recurring task services depend on Kafka

**Mitigation**:
- Deploy Kafka with replication factor of 3 for high availability
- Implement circuit breaker pattern in event publishers to fail gracefully
- Use Dapr pub/sub outbox pattern to persist events locally before publishing
- Monitor Kafka lag and broker health with alerts

### Risk 2: Notification Delivery Failures
**Description**: Browser push notifications may fail due to user denying permissions, closed browsers, or service worker issues.

**Impact**: Medium - Users may miss reminders

**Mitigation**:
- Implement fallback to email notifications when push fails
- Store notification delivery status for retry logic
- Provide in-app notification history for users to check missed notifications
- Educate users during onboarding about enabling notification permissions

### Risk 3: Timezone Calculation Errors
**Description**: Incorrect timezone handling could cause reminders to fire at wrong times, especially during DST transitions.

**Impact**: High - Erodes user trust in the system

**Mitigation**:
- Store all timestamps in UTC, convert to user timezone only in UI
- Use well-tested timezone libraries (Python: pytz/zoneinfo, JavaScript: date-fns-tz)
- Write extensive test cases for DST transitions, leap years, and edge-of-month calculations
- Validate timezone conversions with automated integration tests

### Risk 4: Recurring Task Bugs
**Description**: Complex recurrence logic (end-of-month, leap years, etc.) may have edge case bugs.

**Impact**: High - Incorrect task generation frustrates users

**Mitigation**:
- Implement comprehensive unit tests for date calculation logic
- Use property-based testing (Hypothesis in Python) to catch edge cases
- Log all recurrence calculations for debugging
- Provide UI for users to review upcoming instances before they're created

### Risk 5: Event Duplication
**Description**: Kafka retries or at-least-once delivery may cause duplicate events, leading to duplicate tasks or notifications.

**Impact**: Medium - Annoying for users, data integrity issues

**Mitigation**:
- Make all consumers idempotent using correlation_id or event_id deduplication
- Store processed event IDs in database with TTL
- Use Kafka exactly-once semantics where supported
- Implement deduplication window (e.g., ignore duplicate events within 5 minutes)

### Risk 6: Dapr Learning Curve
**Description**: Team may lack experience with Dapr, causing implementation delays or misconfigurations.

**Impact**: Medium - Project timeline risk

**Mitigation**:
- Allocate time for Dapr training and experimentation
- Start with simple Dapr features (pub/sub, secrets) before advanced ones (jobs, workflows)
- Use Dapr quickstarts and official documentation extensively
- Consider consulting with Dapr community or Microsoft for guidance

### Risk 7: Database Performance Degradation
**Description**: As task and audit log tables grow, queries may become slow, impacting user experience.

**Impact**: Medium - UX degradation over time

**Mitigation**:
- Add database indexes on frequently queried columns (user_id, due_at, priority, tags)
- Implement pagination for task lists (50 tasks per page)
- Archive or partition old audit logs using TimescaleDB or PostgreSQL partitioning
- Monitor query performance with slow query logs and profiling tools

### Risk 8: Kubernetes Complexity
**Description**: Managing multiple microservices, Dapr sidecars, Kafka, and databases in Kubernetes is complex.

**Impact**: High - Operational burden, deployment failures

**Mitigation**:
- Use Helm charts for templated, repeatable deployments
- Implement health checks and readiness probes for all services
- Use Kubernetes namespaces to isolate environments (dev, staging, prod)
- Invest in CI/CD pipelines for automated testing and deployment
- Implement centralized logging (Loki/ELK) and monitoring (Prometheus/Grafana)

## Notes

- This specification intentionally avoids implementation details (e.g., specific API endpoints, database schemas, React components) - these will be defined in the planning phase
- Event schemas should be versioned from day one to support backwards-compatible evolution
- Consider using Avro or Protobuf for event serialization if schema validation and evolution become critical
- Dapr Jobs API is experimental as of Dapr 1.12 - verify stability before production use, or fallback to cron bindings
- The system should be designed for horizontal scaling - all services should be stateless (state in PostgreSQL/Kafka only)
- Security considerations (authentication, authorization, data encryption) are assumed to be carried forward from Phase II and expanded in the planning phase
- This phase represents a significant architectural shift from monolithic to microservices - plan for incremental migration if needed
