"""
Rate limiting middleware for WebSocket connections.
"""

import asyncio

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

@dataclass
class RateLimitState:
    """Rate limiting state for a specific identifier."""

    # Connection tracking
    connections: int = 0
    first_connection: Optional[float] = None

    # Message rate limiting (sliding window)
    message_times: deque = field(default_factory=deque)
    burst_tokens: int = 0
    last_token_refresh: float = field(default_factory=time.time)

    def add_message(self, timestamp: float, window_seconds: int, max_messages: int) -> bool:
        """Add a message and check if rate limit is exceeded."""
        # Clean old messages outside the window
        cutoff = timestamp - window_seconds
        while self.message_times and self.message_times[0] < cutoff:
            self.message_times.popleft()

        # Check if we're at the limit
        if len(self.message_times) >= max_messages:
            return False

        # Add the new message
        self.message_times.append(timestamp)
        return True

    def add_burst_token(self, timestamp: float, refill_rate: float, max_tokens: int):
        """Add tokens to burst bucket (token bucket algorithm)."""
        time_passed = timestamp - self.last_token_refresh
        tokens_to_add = int(time_passed * refill_rate)

        if tokens_to_add > 0:
            self.burst_tokens = min(max_tokens, self.burst_tokens + tokens_to_add)
            self.last_token_refresh = timestamp

    def consume_burst_token(self) -> bool:
        """Try to consume a burst token."""
        if self.burst_tokens > 0:
            self.burst_tokens -= 1
            return True
        return False

