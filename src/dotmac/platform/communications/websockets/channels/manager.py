"""
Concrete implementation of channel manager.
"""

import asyncio

from typing import Any, Optional

from .abstractions import Channel, ChannelManager, ChannelMetadata

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class ConcreteChannel(Channel):
    """Concrete implementation of a channel."""

    def __init__(self, name: str, session_manager, metadata: Optional[ChannelMetadata] = None):
        super().__init__(name, metadata)
        self.session_manager = session_manager

    async def broadcast(
        self, message_type: str, data: Any, exclude_session: Optional[str] = None
    ) -> int:
        """Broadcast message to all subscribers."""
        success_count = 0

        # Add to message history
        await self.add_message(message_type, data)

        # Send to all subscribers
        for session_id in self._subscribers.copy():  # Copy to avoid modification during iteration
            if exclude_session and session_id == exclude_session:
                continue

            session = self.session_manager.get_session(session_id)
            if session:
                try:
                    if await session.send_message(message_type, data):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error sending to session {session_id}: {e}")
                    # Remove failed session from subscribers
                    await self.unsubscribe(session_id)
            else:
                # Session no longer exists, remove from subscribers
                await self.unsubscribe(session_id)

        return success_count

class ConcreteChannelManager(ChannelManager):
    """Concrete implementation of channel manager."""

    def __init__(self, config):
        self.config = config
        self.session_manager = None  # Will be set by gateway

        self._channels: dict[str, ConcreteChannel] = {}
        self._session_channels: dict[str, set[str]] = {}  # session_id -> channel_names

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    def set_session_manager(self, session_manager):
        """Set the session manager reference."""
        self.session_manager = session_manager

    async def start(self):
        """Start the channel manager."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the channel manager."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        """Periodically clean up empty channels."""
        while True:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                await self.cleanup_empty_channels()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Channel cleanup error: {e}")

    async def create_channel(
        self, name: str, metadata: Optional[ChannelMetadata] = None
    ) -> Channel:
        """Create a new channel."""
        if name in self._channels:
            return self._channels[name]

        if not metadata:
            metadata = ChannelMetadata(name=name)

        channel = ConcreteChannel(name, self.session_manager, metadata)
        self._channels[name] = channel

        logger.debug(f"Created channel: {name}")
        return channel

    async def get_channel(self, name: str) -> Optional[Channel]:
        """Get a channel by name."""
        return self._channels.get(name)

    async def get_or_create_channel(
        self, name: str, metadata: Optional[ChannelMetadata] = None
    ) -> Channel:
        """Get an existing channel or create a new one."""
        channel = await self.get_channel(name)
        if not channel:
            channel = await self.create_channel(name, metadata)
        return channel

    async def delete_channel(self, name: str) -> bool:
        """Delete a channel."""
        channel = self._channels.pop(name, None)
        if not channel:
            return False

        # Unsubscribe all sessions
        for session_id in list(channel.subscribers):
            await self.unsubscribe_session_by_id(session_id, name)

        logger.debug(f"Deleted channel: {name}")
        return True

    async def list_channels(self, tenant_id: Optional[str] = None) -> list[str]:
        """List all channels, optionally filtered by tenant."""
        if tenant_id:
            return [
                name
                for name, channel in self._channels.items()
                if channel.metadata.tenant_id == tenant_id
            ]
        return list(self._channels.keys())

    async def subscribe_session(self, session, channel_name: str) -> bool:
        """Subscribe a session to a channel."""
        # Apply tenant isolation if enabled
        if self.config.tenant_isolation_enabled and session.tenant_id:
            if not channel_name.startswith(f"tenant:{session.tenant_id}:"):
                # Auto-prefix with tenant
                channel_name = f"tenant:{session.tenant_id}:{channel_name}"

        # Get or create channel
        channel = await self.get_or_create_channel(channel_name)

        # Check access permissions
        if not await self._can_access_channel(session, channel):
            return False

        # Subscribe to channel
        success = await channel.subscribe(session.session_id)
        if success:
            # Track session subscriptions
            if session.session_id not in self._session_channels:
                self._session_channels[session.session_id] = set()
            self._session_channels[session.session_id].add(channel_name)

            # Add to session metadata
            session.metadata.channels.add(channel_name)

            # Send message history if available
            history = channel.get_message_history(10)  # Last 10 messages
            if history:
                await session.send_message(
                    "channel_history", {"channel": channel_name, "messages": history}
                )

        return success

    async def unsubscribe_session(self, session, channel_name: str) -> bool:
        """Unsubscribe a session from a channel."""
        return await self.unsubscribe_session_by_id(session.session_id, channel_name)

    async def unsubscribe_session_by_id(self, session_id: str, channel_name: str) -> bool:
        """Unsubscribe a session from a channel by session ID."""
        channel = await self.get_channel(channel_name)
        if not channel:
            return False

        success = await channel.unsubscribe(session_id)
        if success:
            # Remove from session tracking
            if session_id in self._session_channels:
                self._session_channels[session_id].discard(channel_name)
                if not self._session_channels[session_id]:
                    del self._session_channels[session_id]

            # Remove from session metadata if session still exists
            if self.session_manager:
                session = self.session_manager.get_session(session_id)
                if session:
                    session.metadata.channels.discard(channel_name)

        return success

    async def unsubscribe_session_from_all(self, session_id: str):
        """Unsubscribe a session from all channels."""
        channels = self._session_channels.get(session_id, set()).copy()
        for channel_name in channels:
            await self.unsubscribe_session_by_id(session_id, channel_name)

    async def broadcast_to_channel(
        self,
        channel_name: str,
        message_type: str,
        data: Any = None,
        exclude_session: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Broadcast message to all subscribers of a channel."""
        # Apply tenant isolation if specified
        if tenant_id and self.config.tenant_isolation_enabled:
            if not channel_name.startswith(f"tenant:{tenant_id}:"):
                channel_name = f"tenant:{tenant_id}:{channel_name}"

        channel = await self.get_channel(channel_name)
        if not channel:
            return 0

        return await channel.broadcast(message_type, data, exclude_session)

    async def get_channel_subscribers(self, channel_name: str) -> list[str]:
        """Get list of subscribers for a channel."""
        channel = await self.get_channel(channel_name)
        if channel:
            return list(channel.subscribers)
        return []

    async def get_session_channels(self, session_id: str) -> list[str]:
        """Get list of channels a session is subscribed to."""
        return list(self._session_channels.get(session_id, set()))

    async def _can_access_channel(self, session, channel: Channel) -> bool:
        """Check if session can access a channel."""
        metadata = channel.metadata

        # Public channels are always accessible
        if metadata.public:
            return True

        # Check authentication requirement
        if not session.is_authenticated:
            return False

        # Check tenant isolation
        if metadata.tenant_id and metadata.tenant_id != session.tenant_id:
            return False

        # Check required roles
        if metadata.required_roles:
            user_info = getattr(session, "user_info", None)
            if not user_info or not hasattr(user_info, "has_any_role"):
                return False
            if not user_info.has_any_role(metadata.required_roles):
                return False

        # Check required permissions
        if metadata.required_permissions:
            user_info = getattr(session, "user_info", None)
            if not user_info or not hasattr(user_info, "has_permission"):
                return False
            for permission in metadata.required_permissions:
                if not user_info.has_permission(permission):
                    return False

        return True

    async def cleanup_empty_channels(self):
        """Clean up empty channels that don't need to persist."""
        channels_to_delete = []

        for name, channel in self._channels.items():
            if channel.is_empty() and not channel.should_persist():
                channels_to_delete.append(name)

        for name in channels_to_delete:
            await self.delete_channel(name)

        if channels_to_delete:
            logger.debug(f"Cleaned up {len(channels_to_delete)} empty channels")

    def get_stats(self) -> dict[str, Any]:
        """Get channel manager statistics."""
        total_subscribers = sum(len(channel.subscribers) for channel in self._channels.values())

        channel_stats = {}
        for name, channel in self._channels.items():
            channel_stats[name] = {
                "subscribers": len(channel.subscribers),
                "total_messages": channel.metadata.total_messages,
                "peak_subscribers": channel.metadata.peak_subscribers,
                "created_at": channel.metadata.created_at,
                "last_activity": channel.metadata.last_activity,
            }

        return {
            "total_channels": len(self._channels),
            "total_subscribers": total_subscribers,
            "active_sessions_with_subscriptions": len(self._session_channels),
            "channels": channel_stats,
        }

    async def get_channel_info(self, channel_name: str) -> Optional[dict[str, Any]]:
        """Get detailed information about a channel."""
        channel = await self.get_channel(channel_name)
        if channel:
            return channel.to_dict()
        return None
