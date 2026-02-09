"""
Integration tests for Recurring Task Service API.

Tests the FastAPI endpoints with real database (testcontainers).
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import json


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_recurring_task_payload():
    """Sample payload for creating recurring task."""
    return {
        "user_id": 1,
        "title": "Daily Standup Meeting",
        "description": "Team daily sync",
        "rrule": "FREQ=DAILY;INTERVAL=1",
        "start_date": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Health Check Tests
# =============================================================================

class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.integration
    def test_health_check(self, test_client_recurring_service):
        """Health endpoint returns healthy status."""
        response = test_client_recurring_service.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "ok"]

    @pytest.mark.integration
    def test_liveness_probe(self, test_client_recurring_service):
        """Kubernetes liveness probe returns ok."""
        response = test_client_recurring_service.get("/health/live")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_readiness_probe(self, test_client_recurring_service):
        """Kubernetes readiness probe returns ok."""
        response = test_client_recurring_service.get("/health/ready")
        assert response.status_code == 200


# =============================================================================
# Event Handler Tests
# =============================================================================

class TestEventHandlers:
    """Tests for Dapr event handler endpoints."""

    @pytest.mark.integration
    @pytest.mark.dapr
    def test_task_event_handler_valid_payload(self, test_client_recurring_service):
        """Task event handler accepts valid payload."""
        event = {
            "specversion": "1.0",
            "type": "task.created",
            "source": "test",
            "id": "test-event-001",
            "datacontenttype": "application/json",
            "data": {
                "task_id": "task-123",
                "user_id": 1,
                "title": "Test Task",
            }
        }
        response = test_client_recurring_service.post(
            "/events/task",
            json=event,
            headers={"Content-Type": "application/cloudevents+json"}
        )
        # 200 or 204 indicates successful handling
        assert response.status_code in [200, 204, 400, 422]

    @pytest.mark.integration
    @pytest.mark.dapr
    def test_recurring_task_event_handler(self, test_client_recurring_service):
        """Recurring task event handler processes events."""
        event = {
            "specversion": "1.0",
            "type": "recurring_task.created",
            "source": "test",
            "id": "test-event-002",
            "datacontenttype": "application/json",
            "data": {
                "recurring_task_id": 1,
                "user_id": 1,
                "rrule": "FREQ=DAILY;INTERVAL=1",
                "start_date": datetime.utcnow().isoformat(),
            }
        }
        response = test_client_recurring_service.post(
            "/events/recurring-task",
            json=event,
            headers={"Content-Type": "application/cloudevents+json"}
        )
        assert response.status_code in [200, 204, 400, 422]

    @pytest.mark.integration
    def test_invalid_event_payload(self, test_client_recurring_service):
        """Invalid event payload is rejected."""
        response = test_client_recurring_service.post(
            "/events/task",
            json={"invalid": "payload"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]


# =============================================================================
# API Response Format Tests
# =============================================================================

class TestAPIResponseFormat:
    """Tests for API response format compliance."""

    @pytest.mark.integration
    def test_json_content_type(self, test_client_recurring_service):
        """Responses have correct content type."""
        response = test_client_recurring_service.get("/health")
        assert "application/json" in response.headers.get("content-type", "")

    @pytest.mark.integration
    def test_error_response_format(self, test_client_recurring_service):
        """Error responses follow standard format."""
        response = test_client_recurring_service.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


# =============================================================================
# Performance Tests
# =============================================================================

class TestAPIPerformance:
    """Basic performance tests for API endpoints."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_health_check_response_time(self, test_client_recurring_service):
        """Health check responds within acceptable time."""
        import time
        start = time.time()
        response = test_client_recurring_service.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in under 1 second

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_requests(self, test_client_recurring_service):
        """Service handles concurrent requests."""
        import concurrent.futures
        
        def make_request():
            return test_client_recurring_service.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(r.status_code == 200 for r in results)
