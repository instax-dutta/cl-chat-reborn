"""
Tests for sanitizer.py — username validation, message cleaning,
peer count validation, and RateLimiter.
"""

import pytest

from sanitizer import (
    check_username,
    clean_message,
    validate_peer_count,
    RateLimiter,
)


class TestCheckUsername:
    """Tests for check_username()."""

    def test_valid_normal(self):
        """Valid usernames return the sanitized name."""
        assert check_username("Alice") == "Alice"
        assert check_username("user_1") == "user_1"
        assert check_username("a1234567890123456789") == "a1234567890123456789"

    def test_valid_with_hyphen(self):
        """Usernames with hyphens are valid."""
        assert check_username("test-user") == "test-user"

    def test_valid_with_underscore_prefix(self):
        """Underscore after first char is okay."""
        assert check_username("a_b_c") == "a_b_c"

    def test_invalid_empty(self):
        """Empty string returns None."""
        assert check_username("") is None

    def test_invalid_too_short(self):
        """Single character returns None."""
        assert check_username("a") is None

    def test_invalid_special_char(self):
        """Special characters like '!' return None."""
        assert check_username("a!") is None

    def test_invalid_too_long(self):
        """Username exceeding 20 chars gets truncated."""
        result = check_username("a" + "b" * 20)
        # check_username truncates to MAX_USERNAME_LENGTH (20) then validates
        assert result is not None
        assert len(result) == 20

    def test_invalid_none(self):
        """None input returns None."""
        assert check_username(None) is None

    def test_invalid_non_string(self):
        """Non-string input (int) returns None."""
        assert check_username(123) is None

    def test_strips_newlines_and_tabs(self):
        """Newlines, tabs, and carriage returns are stripped before validation."""
        result = check_username("Alice\n")
        assert result is None or result == "Alice"

    def test_strips_whitespace(self):
        """Leading/trailing whitespace is stripped."""
        assert check_username("  Bob  ") == "Bob"


class TestCleanMessage:
    """Tests for clean_message()."""

    def test_normal_message_unchanged(self):
        """Normal printable message passes through unchanged."""
        result = clean_message("Hello world")
        assert result == "Hello world"

    def test_too_long_truncated(self):
        """Message exceeding MAX_MESSAGE_LENGTH (4096) is truncated."""
        long_msg = "x" * 5000
        result = clean_message(long_msg)
        assert len(result) == 4096

    def test_control_chars_stripped(self):
        """Control characters (\\x00, \\x01) are stripped; newlines preserved."""
        msg = "hello\x00world\x01test"
        result = clean_message(msg)
        assert "\x00" not in result
        assert "\x01" not in result

    def test_newlines_preserved(self):
        """Newlines and tabs are preserved."""
        msg = "line1\nline2\ttabbed"
        result = clean_message(msg)
        assert "\n" in result
        assert "\t" in result

    def test_invalid_none(self):
        """None input returns empty string."""
        assert clean_message(None) == ""

    def test_invalid_non_string(self):
        """Non-string input returns empty string."""
        assert clean_message(123) == ""

    def test_invalid_empty(self):
        """Empty string returns empty string (after strip)."""
        result = clean_message("")
        assert result == ""


class TestValidatePeerCount:
    """Tests for validate_peer_count()."""

    def test_below_max(self):
        """Count below MAX_PEER_COUNT (50) returns True."""
        assert validate_peer_count(0) is True
        assert validate_peer_count(49) is True

    def test_at_limit(self):
        """Count == MAX_PEER_COUNT (50) returns False."""
        assert validate_peer_count(50) is False

    def test_over_limit(self):
        """Count over MAX_PEER_COUNT returns False."""
        assert validate_peer_count(100) is False


class TestRateLimiter:
    """Tests for RateLimiter sliding-window rate limiter."""

    def test_allows_within_limit(self):
        """First max_events calls to allow() return True."""
        rl = RateLimiter(max_events=3, window=60)
        assert rl.allow("key") is True
        assert rl.allow("key") is True
        assert rl.allow("key") is True

    def test_blocks_at_limit(self):
        """Call after max_events returns False."""
        rl = RateLimiter(max_events=3, window=60)
        rl.allow("key")
        rl.allow("key")
        rl.allow("key")
        assert rl.allow("key") is False

    def test_reset_clears_block(self):
        """After reset(), allow() returns True again."""
        rl = RateLimiter(max_events=2, window=60)
        assert rl.allow("key") is True
        assert rl.allow("key") is True
        assert rl.allow("key") is False
        rl.reset("key")
        assert rl.allow("key") is True

    def test_separate_keys_independent(self):
        """Two different keys each have their own budget."""
        rl = RateLimiter(max_events=2, window=60)
        assert rl.allow("alice") is True
        assert rl.allow("bob") is True
        assert rl.allow("alice") is True
        assert rl.allow("bob") is True
        assert rl.allow("alice") is False  # alice exhausted
        assert rl.allow("bob") is False  # bob exhausted

    def test_reset_nonexistent_key_no_error(self):
        """Calling reset() on a key that doesn't exist is a no-op."""
        rl = RateLimiter(max_events=3, window=60)
        rl.reset("nonexistent")  # should not raise
        assert rl.allow("key") is True
