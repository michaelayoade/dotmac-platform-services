"""
Advanced broadcast utilities and patterns.
"""


import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from dotmac.platform.logging import get_logger
logger = get_logger(__name__)

class BroadcastScope(str, Enum):
    """Scope of broadcast operations."""

    SESSION = "session"  # Single session
    USER = "user"  # All sessions of a user
    TENANT = "tenant"  # All sessions in a tenant
    CHANNEL = "channel"  # All subscribers of a channel
    ROLE = "role"  # All users with a specific role
    PERMISSION = "permission"  # All users with a specific permission
    GLOBAL = "global"  # All connected sessions

@dataclass
class BroadcastTarget:
    """Target for broadcast operations."""

    scope: BroadcastScope
    identifier: str  # session_id, user_id, tenant_id, channel_name, role, permission

    # Optional filters
    exclude_sessions: set[str] = field(default_factory=set)
    include_only_sessions: Optional[set[str]] = None

    # Conditions
    require_authenticated: bool = False
    require_permissions: list[str] = field(default_factory=list)
    require_roles: list[str] = field(default_factory=list)

    # Tenant filtering
    tenant_id: Optional[str] = None

@dataclass
class BroadcastMessage:
    """Message for broadcast operations."""

    type: str
    data: Any = None

    # Message metadata
    sender_id: Optional[str] = None
    tenant_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    # Delivery options
    reliable: bool = False  # Ensure delivery or queue for retry
    ttl_seconds: Optional[int] = None  # Message expiration

    # Custom headers
    headers: dict[str, str] = field(default_factory=dict)

@dataclass
class BroadcastResult:
    """Result of broadcast operation."""

    target: BroadcastTarget
    message: BroadcastMessage

    # Results
    success: bool
    delivered_count: int = 0
    failed_count: int = 0
    filtered_count: int = 0  # Sessions filtered out by conditions

    # Error information
    errors: list[str] = field(default_factory=list)

    # Timing
    duration_ms: float = 0
    timestamp: float = field(default_factory=time.time)

