"""
Unit tests for Notification Preference Logic.

Tests cover:
- User preference management
- Channel selection logic
- Quiet hours enforcement
- Rate limiting calculations
- Notification priority routing
"""
import pytest
from datetime import datetime, time
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Notification Models (for unit testing without importing service)
# =============================================================================

class NotificationChannel(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    WEBSOCKET = "websocket"
    SMS = "sms"


@dataclass
class NotificationPreference:
    """User notification preferences."""
    user_id: str
    email_enabled: bool = True
    push_enabled: bool = True
    websocket_enabled: bool = True
    sms_enabled: bool = False
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    preferred_channels: Optional[List[str]] = None
    rate_limit_per_minute: int = 10


class NotificationPreferenceService:
    """Service for managing notification preferences."""

    @staticmethod
    def get_enabled_channels(pref: NotificationPreference) -> List[NotificationChannel]:
        """Get list of enabled notification channels."""
        channels = []
        if pref.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if pref.push_enabled:
            channels.append(NotificationChannel.PUSH)
        if pref.websocket_enabled:
            channels.append(NotificationChannel.WEBSOCKET)
        if pref.sms_enabled:
            channels.append(NotificationChannel.SMS)
        return channels

    @staticmethod
    def is_in_quiet_hours(pref: NotificationPreference, current_time: time) -> bool:
        """Check if current time is within quiet hours."""
        if not pref.quiet_hours_start or not pref.quiet_hours_end:
            return False

        start = pref.quiet_hours_start
        end = pref.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 - 08:00)
        if start > end:
            return current_time >= start or current_time <= end
        else:
            return start <= current_time <= end

    @staticmethod
    def should_send_notification(
        pref: NotificationPreference,
        channel: NotificationChannel,
        current_time: time,
        is_urgent: bool = False,
    ) -> bool:
        """Determine if notification should be sent."""
        # Urgent notifications bypass quiet hours
        if not is_urgent and NotificationPreferenceService.is_in_quiet_hours(pref, current_time):
            return False

        # Check if channel is enabled
        enabled_channels = NotificationPreferenceService.get_enabled_channels(pref)
        return channel in enabled_channels

    @staticmethod
    def select_best_channel(
        pref: NotificationPreference,
        available_channels: List[NotificationChannel],
    ) -> Optional[NotificationChannel]:
        """Select the best notification channel based on preferences."""
        enabled = NotificationPreferenceService.get_enabled_channels(pref)
        
        # If preferred channels are set, prioritize them
        if pref.preferred_channels:
            for ch_name in pref.preferred_channels:
                try:
                    ch = NotificationChannel(ch_name)
                    if ch in enabled and ch in available_channels:
                        return ch
                except ValueError:
                    continue

        # Default priority: push > websocket > email > sms
        priority = [
            NotificationChannel.PUSH,
            NotificationChannel.WEBSOCKET,
            NotificationChannel.EMAIL,
            NotificationChannel.SMS,
        ]
        
        for ch in priority:
            if ch in enabled and ch in available_channels:
                return ch
        
        return None

    @staticmethod
    def calculate_rate_limit_remaining(
        pref: NotificationPreference,
        sent_in_last_minute: int,
    ) -> int:
        """Calculate remaining rate limit for notifications."""
        return max(0, pref.rate_limit_per_minute - sent_in_last_minute)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def default_preferences():
    """Default notification preferences."""
    return NotificationPreference(
        user_id="user-123",
        email_enabled=True,
        push_enabled=True,
        websocket_enabled=True,
        sms_enabled=False,
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(8, 0),
        rate_limit_per_minute=10,
    )


@pytest.fixture
def minimal_preferences():
    """Minimal notification preferences (only email)."""
    return NotificationPreference(
        user_id="user-456",
        email_enabled=True,
        push_enabled=False,
        websocket_enabled=False,
        sms_enabled=False,
    )


@pytest.fixture
def all_channels_preferences():
    """All channels enabled preferences."""
    return NotificationPreference(
        user_id="user-789",
        email_enabled=True,
        push_enabled=True,
        websocket_enabled=True,
        sms_enabled=True,
    )


@pytest.fixture
def service():
    """Notification preference service instance."""
    return NotificationPreferenceService()


# =============================================================================
# Channel Enable/Disable Tests
# =============================================================================

