"""Factory functions for creating API Gateway instances."""


from typing import Optional
from fastapi import FastAPI
from .gateway import APIGateway
from .config import GatewayConfig, GatewayMode
from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

def create_gateway(mode: str = "development") -> APIGateway:
    """
    Create an API Gateway instance based on mode.

    Args:
        mode: One of "development", "staging", or "production"

    Returns:
        Configured APIGateway instance
    """
    logger.info(f"Creating API Gateway in {mode} mode")
    if mode == "development":
        config = GatewayConfig.for_development()
    elif mode == "production":
        config = GatewayConfig.for_production()
    else:
        # Default/staging config
        config = GatewayConfig(mode=GatewayMode.STAGING)

    logger.debug(f"Gateway configuration: {config.mode}, port={config.port}")
    return APIGateway(config)

def setup_gateway_app(
    app: FastAPI, mode: str = "development", config: Optional[GatewayConfig] = None
) -> APIGateway:
    """
    Setup FastAPI app with API Gateway.

    Args:
        app: FastAPI application instance
        mode: Operating mode
        config: Optional custom configuration

    Returns:
        Configured APIGateway instance

    Example:
        ```python
        from fastapi import FastAPI
        from dotmac.platform.api_gateway.factory import setup_gateway_app

        app = FastAPI()
        gateway = setup_gateway_app(app, mode="production")
        ```
    """
    if config:
        logger.info("Setting up gateway with custom configuration")
        gateway = APIGateway(config)
    else:
        logger.info(f"Setting up gateway in {mode} mode")
        gateway = create_gateway(mode)

    gateway.setup(app)
    logger.info("API Gateway setup completed")
    return gateway
