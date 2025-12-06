"""
Automatic geocoding for customer addresses.

Provides functionality to geocode customer service addresses
and cache the results for future lookups.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


async def geocode_customer_address(
    customer_data: dict[str, Any],
    force: bool = False,
) -> dict[str, float] | None:
    """
    Geocode a customer's service address.

    Args:
        customer_data: Dictionary containing address fields:
            - service_address_line1
            - service_city
            - service_state_province
            - service_postal_code
            - service_country
            - service_coordinates (existing coordinates if any)
        force: If True, re-geocode even if coordinates exist

    Returns:
        Dictionary with lat/lon coordinates, or None if geocoding fails:
        {"lat": float, "lon": float}
    """
    # Check if we already have coordinates and force is False
    existing_coords = customer_data.get("service_coordinates", {})
    if not force and existing_coords.get("lat") and existing_coords.get("lon"):
        return existing_coords

    # Build address string from components
    address_parts = []
    if customer_data.get("service_address_line1"):
        address_parts.append(customer_data["service_address_line1"])
    if customer_data.get("service_city"):
        address_parts.append(customer_data["service_city"])
    if customer_data.get("service_state_province"):
        address_parts.append(customer_data["service_state_province"])
    if customer_data.get("service_postal_code"):
        address_parts.append(customer_data["service_postal_code"])
    if customer_data.get("service_country"):
        address_parts.append(customer_data["service_country"])

    if not address_parts:
        logger.debug("No address components provided for geocoding")
        return None

    address_string = ", ".join(address_parts)

    # TODO: Implement actual geocoding using a service like:
    # - Google Maps Geocoding API
    # - OpenStreetMap Nominatim
    # - Mapbox Geocoding API
    # For now, return None to indicate geocoding is not configured
    logger.debug(
        "Geocoding not configured",
        address=address_string,
    )

    return None
