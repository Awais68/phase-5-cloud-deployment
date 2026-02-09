"""
Locust Load Testing for Todo App Microservices.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Web UI available at: http://localhost:8089

For headless execution:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
        --users=100 --spawn-rate=10 --run-time=5m --headless
"""
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import json
import random
import string
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Test Data Generation
# =============================================================================

def generate_task_title():
    """Generate random task title."""
    prefixes = ["Review", "Complete", "Fix", "Update", "Create", "Test", "Deploy"]
    subjects = ["feature", "bug", "documentation", "API", "database", "UI", "tests"]
    return f"{random.choice(prefixes)} {random.choice(subjects)} {random.randint(1, 1000)}"


def generate_rrule():
    """Generate random RRULE."""
    frequencies = [
        "FREQ=DAILY;INTERVAL=1",
        "FREQ=DAILY;INTERVAL=2",
        "FREQ=WEEKLY;INTERVAL=1",
        "FREQ=WEEKLY;BYDAY=MO,WE,FR",
        "FREQ=MONTHLY;BYMONTHDAY=1",
        "FREQ=MONTHLY;BYMONTHDAY=15",
    ]
    return random.choice(frequencies)


def generate_user_id():
    """Generate random user ID."""
    return f"load-test-user-{random.randint(1, 10000)}"


# =============================================================================
# Main API User
# =============================================================================

