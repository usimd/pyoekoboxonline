"""Configuration and utilities for integration tests."""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class IntegrationTestConfig:
    """Configuration for integration tests."""

    shop_id: str
    username: str
    password: str
    timeout: float = 30.0
    base_url: str | None = None

    @classmethod
    def from_env(cls) -> "IntegrationTestConfig":
        """Create config from environment variables."""
        shop_id = os.getenv("OEKOBOX_SHOP_ID", "")
        username = os.getenv("OEKOBOX_USERNAME", "")
        password = os.getenv("OEKOBOX_PASSWORD", "")
        timeout = float(os.getenv("OEKOBOX_TIMEOUT", "30.0"))
        base_url = os.getenv("OEKOBOX_BASE_URL")

        if not all([shop_id, username, password]):
            raise ValueError(
                "Missing required environment variables: "
                "OEKOBOX_SHOP_ID, OEKOBOX_USERNAME, OEKOBOX_PASSWORD"
            )

        return cls(
            shop_id=shop_id,
            username=username,
            password=password,
            timeout=timeout,
            base_url=base_url,
        )

    @classmethod
    def from_file(cls, filepath: str) -> "IntegrationTestConfig":
        """Create config from a file (for local testing)."""
        config = {}
        try:
            with open(filepath) as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Config file not found: {filepath}") from err

        return cls(
            shop_id=config.get("SHOP_ID", ""),
            username=config.get("USERNAME", ""),
            password=config.get("PASSWORD", ""),
            timeout=float(config.get("TIMEOUT", "30.0")),
            base_url=config.get("BASE_URL"),
        )

    def is_valid(self) -> bool:
        """Check if config has all required values."""
        return all([self.shop_id, self.username, self.password])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "shop_id": self.shop_id,
            "username": self.username,
            "password": self.password,
            "timeout": self.timeout,
            "base_url": self.base_url,
        }


def get_test_config() -> IntegrationTestConfig:
    """Get test configuration from environment or file."""
    # Try environment variables first
    try:
        return IntegrationTestConfig.from_env()
    except ValueError:
        pass

    # Try local config file
    config_paths = [
        "integration_test_config.txt",
        "tests/integration_test_config.txt",
        os.path.expanduser("~/.oekobox_test_config"),
    ]

    for path in config_paths:
        try:
            return IntegrationTestConfig.from_file(path)
        except FileNotFoundError:
            continue

    raise ValueError(
        "No valid configuration found. Please set environment variables "
        "or create a config file with the required credentials."
    )
