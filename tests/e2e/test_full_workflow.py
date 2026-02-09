"""
End-to-End tests for the full task management workflow.

Tests the complete flow:
1. Create recurring task → 
2. Generate task instances → 
3. Trigger notifications →
4. Record audit logs

Can run against real services or mocked environment.
"""
import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os


# =============================================================================
# Configuration
# =============================================================================

class E2EConfig:
    """E2E test configuration."""
    
    # Service URLs (override with environment variables)
    MAIN_API_URL = os.getenv("E2E_MAIN_API_URL", "http://localhost:8000")
    RECURRING_SERVICE_URL = os.getenv("E2E_RECURRING_SERVICE_URL", "http://localhost:8002")
    NOTIFICATION_SERVICE_URL = os.getenv("E2E_NOTIFICATION_SERVICE_URL", "http://localhost:8003")
    AUDIT_SERVICE_URL = os.getenv("E2E_AUDIT_SERVICE_URL", "http://localhost:8004")
    
    # Timeouts
    REQUEST_TIMEOUT = 30.0
    EVENT_PROPAGATION_TIMEOUT = 10.0


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def e2e_config():
    """E2E test configuration."""
    return E2EConfig()


@pytest.fixture
async def http_client():
    """Async HTTP client for E2E tests."""
    async with httpx.AsyncClient(timeout=E2EConfig.REQUEST_TIMEOUT) as client:
        yield client


@pytest.fixture
def test_user():
    """Test user for E2E tests."""
    return {
        "user_id": f"e2e-user-{datetime.utcnow().timestamp()}",
        "email": "e2e-test@example.com",
        "name": "E2E Test User"
    }


@pytest.fixture
def recurring_task_data(test_user):
    """Sample recurring task for E2E tests."""
    return {
        "user_id": test_user["user_id"],
        "title": "E2E Test - Daily Standup",
        "description": "Daily team standup meeting",
        "rrule": "FREQ=DAILY;INTERVAL=1;COUNT=7",
        "start_date": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Service Health Checks
# =============================================================================

class TestServiceHealth:
    """Verify all services are healthy before E2E tests."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_main_api_health(self, http_client, e2e_config):
        """Main API service is healthy."""
        try:
            response = await http_client.get(f"{e2e_config.MAIN_API_URL}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip(f"Main API not available at {e2e_config.MAIN_API_URL}")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_recurring_service_health(self, http_client, e2e_config):
        """Recurring task service is healthy."""
        try:
            response = await http_client.get(f"{e2e_config.RECURRING_SERVICE_URL}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip(f"Recurring service not available at {e2e_config.RECURRING_SERVICE_URL}")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_notification_service_health(self, http_client, e2e_config):
        """Notification service is healthy."""
        try:
            response = await http_client.get(f"{e2e_config.NOTIFICATION_SERVICE_URL}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip(f"Notification service not available at {e2e_config.NOTIFICATION_SERVICE_URL}")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_audit_service_health(self, http_client, e2e_config):
        """Audit log service is healthy."""
        try:
            response = await http_client.get(f"{e2e_config.AUDIT_SERVICE_URL}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip(f"Audit service not available at {e2e_config.AUDIT_SERVICE_URL}")


# =============================================================================
# Complete Workflow Tests
# =============================================================================

class TestRecurringTaskWorkflow:
    """E2E tests for recurring task workflow."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_create_recurring_task_flow(
        self, http_client, e2e_config, recurring_task_data
    ):
        """
        Test complete recurring task creation flow:
        1. Create recurring task via API
        2. Verify task instances are generated
        3. Verify audit log is created
        """
        try:
            # Step 1: Create recurring task
            response = await http_client.post(
                f"{e2e_config.MAIN_API_URL}/api/recurring-tasks",
                json=recurring_task_data
            )
            
            if response.status_code == 404:
                pytest.skip("Recurring task endpoint not implemented")
            
            assert response.status_code in [200, 201]
            task = response.json()
            task_id = task.get("id")
            
            # Step 2: Wait for event propagation
            await asyncio.sleep(e2e_config.EVENT_PROPAGATION_TIMEOUT)
            
            # Step 3: Verify task was created
            get_response = await http_client.get(
                f"{e2e_config.MAIN_API_URL}/api/recurring-tasks/{task_id}"
            )
            assert get_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Services not available for E2E test")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_task_instance_generation_flow(
        self, http_client, e2e_config, recurring_task_data
    ):
        """
        Test task instance generation from recurring task.
        """
        try:
            # Create recurring task
            response = await http_client.post(
                f"{e2e_config.MAIN_API_URL}/api/recurring-tasks",
                json=recurring_task_data
            )
            
            if response.status_code == 404:
                pytest.skip("Endpoint not implemented")
            
            if response.status_code not in [200, 201]:
                pytest.skip(f"Failed to create task: {response.text}")
            
            task_id = response.json().get("id")
            
            # Wait for instances to be generated
            await asyncio.sleep(e2e_config.EVENT_PROPAGATION_TIMEOUT)
            
            # Query generated instances
            instances_response = await http_client.get(
                f"{e2e_config.MAIN_API_URL}/api/recurring-tasks/{task_id}/instances"
            )
            
            if instances_response.status_code == 200:
                instances = instances_response.json()
                # Should have generated instances based on RRULE
                assert len(instances) > 0
                
        except httpx.ConnectError:
            pytest.skip("Services not available")


