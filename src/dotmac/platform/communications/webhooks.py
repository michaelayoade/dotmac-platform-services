"""Webhook delivery helpers for the communications package."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any, Mapping, MutableMapping, Optional
from uuid import uuid4

from dotmac.platform.observability.logging import get_logger
from dotmac.platform.observability.unified_logging import get_logger

from .notifications.task_notifications import WebhookProvider

logger = get_logger(__name__)

def _serialize_payload(payload: Any, content_type: str) -> Optional[str]:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    if content_type == "application/json":
        try:
            return json.dumps(payload)
        except TypeError:
            logger.warning("Failed to JSON serialize payload; using str() fallback")
            return json.dumps(str(payload))
    return str(payload)

class WebhookClient:
    """Lightweight wrapper around the internal webhook provider."""

    def __init__(
        self,
        *,
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        self._provider = WebhookProvider(timeout=timeout, verify_ssl=verify_ssl)

    async def send(
        self,
        url: str,
        payload: Any = None,
        *,
        subject: Optional[str] = None,
        metadata: Optional[MutableMapping[str, Any]] = None,
        context: Optional[Mapping[str, Any]] = None,
        content_type: str = "application/json",
    ) -> bool:
        body = _serialize_payload(payload, content_type)
        request = SimpleNamespace(
            notification_id=str(uuid4()),
            recipient=url,
            subject=subject,
            body=body,
            content_type=content_type,
            context=dict(context or {}),
            metadata=dict(metadata or {}),
        )
        success = await self._provider.send_notification(request)
        if not success:
            logger.error("Webhook delivery failed", extra={"webhook_url": url})
        return success

    def send_sync(self, *args: Any, **kwargs: Any) -> bool:
        return asyncio.run(self.send(*args, **kwargs))

async def send_webhook_notification(
    url: str,
    payload: Any = None,
    *,
    subject: Optional[str] = None,
    metadata: Optional[MutableMapping[str, Any]] = None,
    context: Optional[Mapping[str, Any]] = None,
    content_type: str = "application/json",
    timeout: int = 30,
    verify_ssl: bool = True,
) -> bool:
    client = WebhookClient(timeout=timeout, verify_ssl=verify_ssl)
    return await client.send(
        url,
        payload,
        subject=subject,
        metadata=metadata,
        context=context,
        content_type=content_type,
    )

def send_webhook_notification_sync(*args: Any, **kwargs: Any) -> bool:
    return asyncio.run(send_webhook_notification(*args, **kwargs))

__all__ = [
    "WebhookClient",
    "send_webhook_notification",
    "send_webhook_notification_sync",
]
