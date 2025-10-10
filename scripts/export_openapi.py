"""Utility script to export the API Gateway OpenAPI schema to a JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotmac.platform.api_gateway.gateway import APIGateway
from fastapi import FastAPI

from dotmac.platform.settings import settings

DEFAULT_OUTPUT = Path("openapi.json")


def build_app(mode: str = "development") -> FastAPI:
    """Construct a FastAPI app wired to the API Gateway."""
    app = FastAPI(title="DotMac Platform API", version="1.0.0")
    gateway = APIGateway(settings)
    gateway.setup(app)
    return app


def export_schema(output: Path, mode: str = "development") -> None:
    app = build_app(mode=mode)
    schema = app.openapi()
    output.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"OpenAPI schema written to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema for the DotMac platform")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination JSON file")
    parser.add_argument(
        "--mode",
        choices=["development", "staging", "production"],
        default="development",
        help="Gateway mode used when building the app",
    )
    args = parser.parse_args()

    export_schema(output=args.output, mode=args.mode)


if __name__ == "__main__":
    main()