class TestChannelEnablement:
    """Tests for channel enablement logic."""

    def test_get_enabled_channels_default(self, service, default_preferences):
        """Get enabled channels for default preferences."""
        channels = service.get_enabled_channels(default_preferences)
        assert NotificationChannel.EMAIL in channels
        assert NotificationChannel.PUSH in channels
        assert NotificationChannel.WEBSOCKET in channels
        assert NotificationChannel.SMS not in channels

    def test_get_enabled_channels_minimal(self, service, minimal_preferences):
        """Get enabled channels for minimal preferences."""
        channels = service.get_enabled_channels(minimal_preferences)
        assert len(channels) == 1
        assert NotificationChannel.EMAIL in channels

    def test_get_enabled_channels_all(self, service, all_channels_preferences):
        """Get enabled channels when all are enabled."""
        channels = service.get_enabled_channels(all_channels_preferences)
        assert len(channels) == 4

    def test_get_enabled_channels_none(self, service):
        """Get enabled channels when none are enabled."""
        pref = NotificationPreference(
            user_id="user-no-channels",
            email_enabled=False,
            push_enabled=False,
            websocket_enabled=False,
            sms_enabled=False,
        )
        channels = service.get_enabled_channels(pref)
        assert len(channels) == 0


# =============================================================================
# Quiet Hours Tests
# =============================================================================

class TestQuietHours:
    """Tests for quiet hours enforcement."""

    def test_in_quiet_hours_night_time(self, service, default_preferences):
        """Check if 23:00 is in quiet hours (22:00-08:00)."""
        current = time(23, 0)
        assert service.is_in_quiet_hours(default_preferences, current) is True

    def test_in_quiet_hours_early_morning(self, service, default_preferences):
        """Check if 03:00 is in quiet hours (22:00-08:00)."""
        current = time(3, 0)
        assert service.is_in_quiet_hours(default_preferences, current) is True

    def test_not_in_quiet_hours_daytime(self, service, default_preferences):
        """Check if 14:00 is not in quiet hours (22:00-08:00)."""
        current = time(14, 0)
        assert service.is_in_quiet_hours(default_preferences, current) is False

    def test_no_quiet_hours_configured(self, service, minimal_preferences):
        """No quiet hours when not configured."""
        current = time(23, 0)
        assert service.is_in_quiet_hours(minimal_preferences, current) is False

    def test_quiet_hours_boundary_start(self, service, default_preferences):
        """Check quiet hours at exact start time."""
        current = time(22, 0)
        assert service.is_in_quiet_hours(default_preferences, current) is True

    def test_quiet_hours_boundary_end(self, service, default_preferences):
        """Check quiet hours at exact end time."""
        current = time(8, 0)
        assert service.is_in_quiet_hours(default_preferences, current) is True

    def test_quiet_hours_daytime_range(self, service):
        """Test daytime quiet hours (not overnight)."""
        pref = NotificationPreference(
            user_id="daytime-quiet",
            quiet_hours_start=time(12, 0),
            quiet_hours_end=time(14, 0),
        )
        assert service.is_in_quiet_hours(pref, time(13, 0)) is True
        assert service.is_in_quiet_hours(pref, time(11, 0)) is False
        assert service.is_in_quiet_hours(pref, time(15, 0)) is False


# =============================================================================
# Notification Sending Decision Tests
# =============================================================================

class TestNotificationSending:
    """Tests for notification sending decisions."""

    def test_should_send_normal_during_day(self, service, default_preferences):
        """Normal notification during daytime should be sent."""
        result = service.should_send_notification(
            default_preferences,
            NotificationChannel.EMAIL,
            current_time=time(14, 0),
            is_urgent=False
        )
        assert result is True

    def test_should_not_send_normal_during_quiet(self, service, default_preferences):
        """Normal notification during quiet hours should not be sent."""
        result = service.should_send_notification(
            default_preferences,
            NotificationChannel.EMAIL,
            current_time=time(23, 0),
            is_urgent=False
        )
        assert result is False

    def test_should_send_urgent_during_quiet(self, service, default_preferences):
        """Urgent notification during quiet hours should be sent."""
        result = service.should_send_notification(
            default_preferences,
            NotificationChannel.EMAIL,
            current_time=time(23, 0),
            is_urgent=True
        )
        assert result is True

    def test_should_not_send_disabled_channel(self, service, default_preferences):
        """Notification to disabled channel should not be sent."""
        result = service.should_send_notification(
            default_preferences,
            NotificationChannel.SMS,  # SMS is disabled
            current_time=time(14, 0),
            is_urgent=False
        )
        assert result is False


