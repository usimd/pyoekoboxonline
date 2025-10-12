# Pyoekoboxonline

A Python client library for the [Ökobox Online](https://oekobox-online.de) e-commerce REST API. This library provides an easy-to-use, async interface for interacting with organic food delivery and subscription services.

> **Note**: This library is designed to be compatible with Home Assistant custom integrations.

## Requirements

- **Python 3.11+** - Modern Python features and performance improvements
- **Async/await support** - Built with modern Python async patterns

## Features

- **Type hints** - Full type annotation support with mypy
- **Pydantic models** - Robust data validation and serialization
- **Comprehensive error handling** - Detailed exception hierarchy
- **Well tested** - High test coverage with pytest
- **Production ready** - Follows Python packaging best practices

## Installation

```bash
pip install pyoekoboxonline
```

**Note**: Requires Python 3.11 or higher.

## Quick Start

```python
import asyncio
from pyoekoboxonline import OekoboxClient

async def main():
    # First, discover available shops
    shops = await OekoboxClient.get_available_shops()
    print(f"Found {len(shops)} shops")

    # Connect to a specific shop
    client = OekoboxClient(
        shop_id="your_shop_id",  # From shop list
        username="your-username",
        password="your-password"
    )

    async with client:
        # Login
        user = await client.login()
        print(f"Hello, {user.username}!")

        # Browse product categories
        groups = await client.get_groups()
        for group in groups:
            print(f"Category: {group.name}")

        # Browse products
        items = await client.get_items()
        for item in items:
            print(f"{item.name}: {item.price}")

        # Add items to cart
        await client.add_to_cart("item_123", quantity=2.0)

        # View orders
        orders = await client.get_orders()
        for order in orders:
            print(f"Order {order.id}: {order.total_amount}")

asyncio.run(main())
```

## API Reference

### Client

#### `OekoboxClient(shop_id, username, password, base_url=None, timeout=30.0)`

The main client class for interacting with the Ökobox Online API.

**Parameters:**
- `shop_id` (str): Shop identifier from the shop list
- `username` (str): Your account username
- `password` (str): Your account password
- `base_url` (str, optional): Custom base URL (auto-detected from shop_id)
- `timeout` (float, optional): Request timeout in seconds

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
