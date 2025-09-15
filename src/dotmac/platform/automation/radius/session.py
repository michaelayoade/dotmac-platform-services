"""
RADIUS session management.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Optional

from .types import RADIUSSession, RADIUSSessionStatus

logger = logging.getLogger(__name__)


class RADIUSSessionManager:
    """
    RADIUS session lifecycle management.

    Manages active RADIUS sessions, tracking, and cleanup.
    """

    def __init__(self):
        self._sessions: dict[str, RADIUSSession] = {}
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start session manager."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("RADIUS session manager started")

    async def stop(self):
        """Stop session manager."""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("RADIUS session manager stopped")

    async def create_session(self, session: RADIUSSession) -> RADIUSSession:
        """Create new RADIUS session."""
        self._sessions[session.session_id] = session
        logger.info(
            f"Created RADIUS session {session.session_id} for user {session.username}"
        )
        return session

    async def update_session(self, session: RADIUSSession):
        """Update existing session."""
        if session.session_id in self._sessions:
            self._sessions[session.session_id] = session
            logger.debug(f"Updated RADIUS session {session.session_id}")

    async def remove_session(self, session_id: str) -> bool:
        """Remove session."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            del self._sessions[session_id]
            logger.info(
                f"Removed RADIUS session {session_id} for user {session.username}"
            )
            return True
        return False

    def get_session(self, session_id: str) -> Optional[RADIUSSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_user_sessions(self, username: str) -> list[RADIUSSession]:
        """Get all sessions for user."""
        return [s for s in self._sessions.values() if s.username == username]

    def get_active_sessions(self) -> list[RADIUSSession]:
        """Get all active sessions."""
        return [
            s for s in self._sessions.values() if s.status == RADIUSSessionStatus.ACTIVE
        ]

    async def _cleanup_loop(self):
        """Background session cleanup task."""
        while self._running:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(10)

    async def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now(UTC)
        expired_sessions = []

        for session in self._sessions.values():
            # Check for session timeout
            if (
                session.session_timeout
                and session.session_time > session.session_timeout
            ):
                expired_sessions.append(session.session_id)
                continue

            # Check for idle timeout
            if session.idle_timeout:
                idle_time = (now - session.last_update).total_seconds()
                if idle_time > session.idle_timeout:
                    expired_sessions.append(session.session_id)

        for session_id in expired_sessions:
            await self.remove_session(session_id)