class TodoAPIUser(HttpUser):
    """
    Load test user for main Todo API.
    
    Simulates typical user behavior:
    - Creating tasks
    - Listing tasks
    - Updating tasks
    - Completing tasks
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user with random ID."""
        self.user_id = generate_user_id()
        self.created_tasks = []
    
    @task(10)
    def create_task(self):
        """Create a new task."""
        payload = {
            "user_id": self.user_id,
            "title": generate_task_title(),
            "description": f"Load test task created at {datetime.utcnow().isoformat()}",
            "priority": random.choice(["low", "medium", "high"]),
            "due_date": (datetime.utcnow() + timedelta(days=random.randint(1, 30))).isoformat(),
        }
        
        with self.client.post(
            "/api/tasks",
            json=payload,
            catch_response=True,
            name="/api/tasks [POST]"
        ) as response:
            if response.status_code in [200, 201]:
                task_data = response.json()
                task_id = task_data.get("id")
                if task_id:
                    self.created_tasks.append(task_id)
                response.success()
            elif response.status_code == 404:
                response.failure("Endpoint not found - check API routes")
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(20)
    def list_tasks(self):
        """List all tasks for user."""
        with self.client.get(
            f"/api/tasks?user_id={self.user_id}",
            catch_response=True,
            name="/api/tasks [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Endpoint not found")
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(5)
    def get_single_task(self):
        """Get a single task by ID."""
        if not self.created_tasks:
            return
        
        task_id = random.choice(self.created_tasks)
        with self.client.get(
            f"/api/tasks/{task_id}",
            catch_response=True,
            name="/api/tasks/{id} [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Task may have been deleted
                self.created_tasks.remove(task_id)
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    def update_task(self):
        """Update an existing task."""
        if not self.created_tasks:
            return
        
        task_id = random.choice(self.created_tasks)
        payload = {
            "title": generate_task_title(),
            "priority": random.choice(["low", "medium", "high"]),
        }
        
        with self.client.put(
            f"/api/tasks/{task_id}",
            json=payload,
            catch_response=True,
            name="/api/tasks/{id} [PUT]"
        ) as response:
            if response.status_code in [200, 204]:
                response.success()
            elif response.status_code == 404:
                self.created_tasks.remove(task_id)
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def complete_task(self):
        """Mark a task as complete."""
        if not self.created_tasks:
            return
        
        task_id = random.choice(self.created_tasks)
        payload = {"status": "completed"}
        
        with self.client.patch(
            f"/api/tasks/{task_id}",
            json=payload,
            catch_response=True,
            name="/api/tasks/{id} [PATCH]"
        ) as response:
            if response.status_code in [200, 204]:
                response.success()
            elif response.status_code == 404:
                self.created_tasks.remove(task_id)
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    def delete_task(self):
        """Delete a task."""
        if not self.created_tasks:
            return
        
        task_id = self.created_tasks.pop()
        
        with self.client.delete(
            f"/api/tasks/{task_id}",
            catch_response=True,
            name="/api/tasks/{id} [DELETE]"
        ) as response:
            if response.status_code in [200, 204]:
                response.success()
            elif response.status_code == 404:
                response.success()  # Already deleted
            else:
                response.failure(f"Failed: {response.status_code}")


# =============================================================================
# Recurring Task Service User
# =============================================================================

class RecurringTaskUser(HttpUser):
    """
    Load test user for Recurring Task Service.
    
    Tests recurring task creation and instance generation.
    """
    
    wait_time = between(2, 5)
    host = "http://localhost:8002"  # Override for this user
    
    def on_start(self):
        """Initialize user."""
        self.user_id = generate_user_id()
    
    @task(5)
    def create_recurring_task(self):
        """Create a recurring task."""
        payload = {
            "user_id": self.user_id,
            "title": f"Recurring: {generate_task_title()}",
            "rrule": generate_rrule(),
            "start_date": datetime.utcnow().isoformat(),
        }
        
        with self.client.post(
            "/api/recurring-tasks",
            json=payload,
            catch_response=True,
            name="/api/recurring-tasks [POST]"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.failure("Endpoint not found")
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(10)
    def health_check(self):
        """Health check endpoint."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


# =============================================================================
# Notification Service User
# =============================================================================

class NotificationServiceUser(HttpUser):
    """
    Load test user for Notification Service.
    
    Tests notification endpoints and delivery.
    """
    
    wait_time = between(1, 3)
    host = "http://localhost:8003"
    
    @task(10)
    def health_check(self):
        """Health check endpoint."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(3)
    def trigger_test_notification(self):
        """Trigger a test notification."""
        payload = {
            "user_id": generate_user_id(),
            "type": "test",
            "title": "Load Test Notification",
            "body": f"Test notification at {datetime.utcnow().isoformat()}",
            "channels": ["websocket"],  # Use websocket for load testing
        }
        
        with self.client.post(
            "/api/notifications/test",
            json=payload,
            catch_response=True,
            name="/api/notifications/test [POST]"
        ) as response:
            if response.status_code in [200, 201, 204]:
                response.success()
            elif response.status_code == 404:
                response.failure("Endpoint not found")
            else:
                response.failure(f"Failed: {response.status_code}")


# =============================================================================
# Audit Service User
# =============================================================================

class AuditServiceUser(HttpUser):
    """
    Load test user for Audit Log Service.
    
    Tests audit log querying.
    """
    
    wait_time = between(2, 5)
    host = "http://localhost:8004"
    
    @task(10)
    def health_check(self):
        """Health check endpoint."""
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(5)
    def query_audit_logs(self):
        """Query audit logs."""
        params = {
            "entity_type": random.choice(["task", "user", "recurring_task"]),
            "limit": 50,
        }
        
        with self.client.get(
            "/audit",
            params=params,
            catch_response=True,
            name="/audit [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Endpoint not found")
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def query_user_activity(self):
        """Query user activity trail."""
        user_id = generate_user_id()
        
        with self.client.get(
            f"/audit/user/{user_id}/activity",
            catch_response=True,
            name="/audit/user/{id}/activity [GET]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()  # 404 is ok if user has no activity
            else:
                response.failure(f"Failed: {response.status_code}")


# =============================================================================
# Event Handlers for Statistics
# =============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    logger.info("Load test starting...")
    if isinstance(environment.runner, MasterRunner):
        logger.info("Running in distributed mode")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test completion."""
    logger.info("Load test completed")
    
    # Print summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Requests/s: {stats.total.current_rps:.2f}")