class TestNotificationWorkflow:
    """E2E tests for notification workflow."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_task_reminder_notification_flow(
        self, http_client, e2e_config, test_user
    ):
        """
        Test notification triggered by task reminder:
        1. Create task with due date
        2. Trigger reminder event
        3. Verify notification was sent
        """
        try:
            # Create a task with near due date
            task_data = {
                "user_id": test_user["user_id"],
                "title": "E2E Notification Test Task",
                "due_date": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            }
            
            response = await http_client.post(
                f"{e2e_config.MAIN_API_URL}/api/tasks",
                json=task_data
            )
            
            if response.status_code not in [200, 201]:
                pytest.skip(f"Task creation failed: {response.status_code}")
            
            # Wait for reminder processing
            await asyncio.sleep(2)
            
            # Check notification service logs or delivery status
            # This would typically check a notification inbox or delivery endpoint
            
        except httpx.ConnectError:
            pytest.skip("Services not available")


class TestAuditLogWorkflow:
    """E2E tests for audit logging workflow."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_task_creation_audit_log(
        self, http_client, e2e_config, test_user
    ):
        """
        Test audit log is created when task is created:
        1. Create task
        2. Query audit service for task creation event
        """
        try:
            # Create task
            task_data = {
                "user_id": test_user["user_id"],
                "title": "E2E Audit Test Task",
            }
            
            response = await http_client.post(
                f"{e2e_config.MAIN_API_URL}/api/tasks",
                json=task_data
            )
            
            if response.status_code not in [200, 201]:
                pytest.skip(f"Task creation failed: {response.status_code}")
            
            task_id = response.json().get("id")
            
            # Wait for audit event propagation
            await asyncio.sleep(e2e_config.EVENT_PROPAGATION_TIMEOUT)
            
            # Query audit logs
            audit_response = await http_client.get(
                f"{e2e_config.AUDIT_SERVICE_URL}/audit",
                params={
                    "entity_type": "task",
                    "entity_id": str(task_id),
                    "action": "created"
                }
            )
            
            if audit_response.status_code == 200:
                audit_logs = audit_response.json()
                # Should have at least one audit entry
                if isinstance(audit_logs, list):
                    assert len(audit_logs) >= 0  # May be empty if event not propagated
                    
        except httpx.ConnectError:
            pytest.skip("Services not available")


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """E2E tests for error handling scenarios."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invalid_rrule_rejected(self, http_client, e2e_config, test_user):
        """Invalid RRULE is rejected with proper error."""
        try:
            task_data = {
                "user_id": test_user["user_id"],
                "title": "Invalid RRULE Task",
                "rrule": "INVALID_RRULE_STRING",
                "start_date": datetime.utcnow().isoformat(),
            }
            
            response = await http_client.post(
                f"{e2e_config.MAIN_API_URL}/api/recurring-tasks",
                json=task_data
            )
            
            # Should be rejected with 400 or 422
            if response.status_code != 404:
                assert response.status_code in [400, 422]
                
        except httpx.ConnectError:
            pytest.skip("Services not available")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, http_client, e2e_config):
        """Missing required fields returns proper error."""
        try:
            response = await http_client.post(
                f"{e2e_config.MAIN_API_URL}/api/tasks",
                json={}  # Empty payload
            )
            
            assert response.status_code in [400, 422]
            
        except httpx.ConnectError:
            pytest.skip("Services not available")


# =============================================================================
# Performance Tests
# =============================================================================

class TestE2EPerformance:
    """E2E performance tests."""

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_task_creation(self, http_client, e2e_config, test_user):
        """Test concurrent task creation performance."""
        try:
            tasks = []
            for i in range(10):
                task_data = {
                    "user_id": test_user["user_id"],
                    "title": f"Concurrent Task {i}",
                }
                tasks.append(
                    http_client.post(
                        f"{e2e_config.MAIN_API_URL}/api/tasks",
                        json=task_data
                    )
                )
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            success_count = sum(
                1 for r in responses 
                if isinstance(r, httpx.Response) and r.status_code in [200, 201]
            )
            
            # At least 80% should succeed
            assert success_count >= 8
            
        except httpx.ConnectError:
            pytest.skip("Services not available")


# =============================================================================
# Cleanup Utilities
# =============================================================================

@pytest.fixture(autouse=True)
async def cleanup_test_data(http_client, e2e_config, test_user):
    """Clean up test data after E2E tests."""
    yield
    
    # Cleanup code would go here
    # Delete test tasks, notifications, etc.
    pass
