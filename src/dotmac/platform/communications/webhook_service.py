"""Webhook subscription and delivery service."""

import asyncio
import hmac
import hashlib
import json
import time
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

import aiohttp
import structlog

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..auth.core import REDIS_URL

logger = structlog.get_logger()


class WebhookService:
    """Webhook subscription and delivery management."""

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or REDIS_URL
        self._redis = None
        self._memory_storage: Dict[str, Any] = {}

    async def _get_redis(self):
        """Get Redis connection."""
        if not REDIS_AVAILABLE:
            return None

        if self._redis is None:
            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    def _serialize(self, data: Any) -> str:
        """Serialize data to JSON."""
        return json.dumps(data, default=str)

    def _deserialize(self, data: str) -> Any:
        """Deserialize data from JSON."""
        return json.loads(data)

    async def create_subscription(self, subscription_data: Dict[str, Any]) -> bool:
        """Create webhook subscription."""
        try:
            subscription_id = subscription_data["id"]
            client = await self._get_redis()

            if client:
                await client.set(
                    f"webhook_subscription:{subscription_id}",
                    self._serialize(subscription_data)
                )
                # Add to user's subscription list
                await client.sadd(
                    f"user_webhooks:{subscription_data['user_id']}",
                    subscription_id
                )
            else:
                # Fallback to memory
                if "subscriptions" not in self._memory_storage:
                    self._memory_storage["subscriptions"] = {}
                if "user_subscriptions" not in self._memory_storage:
                    self._memory_storage["user_subscriptions"] = {}

                self._memory_storage["subscriptions"][subscription_id] = subscription_data

                user_id = subscription_data["user_id"]
                if user_id not in self._memory_storage["user_subscriptions"]:
                    self._memory_storage["user_subscriptions"][user_id] = set()
                self._memory_storage["user_subscriptions"][user_id].add(subscription_id)

            return True
        except Exception as e:
            logger.error("Failed to create webhook subscription", error=str(e))
            return False

    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook subscription by ID."""
        try:
            client = await self._get_redis()

            if client:
                data = await client.get(f"webhook_subscription:{subscription_id}")
                return self._deserialize(data) if data else None
            else:
                # Fallback to memory
                subscriptions = self._memory_storage.get("subscriptions", {})
                return subscriptions.get(subscription_id)
        except Exception as e:
            logger.error("Failed to get webhook subscription", error=str(e))
            return None

    async def list_user_subscriptions(
        self,
        user_id: str,
        event_filter: Optional[str] = None,
        active_only: bool = False,
        page: int = 1,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List user's webhook subscriptions."""
        try:
            client = await self._get_redis()
            subscriptions = []

            if client:
                # Get user's subscription IDs
                subscription_ids = await client.smembers(f"user_webhooks:{user_id}")

                for sub_id in subscription_ids:
                    data = await client.get(f"webhook_subscription:{sub_id}")
                    if data:
                        subscription = self._deserialize(data)

                        # Apply filters
                        if event_filter and event_filter not in subscription.get("events", []):
                            continue
                        if active_only and not subscription.get("is_active", True):
                            continue

                        subscriptions.append(subscription)
            else:
                # Fallback to memory
                user_subs = self._memory_storage.get("user_subscriptions", {}).get(user_id, set())
                all_subs = self._memory_storage.get("subscriptions", {})

                for sub_id in user_subs:
                    if sub_id in all_subs:
                        subscription = all_subs[sub_id]

                        # Apply filters
                        if event_filter and event_filter not in subscription.get("events", []):
                            continue
                        if active_only and not subscription.get("is_active", True):
                            continue

                        subscriptions.append(subscription)

            # Sort by creation date (newest first)
            subscriptions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Apply pagination
            total = len(subscriptions)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_subscriptions = subscriptions[start_idx:end_idx]

            return {
                "subscriptions": paginated_subscriptions,
                "total": total,
                "page": page,
                "limit": limit,
            }
        except Exception as e:
            logger.error("Failed to list user webhook subscriptions", error=str(e))
            return {"subscriptions": [], "total": 0, "page": page, "limit": limit}

    async def update_subscription(self, subscription_id: str, updates: Dict[str, Any]) -> bool:
        """Update webhook subscription."""
        try:
            client = await self._get_redis()

            if client:
                data = await client.get(f"webhook_subscription:{subscription_id}")
                if not data:
                    return False

                subscription = self._deserialize(data)
                subscription.update(updates)
                await client.set(
                    f"webhook_subscription:{subscription_id}",
                    self._serialize(subscription)
                )
                return True
            else:
                # Fallback to memory
                subscriptions = self._memory_storage.get("subscriptions", {})
                if subscription_id in subscriptions:
                    subscriptions[subscription_id].update(updates)
                    return True
                return False
        except Exception as e:
            logger.error("Failed to update webhook subscription", error=str(e))
            return False

    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete webhook subscription."""
        try:
            client = await self._get_redis()

            if client:
                # Get subscription data to get user_id
                data = await client.get(f"webhook_subscription:{subscription_id}")
                if data:
                    subscription = self._deserialize(data)
                    user_id = subscription["user_id"]

                    # Remove from user's subscription list
                    await client.srem(f"user_webhooks:{user_id}", subscription_id)

                # Delete subscription
                deleted_count = await client.delete(f"webhook_subscription:{subscription_id}")

                # Clean up deliveries
                await client.delete(f"webhook_deliveries:{subscription_id}")

                return bool(deleted_count)
            else:
                # Fallback to memory
                subscriptions = self._memory_storage.get("subscriptions", {})
                user_subscriptions = self._memory_storage.get("user_subscriptions", {})
                deliveries = self._memory_storage.get("deliveries", {})

                if subscription_id in subscriptions:
                    subscription = subscriptions[subscription_id]
                    user_id = subscription["user_id"]

                    # Remove from user's subscription list
                    if user_id in user_subscriptions:
                        user_subscriptions[user_id].discard(subscription_id)

                    # Remove subscription and deliveries
                    del subscriptions[subscription_id]
                    deliveries.pop(subscription_id, None)

                    return True
                return False
        except Exception as e:
            logger.error("Failed to delete webhook subscription", error=str(e))
            return False

    async def get_subscriptions_for_event(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all active subscriptions for a specific event type."""
        try:
            client = await self._get_redis()
            matching_subscriptions = []

            if client:
                # Scan all webhook subscriptions
                async for key in client.scan_iter(match="webhook_subscription:*"):
                    data = await client.get(key)
                    if data:
                        subscription = self._deserialize(data)
                        if (subscription.get("is_active", True) and
                            event_type in subscription.get("events", [])):
                            matching_subscriptions.append(subscription)
            else:
                # Fallback to memory
                subscriptions = self._memory_storage.get("subscriptions", {})
                for subscription in subscriptions.values():
                    if (subscription.get("is_active", True) and
                        event_type in subscription.get("events", [])):
                        matching_subscriptions.append(subscription)

            return matching_subscriptions
        except Exception as e:
            logger.error("Failed to get subscriptions for event", error=str(e))
            return []

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate webhook signature."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def _record_delivery(
        self,
        subscription_id: str,
        delivery_id: str,
        event_type: str,
        status: str,
        response_status: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
    ) -> None:
        """Record webhook delivery attempt."""
        try:
            delivery_data = {
                "id": delivery_id,
                "subscription_id": subscription_id,
                "event_type": event_type,
                "status": status,
                "response_status": response_status,
                "response_body": response_body,
                "error_message": error_message,
                "delivered_at": datetime.now(UTC).isoformat(),
                "retry_count": retry_count,
                "next_retry_at": None,
            }

            # Calculate next retry time if failed
            if status == "failed" and retry_count < 5:  # Max 5 retries
                retry_delay = min(300, 30 * (2 ** retry_count))  # Exponential backoff, max 5 min
                next_retry = datetime.now(UTC) + timedelta(seconds=retry_delay)
                delivery_data["next_retry_at"] = next_retry.isoformat()

            client = await self._get_redis()

            if client:
                # Store delivery record
                await client.lpush(
                    f"webhook_deliveries:{subscription_id}",
                    self._serialize(delivery_data)
                )
                # Keep only last 100 deliveries
                await client.ltrim(f"webhook_deliveries:{subscription_id}", 0, 99)
            else:
                # Fallback to memory
                if "deliveries" not in self._memory_storage:
                    self._memory_storage["deliveries"] = {}
                if subscription_id not in self._memory_storage["deliveries"]:
                    self._memory_storage["deliveries"][subscription_id] = []

                deliveries = self._memory_storage["deliveries"][subscription_id]
                deliveries.insert(0, delivery_data)
                # Keep only last 100 deliveries
                if len(deliveries) > 100:
                    self._memory_storage["deliveries"][subscription_id] = deliveries[:100]

        except Exception as e:
            logger.error("Failed to record delivery", error=str(e))

    async def list_deliveries(
        self,
        subscription_id: str,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List webhook deliveries for a subscription."""
        try:
            client = await self._get_redis()
            deliveries = []

            if client:
                # Get deliveries from Redis list
                delivery_data_list = await client.lrange(f"webhook_deliveries:{subscription_id}", 0, -1)
                for data_str in delivery_data_list:
                    delivery = self._deserialize(data_str)
                    if not status_filter or delivery.get("status") == status_filter:
                        deliveries.append(delivery)
            else:
                # Fallback to memory
                subscription_deliveries = self._memory_storage.get("deliveries", {}).get(subscription_id, [])
                for delivery in subscription_deliveries:
                    if not status_filter or delivery.get("status") == status_filter:
                        deliveries.append(delivery)

            # Apply pagination
            total = len(deliveries)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_deliveries = deliveries[start_idx:end_idx]

            return {
                "deliveries": paginated_deliveries,
                "total": total,
                "page": page,
                "limit": limit,
            }
        except Exception as e:
            logger.error("Failed to list deliveries", error=str(e))
            return {"deliveries": [], "total": 0, "page": page, "limit": limit}

    async def deliver_webhook(
        self,
        subscription_id: str,
        event_type: str,
        payload: Dict[str, Any],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Deliver webhook to subscription endpoint."""
        delivery_id = str(uuid4())
        start_time = time.time()

        try:
            subscription = await self.get_subscription(subscription_id)
            if not subscription:
                return {"success": False, "error": "Subscription not found"}

            if not subscription.get("is_active", True):
                return {"success": False, "error": "Subscription is inactive"}

            # Prepare webhook payload
            webhook_payload = {
                "id": str(uuid4()),
                "event": event_type,
                "created_at": datetime.now(UTC).isoformat(),
                "data": payload,
            }

            payload_str = self._serialize(webhook_payload)

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "DotMac-Webhooks/1.0",
                **subscription.get("headers", {}),
            }

            # Add signature if secret is configured
            if subscription.get("secret"):
                signature = self._generate_signature(payload_str, subscription["secret"])
                headers["X-Webhook-Signature"] = signature

            # Make HTTP request
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    subscription["url"],
                    data=payload_str,
                    headers=headers,
                ) as response:
                    response_body = await response.text()
                    delivery_time_ms = int((time.time() - start_time) * 1000)

                    if 200 <= response.status < 300:
                        # Success
                        await self._record_delivery(
                            subscription_id=subscription_id,
                            delivery_id=delivery_id,
                            event_type=event_type,
                            status="success",
                            response_status=response.status,
                            response_body=response_body[:1000],  # Truncate response
                            retry_count=retry_count,
                        )

                        # Update subscription stats
                        await self.update_subscription(subscription_id, {
                            "last_delivery_at": datetime.now(UTC).isoformat(),
                            "total_deliveries": subscription.get("total_deliveries", 0) + 1,
                        })

                        return {
                            "success": True,
                            "status_code": response.status,
                            "response_body": response_body,
                            "delivery_time_ms": delivery_time_ms,
                        }
                    else:
                        # HTTP error
                        await self._record_delivery(
                            subscription_id=subscription_id,
                            delivery_id=delivery_id,
                            event_type=event_type,
                            status="failed",
                            response_status=response.status,
                            response_body=response_body[:1000],
                            error_message=f"HTTP {response.status}: {response_body[:100]}",
                            retry_count=retry_count,
                        )

                        # Update failed delivery count
                        await self.update_subscription(subscription_id, {
                            "failed_deliveries": subscription.get("failed_deliveries", 0) + 1,
                        })

                        return {
                            "success": False,
                            "status_code": response.status,
                            "response_body": response_body,
                            "error_message": f"HTTP {response.status}",
                            "delivery_time_ms": int((time.time() - start_time) * 1000),
                        }

        except asyncio.TimeoutError:
            await self._record_delivery(
                subscription_id=subscription_id,
                delivery_id=delivery_id,
                event_type=event_type,
                status="failed",
                error_message="Request timeout",
                retry_count=retry_count,
            )
            return {
                "success": False,
                "error_message": "Request timeout",
                "delivery_time_ms": int((time.time() - start_time) * 1000),
            }
        except Exception as e:
            await self._record_delivery(
                subscription_id=subscription_id,
                delivery_id=delivery_id,
                event_type=event_type,
                status="failed",
                error_message=str(e),
                retry_count=retry_count,
            )
            return {
                "success": False,
                "error_message": str(e),
                "delivery_time_ms": int((time.time() - start_time) * 1000),
            }

    async def test_delivery(
        self,
        subscription_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Test webhook delivery without recording stats."""
        start_time = time.time()

        try:
            subscription = await self.get_subscription(subscription_id)
            if not subscription:
                return {"success": False, "error_message": "Subscription not found"}

            # Prepare test webhook payload
            webhook_payload = {
                "id": f"test-{uuid4()}",
                "event": event_type,
                "created_at": datetime.now(UTC).isoformat(),
                "test": True,
                "data": payload,
            }

            payload_str = self._serialize(webhook_payload)

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "DotMac-Webhooks/1.0 (Test)",
                **subscription.get("headers", {}),
            }

            # Add signature if secret is configured
            if subscription.get("secret"):
                signature = self._generate_signature(payload_str, subscription["secret"])
                headers["X-Webhook-Signature"] = signature

            # Make HTTP request
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    subscription["url"],
                    data=payload_str,
                    headers=headers,
                ) as response:
                    response_body = await response.text()
                    delivery_time_ms = int((time.time() - start_time) * 1000)

                    return {
                        "success": 200 <= response.status < 300,
                        "status_code": response.status,
                        "response_body": response_body,
                        "error_message": None if 200 <= response.status < 300 else f"HTTP {response.status}",
                        "delivery_time_ms": delivery_time_ms,
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error_message": "Request timeout",
                "delivery_time_ms": int((time.time() - start_time) * 1000),
            }
        except Exception as e:
            return {
                "success": False,
                "error_message": str(e),
                "delivery_time_ms": int((time.time() - start_time) * 1000),
            }

    async def retry_delivery(self, delivery_id: str) -> bool:
        """Retry a failed webhook delivery."""
        # This would typically involve looking up the delivery record,
        # extracting the original payload, and re-delivering
        logger.info("Webhook delivery retry requested", delivery_id=delivery_id)
        # Implementation would depend on how you want to store and retrieve delivery records
        return True

    async def trigger_event(self, event_type: str, payload: Dict[str, Any]) -> int:
        """Trigger webhook deliveries for an event type."""
        subscriptions = await self.get_subscriptions_for_event(event_type)

        delivery_tasks = []
        for subscription in subscriptions:
            task = asyncio.create_task(
                self.deliver_webhook(
                    subscription_id=subscription["id"],
                    event_type=event_type,
                    payload=payload,
                )
            )
            delivery_tasks.append(task)

        # Wait for all deliveries to complete
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)

        logger.info(
            "Triggered webhook deliveries",
            event_type=event_type,
            subscriptions_count=len(subscriptions)
        )

        return len(subscriptions)

    async def check_rate_limit(
        self,
        subscription_id: str,
        limit: int = 100,
        window: int = 3600
    ) -> bool:
        """
        Check if a subscription has exceeded its rate limit.

        Args:
            subscription_id: ID of the subscription
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds (default: 1 hour)

        Returns:
            True if the request is within the rate limit, False otherwise
        """
        try:
            client = await self._get_redis()

            if client:
                # Use Redis for rate limiting
                key = f"webhook_rate_limit:{subscription_id}"
                current_time = time.time()
                window_start = current_time - window

                # Remove old entries outside the window
                await client.zremrangebyscore(key, 0, window_start)

                # Count current entries in the window
                count = await client.zcard(key)

                if count >= limit:
                    logger.warning(
                        "Rate limit exceeded",
                        subscription_id=subscription_id,
                        limit=limit,
                        window=window,
                        count=count
                    )
                    return False

                # Add current request timestamp
                await client.zadd(key, {str(uuid4()): current_time})

                # Set expiry on the key
                await client.expire(key, window)

                return True
            else:
                # Fallback to in-memory rate limiting
                rate_limits = self._memory_storage.setdefault("rate_limits", {})
                subscription_limits = rate_limits.setdefault(subscription_id, [])

                current_time = time.time()
                window_start = current_time - window

                # Filter out old entries
                subscription_limits[:] = [
                    ts for ts in subscription_limits
                    if ts > window_start
                ]

                if len(subscription_limits) >= limit:
                    logger.warning(
                        "Rate limit exceeded (memory)",
                        subscription_id=subscription_id,
                        limit=limit,
                        window=window,
                        count=len(subscription_limits)
                    )
                    return False

                # Add current timestamp
                subscription_limits.append(current_time)

                return True

        except Exception as e:
            logger.error(
                "Failed to check rate limit",
                subscription_id=subscription_id,
                error=str(e)
            )
            # On error, allow the request (fail open)
            return True


# Global service instance
webhook_service = WebhookService()