class RateLimitMiddleware:
    """Rate limiting middleware for WebSocket connections."""

    def __init__(self, config):
        self.config = config

        # Rate limiting state
        self._ip_state: dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._user_state: dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._tenant_state: dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._session_state: dict[str, RateLimitState] = defaultdict(RateLimitState)

        # Active sessions for tracking
        self._active_sessions: dict[str, dict[str, Any]] = {}  # session_id -> session_info

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup_task(self):
        """Start the cleanup task for expired rate limit state."""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.config.cleanup_interval_seconds)
                    self._cleanup_expired_state()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Rate limit cleanup error: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    def stop_cleanup_task(self):
        """Stop the cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    async def check_connection_limit(self, ip_address: str) -> bool:
        """Check if IP address is within connection limits."""
        if not self.config.enabled:
            return True

        current_time = time.time()
        ip_state = self._ip_state[ip_address]

        # Initialize if first connection
        if ip_state.first_connection is None:
            ip_state.first_connection = current_time

        # Check IP connection limit
        if ip_state.connections >= self.config.max_connections_per_ip:
            logger.warning(f"IP connection limit exceeded for {ip_address}")
            return False

        return True

    def add_session(self, session) -> bool:
        """Add a session for rate limit tracking."""
        if not self.config.enabled:
            return True

        session_info = {
            "session_id": session.session_id,
            "ip_address": session.metadata.ip_address,
            "user_id": session.metadata.user_id,
            "tenant_id": session.metadata.tenant_id,
            "connected_at": time.time(),
        }

        self._active_sessions[session.session_id] = session_info

        # Update connection counts
        if session_info["ip_address"]:
            self._ip_state[session_info["ip_address"]].connections += 1

        if session_info["user_id"]:
            user_state = self._user_state[session_info["user_id"]]
            user_state.connections += 1

            # Check user connection limit
            if user_state.connections > self.config.max_connections_per_user:
                logger.warning(f"User connection limit exceeded for {session_info['user_id']}")
                return False

        if session_info["tenant_id"]:
            tenant_state = self._tenant_state[session_info["tenant_id"]]
            tenant_state.connections += 1

            # Check tenant connection limit
            if tenant_state.connections > self.config.max_connections_per_tenant:
                logger.warning(f"Tenant connection limit exceeded for {session_info['tenant_id']}")
                return False

        return True

    def remove_session(self, session):
        """Remove a session from rate limit tracking."""
        if not self.config.enabled:
            return

        session_info = self._active_sessions.pop(session.session_id, None)
        if not session_info:
            return

        # Update connection counts
        if session_info["ip_address"]:
            ip_state = self._ip_state.get(session_info["ip_address"])
            if ip_state:
                ip_state.connections = max(0, ip_state.connections - 1)

        if session_info["user_id"]:
            user_state = self._user_state.get(session_info["user_id"])
            if user_state:
                user_state.connections = max(0, user_state.connections - 1)

        if session_info["tenant_id"]:
            tenant_state = self._tenant_state.get(session_info["tenant_id"])
            if tenant_state:
                tenant_state.connections = max(0, tenant_state.connections - 1)

    async def check_message_rate(self, session) -> bool:
        """Check if session is within message rate limits."""
        if not self.config.enabled:
            return True

        current_time = time.time()
        session_id = session.session_id

        # Get session rate limit state
        session_state = self._session_state[session_id]

        # Add burst tokens (token bucket refill)
        refill_rate = self.config.burst_size / 60.0  # tokens per second
        session_state.add_burst_token(current_time, refill_rate, self.config.burst_size)

        # Try to consume a burst token first
        if session_state.consume_burst_token():
            return True

        # Check sliding window rate limit
        window_seconds = 60  # 1 minute window
        if session_state.add_message(current_time, window_seconds, self.config.messages_per_minute):
            return True

        # Also check user-level rate limits if authenticated
        if session.user_id:
            user_state = self._user_state[session.user_id]
            user_state.add_burst_token(current_time, refill_rate, self.config.burst_size)

            if not user_state.consume_burst_token():
                if not user_state.add_message(
                    current_time, window_seconds, self.config.messages_per_minute
                ):
                    logger.warning(f"User message rate limit exceeded for {session.user_id}")
                    return False

        # Check tenant-level rate limits
        if session.tenant_id:
            tenant_state = self._tenant_state[session.tenant_id]
            tenant_limit = self.config.messages_per_minute * 10  # Higher limit for tenant

            if not tenant_state.add_message(current_time, window_seconds, tenant_limit):
                logger.warning(f"Tenant message rate limit exceeded for {session.tenant_id}")
                return False

        logger.warning(f"Session message rate limit exceeded for {session_id}")
        return False

    def _cleanup_expired_state(self):
        """Clean up expired rate limiting state."""
        current_time = time.time()
        cleanup_threshold = 300  # 5 minutes of inactivity

        # Clean IP state
        expired_ips = [
            ip
            for ip, state in self._ip_state.items()
            if (
                state.connections == 0
                and state.first_connection
                and current_time - state.first_connection > cleanup_threshold
            )
        ]
        for ip in expired_ips:
            del self._ip_state[ip]

        # Clean user state
        expired_users = [
            user_id
            for user_id, state in self._user_state.items()
            if state.connections == 0 and len(state.message_times) == 0
        ]
        for user_id in expired_users:
            del self._user_state[user_id]

        # Clean tenant state
        expired_tenants = [
            tenant_id
            for tenant_id, state in self._tenant_state.items()
            if state.connections == 0 and len(state.message_times) == 0
        ]
        for tenant_id in expired_tenants:
            del self._tenant_state[tenant_id]

        # Clean session state for inactive sessions
        active_session_ids = set(self._active_sessions.keys())
        expired_sessions = [
            session_id
            for session_id in self._session_state.keys()
            if session_id not in active_session_ids
        ]
        for session_id in expired_sessions:
            del self._session_state[session_id]

        if expired_ips or expired_users or expired_tenants or expired_sessions:
            logger.debug(
                f"Rate limit cleanup: {len(expired_ips)} IPs, "
                f"{len(expired_users)} users, {len(expired_tenants)} tenants, "
                f"{len(expired_sessions)} sessions"
            )

    def get_rate_limit_status(self, session) -> dict[str, Any]:
        """Get current rate limit status for a session."""
        if not self.config.enabled:
            return {"rate_limiting": "disabled"}

        session_id = session.session_id
        time.time()

        status = {
            "enabled": True,
            "session": {
                "messages_in_window": len(self._session_state[session_id].message_times),
                "burst_tokens": self._session_state[session_id].burst_tokens,
                "limit": self.config.messages_per_minute,
            },
        }

        if session.user_id:
            user_state = self._user_state[session.user_id]
            status["user"] = {
                "connections": user_state.connections,
                "connection_limit": self.config.max_connections_per_user,
                "messages_in_window": len(user_state.message_times),
                "burst_tokens": user_state.burst_tokens,
            }

        if session.tenant_id:
            tenant_state = self._tenant_state[session.tenant_id]
            status["tenant"] = {
                "connections": tenant_state.connections,
                "connection_limit": self.config.max_connections_per_tenant,
            }

        if session.metadata.ip_address:
            ip_state = self._ip_state[session.metadata.ip_address]
            status["ip"] = {
                "connections": ip_state.connections,
                "connection_limit": self.config.max_connections_per_ip,
            }

        return status

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiting statistics."""
        if not self.config.enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "config": {
                "max_connections_per_ip": self.config.max_connections_per_ip,
                "max_connections_per_user": self.config.max_connections_per_user,
                "max_connections_per_tenant": self.config.max_connections_per_tenant,
                "messages_per_minute": self.config.messages_per_minute,
                "burst_size": self.config.burst_size,
            },
            "state": {
                "tracked_ips": len(self._ip_state),
                "tracked_users": len(self._user_state),
                "tracked_tenants": len(self._tenant_state),
                "active_sessions": len(self._active_sessions),
            },
        }
