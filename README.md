[![codecov](https://codecov.io/gh/usimd/pyoekoboxonline/graph/badge.svg?token=VDG1IFFZSL)](https://codecov.io/gh/usimd/pyoekoboxonline)
[![PyPI](https://img.shields.io/pypi/v/pyoekoboxonline.svg)](https://pypi.org/project/pyoekoboxonline/)
[![Python Version](https://img.shields.io/pypi/pyversions/pyoekoboxonline.svg)](https://pypi.org/project/pyoekoboxonline/)
[![License](https://img.shields.io/pypi/l/pyoekoboxonline.svg)](https://pypi.org/project/pyoekoboxonline/)
# Pyoekoboxonline

A Python client library for the [Ökobox Online](https://oekobox-online.de) e-commerce REST API. This library provides an easy-to-use, async interface for interacting with organic food delivery and subscription services.

> **Note**: This library is designed to be compatible with Home Assistant custom integrations and uses `aiohttp` for HTTP requests.

## Requirements

- **Python 3.11+** - Modern Python features and performance improvements
- **Async/await support** - Built with modern Python async patterns
- **aiohttp** - Modern async HTTP client library

## Features

- **Type hints** - Full type annotation support with mypy
- **Pydantic models** - Robust data validation and serialization
- **Comprehensive error handling** - Detailed exception hierarchy
- **Well tested** - High test coverage with pytest
- **Production ready** - Follows Python packaging best practices
- **External session support** - Compatible with Home Assistant's shared aiohttp session

## Installation

```bash
pip install pyoekoboxonline
```

**Note**: Requires Python 3.11 or higher.

## Quick Start

### Standard Usage

```python
import asyncio
from pyoekoboxonline import OekoboxClient

async def main():
    # First, discover available shops
    shops = await OekoboxClient.get_shop_info()
    print(f"Found {len(shops)} shops")

    # Connect to a specific shop
    async with OekoboxClient(
        shop_id="your_shop_id",  # From shop list
        username="your-username",
        password="your-password"
    ) as client:
        # Login
        await client.logon()

        # Browse product categories
        groups = await client.get_groups()
        for group in groups:
            print(f"Category: {group.name}")

        # Browse products
        items = await client.get_items()
        for item in items:
            print(f"{item.name}: {item.price}")

        # Add items to cart
        await client.add_to_cart(item_id=123, amount=2.0)

        # View orders
        orders = await client.get_orders()
        for order in orders:
            print(f"Order {order.id}")

        # Logout
        await client.logout()

asyncio.run(main())
```

### Home Assistant Integration (External Session)

For Home Assistant integrations, you can pass an external `aiohttp.ClientSession`:

```python
import aiohttp
from pyoekoboxonline import OekoboxClient

async def setup_platform(hash, config, async_add_entities, discovery_info=None):
    """Set up the Ökobox Online integration."""

    # Use Home Assistant's shared session
    session = hash.helpers.aiohttp_client.async_get_clientsession()

    # Create client with external session
    client = OekoboxClient(
        shop_id=config["shop_id"],
        username=config["username"],
        password=config["password"],
        session=session,  # Pass the external session
    )

    # No need for context manager when using external session
    await client.logon()

    # Use the client...
    # The session will be managed by Home Assistant
```

## API Reference

### Client

#### `OekoboxClient(shop_id, username, password, base_url=None, timeout=30.0, session=None)`

The main client class for interacting with the Ökobox Online API.

**Parameters:**
- `shop_id` (str): Shop identifier from the shop list
- `username` (str): Your account username
- `password` (str): Your account password
- `base_url` (str, optional): Custom base URL (auto-detected from shop_id)
- `timeout` (float, optional): Request timeout in seconds (default: 30.0)
- `session` (aiohttp.ClientSession, optional): External aiohttp session (for Home Assistant integrations)

### Shop Discovery

#### `await OekoboxClient.get_available_shops() -> List[Shop]`

Get list of available Ökobox Online shops with location data.

### Authentication

#### `await client.login() -> UserInfo`

Authenticate and establish session.

#### `await client.logout()`

Clear session and logout.

### Product Catalog

#### `await client.get_groups() -> List[Group]`

Get product categories.

#### `await client.get_items(group_id=None, subgroup_id=None) -> List[Item]`

Get available products, optionally filtered by category.

#### `await client.search_items(query: str) -> List[Item]`

Search for products by name or description.

### Shopping Cart

#### `await client.get_cart() -> List[CartItem]`

Get current cart contents.

#### `await client.add_to_cart(item_id: str, quantity: float)`

Add item to cart.

#### `await client.clear_cart()`

Clear all items from cart.

### Orders

#### `await client.get_orders() -> List[Order]`

Get customer's orders.

#### `await client.create_order() -> Order`

Create order from current cart.

## Error Handling

```python
from pyoekoboxonline.exceptions import (
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxAPIError
)

try:
    user = await client.login()
except OekoboxAuthenticationError:
    print("Invalid credentials")
except OekoboxConnectionError as e:
    print(f"Connection error: {e}")
except OekoboxAPIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/usimd/pyoekoboxonline.git
cd pyoekoboxonline

# Install with uv (recommended) - requires Python 3.11+
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Run all pre-commit hooks (includes ruff, mypy, bandit, etc.)
uv run pre-commit run --all-files

# Install pre-commit hooks for automatic checking
uv run pre-commit install
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