class BroadcastManager:
    """Advanced broadcast manager with patterns and utilities."""

    def __init__(self, session_manager, channel_manager):
        self.session_manager = session_manager
        self.channel_manager = channel_manager

        # Broadcast interceptors and filters
        self._pre_broadcast_filters: list[
            Callable[[BroadcastTarget, BroadcastMessage], Awaitable[bool]]
        ] = []
        self._post_broadcast_handlers: list[Callable[[BroadcastResult], Awaitable[None]]] = []

        # Statistics
        self._stats = {
            "total_broadcasts": 0,
            "successful_broadcasts": 0,
            "failed_broadcasts": 0,
            "total_messages_sent": 0,
            "average_delivery_time_ms": 0.0,
        }

    def add_pre_broadcast_filter(
        self, filter_func: Callable[[BroadcastTarget, BroadcastMessage], Awaitable[bool]]
    ):
        """Add a pre-broadcast filter."""
        self._pre_broadcast_filters.append(filter_func)

    def add_post_broadcast_handler(self, handler: Callable[[BroadcastResult], Awaitable[None]]):
        """Add a post-broadcast handler."""
        self._post_broadcast_handlers.append(handler)

    async def broadcast(
        self, target: BroadcastTarget, message: BroadcastMessage
    ) -> BroadcastResult:
        """Perform broadcast operation."""
        start_time = time.time()

        result = BroadcastResult(target=target, message=message, success=False)

        try:
            # Apply pre-broadcast filters
            for filter_func in self._pre_broadcast_filters:
                try:
                    if not await filter_func(target, message):
                        result.errors.append("Blocked by pre-broadcast filter")
                        return result
                except Exception as e:
                    logger.error(f"Pre-broadcast filter error: {e}")
                    result.errors.append(f"Filter error: {e}")
                    return result

            # Get target sessions
            target_sessions = await self._resolve_target_sessions(target)

            # Apply session-level filtering
            filtered_sessions = await self._filter_sessions(target_sessions, target, message)
            result.filtered_count = len(target_sessions) - len(filtered_sessions)

            # Broadcast to filtered sessions
            delivered_count = 0
            failed_count = 0

            for session in filtered_sessions:
                try:
                    success = await session.send_message(message.type, message.data)
                    if success:
                        delivered_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error sending to session {session.session_id}: {e}")
                    failed_count += 1
                    result.errors.append(f"Session {session.session_id}: {e}")

            result.delivered_count = delivered_count
            result.failed_count = failed_count
            result.success = delivered_count > 0

            # Update statistics
            self._update_stats(result, start_time)

        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            result.errors.append(f"Broadcast error: {e}")

        finally:
            result.duration_ms = (time.time() - start_time) * 1000

            # Call post-broadcast handlers
            for handler in self._post_broadcast_handlers:
                try:
                    await handler(result)
                except Exception as e:
                    logger.error(f"Post-broadcast handler error: {e}")

        return result

    async def _resolve_target_sessions(self, target: BroadcastTarget) -> list:
        """Resolve target sessions based on broadcast scope."""
        sessions = []

        if target.scope == BroadcastScope.SESSION:
            session = self.session_manager.get_session(target.identifier)
            if session:
                sessions = [session]

        elif target.scope == BroadcastScope.USER:
            sessions = self.session_manager.get_user_sessions(target.identifier)

        elif target.scope == BroadcastScope.TENANT:
            sessions = self.session_manager.get_tenant_sessions(target.identifier)

        elif target.scope == BroadcastScope.CHANNEL:
            subscriber_ids = await self.channel_manager.get_channel_subscribers(target.identifier)
            sessions = [
                self.session_manager.get_session(sid)
                for sid in subscriber_ids
                if self.session_manager.get_session(sid)
            ]

        elif target.scope == BroadcastScope.ROLE:
            sessions = [
                session
                for session in self.session_manager.get_all_sessions()
                if (
                    session.is_authenticated
                    and hasattr(session, "user_info")
                    and hasattr(session.user_info, "has_role")
                    and session.user_info.has_role(target.identifier)
                )
            ]

        elif target.scope == BroadcastScope.PERMISSION:
            sessions = [
                session
                for session in self.session_manager.get_all_sessions()
                if (
                    session.is_authenticated
                    and hasattr(session, "user_info")
                    and hasattr(session.user_info, "has_permission")
                    and session.user_info.has_permission(target.identifier)
                )
            ]

        elif target.scope == BroadcastScope.GLOBAL:
            sessions = self.session_manager.get_all_sessions()

        return sessions

    async def _filter_sessions(
        self, sessions: list, target: BroadcastTarget, message: BroadcastMessage
    ) -> list:
        """Apply session-level filtering."""
        filtered_sessions = []

        for session in sessions:
            # Exclude specific sessions
            if session.session_id in target.exclude_sessions:
                continue

            # Include only specific sessions (if specified)
            if (
                target.include_only_sessions
                and session.session_id not in target.include_only_sessions
            ):
                continue

            # Authentication requirement
            if target.require_authenticated and not session.is_authenticated:
                continue

            # Tenant filtering
            if target.tenant_id and session.tenant_id != target.tenant_id:
                continue

            # Role requirements
            if target.require_roles:
                if (
                    not session.is_authenticated
                    or not hasattr(session, "user_info")
                    or not hasattr(session.user_info, "has_any_role")
                    or not session.user_info.has_any_role(target.require_roles)
                ):
                    continue

            # Permission requirements
            if target.require_permissions:
                if (
                    not session.is_authenticated
                    or not hasattr(session, "user_info")
                    or not hasattr(session.user_info, "has_permission")
                ):
                    continue

                has_all_permissions = all(
                    session.user_info.has_permission(perm) for perm in target.require_permissions
                )
                if not has_all_permissions:
                    continue

            filtered_sessions.append(session)

        return filtered_sessions

    def _update_stats(self, result: BroadcastResult, start_time: float):
        """Update broadcast statistics."""
        self._stats["total_broadcasts"] += 1

        if result.success:
            self._stats["successful_broadcasts"] += 1
        else:
            self._stats["failed_broadcasts"] += 1

        self._stats["total_messages_sent"] += result.delivered_count

        # Update average delivery time
        current_avg = self._stats["average_delivery_time_ms"]
        total_broadcasts = self._stats["total_broadcasts"]
        new_time = result.duration_ms

        self._stats["average_delivery_time_ms"] = (
            current_avg * (total_broadcasts - 1) + new_time
        ) / total_broadcasts

    # Convenience methods for common broadcast patterns

    async def broadcast_to_user(
        self,
        user_id: str,
        message_type: str,
        data: Any = None,
        exclude_sessions: Optional[set[str]] = None,
    ) -> BroadcastResult:
        """Broadcast to all sessions of a user."""
        target = BroadcastTarget(
            scope=BroadcastScope.USER,
            identifier=user_id,
            exclude_sessions=exclude_sessions or set(),
        )
        message = BroadcastMessage(type=message_type, data=data)
        return await self.broadcast(target, message)

    async def broadcast_to_tenant(
        self,
        tenant_id: str,
        message_type: str,
        data: Any = None,
        require_authenticated: bool = True,
    ) -> BroadcastResult:
        """Broadcast to all sessions in a tenant."""
        target = BroadcastTarget(
            scope=BroadcastScope.TENANT,
            identifier=tenant_id,
            require_authenticated=require_authenticated,
        )
        message = BroadcastMessage(type=message_type, data=data, tenant_id=tenant_id)
        return await self.broadcast(target, message)

    async def broadcast_to_channel(
        self,
        channel_name: str,
        message_type: str,
        data: Any = None,
        exclude_session: Optional[str] = None,
    ) -> BroadcastResult:
        """Broadcast to all subscribers of a channel."""
        target = BroadcastTarget(
            scope=BroadcastScope.CHANNEL,
            identifier=channel_name,
            exclude_sessions={exclude_session} if exclude_session else set(),
        )
        message = BroadcastMessage(type=message_type, data=data)
        return await self.broadcast(target, message)

    async def broadcast_to_role(
        self, role: str, message_type: str, data: Any = None, tenant_id: Optional[str] = None
    ) -> BroadcastResult:
        """Broadcast to all users with a specific role."""
        target = BroadcastTarget(
            scope=BroadcastScope.ROLE,
            identifier=role,
            tenant_id=tenant_id,
            require_authenticated=True,
        )
        message = BroadcastMessage(type=message_type, data=data, tenant_id=tenant_id)
        return await self.broadcast(target, message)

    async def broadcast_to_permission(
        self, permission: str, message_type: str, data: Any = None, tenant_id: Optional[str] = None
    ) -> BroadcastResult:
        """Broadcast to all users with a specific permission."""
        target = BroadcastTarget(
            scope=BroadcastScope.PERMISSION,
            identifier=permission,
            tenant_id=tenant_id,
            require_authenticated=True,
        )
        message = BroadcastMessage(type=message_type, data=data, tenant_id=tenant_id)
        return await self.broadcast(target, message)

    async def broadcast_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        targets: list[BroadcastTarget],
        priority: str = "normal",
        actions: Optional[list[dict[str, Any]]] = None,
    ) -> list[BroadcastResult]:
        """Broadcast a notification to multiple targets."""
        notification_data = {
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "priority": priority,
            "timestamp": time.time(),
        }

        if actions:
            notification_data["actions"] = actions

        broadcast_message = BroadcastMessage(type="notification", data=notification_data)

        results = []
        for target in targets:
            result = await self.broadcast(target, broadcast_message)
            results.append(result)

        return results

    async def broadcast_system_message(
        self, message: str, level: str = "info", tenant_id: Optional[str] = None
    ) -> BroadcastResult:
        """Broadcast a system message."""
        target = BroadcastTarget(
            scope=BroadcastScope.TENANT if tenant_id else BroadcastScope.GLOBAL,
            identifier=tenant_id or "global",
            tenant_id=tenant_id,
        )

        message_data = {
            "message": message,
            "level": level,
            "source": "system",
            "timestamp": time.time(),
        }

        broadcast_message = BroadcastMessage(
            type="system_message", data=message_data, tenant_id=tenant_id
        )

        return await self.broadcast(target, broadcast_message)

    def get_stats(self) -> dict[str, Any]:
        """Get broadcast manager statistics."""
        return {
            **self._stats,
            "pre_broadcast_filters": len(self._pre_broadcast_filters),
            "post_broadcast_handlers": len(self._post_broadcast_handlers),
        }