# =============================================================================
# Channel Selection Tests
# =============================================================================

class TestChannelSelection:
    """Tests for best channel selection."""

    def test_select_push_as_default_best(self, service, default_preferences):
        """Push is selected as best by default."""
        available = [NotificationChannel.EMAIL, NotificationChannel.PUSH]
        best = service.select_best_channel(default_preferences, available)
        assert best == NotificationChannel.PUSH

    def test_select_from_preferred_channels(self, service):
        """Select from preferred channels list."""
        pref = NotificationPreference(
            user_id="user-pref",
            email_enabled=True,
            push_enabled=True,
            preferred_channels=["email", "push"],  # Email preferred
        )
        available = [NotificationChannel.EMAIL, NotificationChannel.PUSH]
        best = service.select_best_channel(pref, available)
        assert best == NotificationChannel.EMAIL

    def test_select_none_when_none_available(self, service, minimal_preferences):
        """Return None when no channels available."""
        available = [NotificationChannel.PUSH]  # Not enabled
        best = service.select_best_channel(minimal_preferences, available)
        assert best is None

    def test_select_fallback_when_preferred_unavailable(self, service):
        """Fallback to default priority when preferred unavailable."""
        pref = NotificationPreference(
            user_id="user-fallback",
            email_enabled=True,
            push_enabled=True,
            preferred_channels=["sms"],  # Not enabled
        )
        available = [NotificationChannel.EMAIL, NotificationChannel.PUSH]
        best = service.select_best_channel(pref, available)
        assert best == NotificationChannel.PUSH  # Default priority


# =============================================================================
# Rate Limiting Tests
# =============================================================================

class TestRateLimiting:
    """Tests for rate limiting calculations."""

    def test_rate_limit_full_remaining(self, service, default_preferences):
        """Full rate limit remaining when none sent."""
        remaining = service.calculate_rate_limit_remaining(
            default_preferences, sent_in_last_minute=0
        )
        assert remaining == 10

    def test_rate_limit_partial_remaining(self, service, default_preferences):
        """Partial rate limit remaining."""
        remaining = service.calculate_rate_limit_remaining(
            default_preferences, sent_in_last_minute=7
        )
        assert remaining == 3

    def test_rate_limit_none_remaining(self, service, default_preferences):
        """No rate limit remaining when at limit."""
        remaining = service.calculate_rate_limit_remaining(
            default_preferences, sent_in_last_minute=10
        )
        assert remaining == 0

    def test_rate_limit_over_limit(self, service, default_preferences):
        """Rate limit returns 0 when over limit."""
        remaining = service.calculate_rate_limit_remaining(
            default_preferences, sent_in_last_minute=15
        )
        assert remaining == 0


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_preferred_channels(self, service):
        """Handle empty preferred channels list."""
        pref = NotificationPreference(
            user_id="empty-pref",
            email_enabled=True,
            push_enabled=True,
            preferred_channels=[],
        )
        available = [NotificationChannel.EMAIL, NotificationChannel.PUSH]
        best = service.select_best_channel(pref, available)
        # Should fall back to default priority
        assert best == NotificationChannel.PUSH

    def test_invalid_preferred_channel(self, service):
        """Handle invalid channel name in preferences."""
        pref = NotificationPreference(
            user_id="invalid-pref",
            email_enabled=True,
            preferred_channels=["invalid_channel", "email"],
        )
        available = [NotificationChannel.EMAIL]
        best = service.select_best_channel(pref, available)
        assert best == NotificationChannel.EMAIL

    def test_midnight_boundary_quiet_hours(self, service):
        """Test quiet hours at midnight boundary."""
        pref = NotificationPreference(
            user_id="midnight-test",
            quiet_hours_start=time(23, 59),
            quiet_hours_end=time(0, 1),
        )
        # Right at midnight
        assert service.is_in_quiet_hours(pref, time(0, 0)) is True
        # Just before start
        assert service.is_in_quiet_hours(pref, time(23, 58)) is False

    def test_custom_rate_limit(self, service):
        """Test custom rate limit value."""
        pref = NotificationPreference(
            user_id="custom-limit",
            rate_limit_per_minute=5,
        )
        remaining = service.calculate_rate_limit_remaining(pref, sent_in_last_minute=3)
        assert remaining == 2
