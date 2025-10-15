"""Main client for the Ökobox Online API."""

import logging
import re
from typing import Any, TypeVar

import httpx

from .exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxValidationError,
)
from .models import (
    Address,
    AuxDate,
    DDate,
    Delivery,
    DeliveryState,
    DeselectedGroup,
    DeselectedItem,
    Favourite,
    Group,
    Item,
    Order,
    Pause,
    Shop,
    ShopDate,
    ShopUrl,
    SubGroup,
    Subscription,
    Tour,
    UserInfo,
    XUnit,
    parse_data_list_response,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OekoboxClient:
    """Async client for the Ökobox Online REST API.

    This client provides methods to interact with the Ökobox Online e-commerce
    platform API for food delivery and subscription services.

    Based on official API documentation from: https://oekobox-online.de/shopdocu/wiki/API

    Args:
        shop_id: Shop identifier from the shop list
        username: Username/Customer ID for authentication (can be email or customer ID)
        password: Password for authentication
        base_url: Base URL of the shop (default: auto-detected from shop_id)
        timeout: Request timeout in seconds (default: 30)

    Example:
        ```python
        import asyncio
        from pyoekoboxonline import OekoboxClient

        async def main():
            async with OekoboxClient("amperhof", "user@example.com", "password") as client:
                # Login using official 'logon' method
                user_info = await client.logon()

                # Get product groups
                groups = await client.get_groups()

                # Logout using official 'logout' method
                await client.logout()

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        shop_id: str,
        username: str,
        password: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Ökobox Online client."""
        self.shop_id = shop_id
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session_id: str | None = None

        # Official API URL structure: https://oekobox-online.de/v3/shop/<shopid>/
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            self.base_url = f"https://oekobox-online.de/v3/shop/{shop_id}"

        # Initialize HTTP client
        self._client: httpx.AsyncClient | None = None

    @property
    def api_base_url(self) -> str:
        """Get the API base URL according to official specification."""
        return f"{self.base_url}/api"

    async def __aenter__(self) -> "OekoboxClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make a raw HTTP request to the API.

        According to official API docs, sessions can be maintained via:
        1. Standard cookies (preferred)
        2. x-oekobox-sid parameter
        """
        if not self._client:
            raise OekoboxConnectionError(
                "Client not initialized. Use async context manager."
            )

        # Prepare headers
        headers = kwargs.get("headers", {})

        # Add session ID parameter if available (official API specification)
        if self.session_id:
            if params is None:
                params = {}
            params["x-oekobox-sid"] = self.session_id

        try:
            response = await self._client.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                cookies={"OOSESSION": self.session_id} if self.session_id else None,
                **kwargs,
            )

            # Extract session ID from various cookie formats
            if "Set-Cookie" in response.headers or response.cookies:
                # Try multiple session cookie names based on official documentation
                session_cookies = ["JSESSIONID", "OOSESSION", "sessionid"]

                for cookie_name in session_cookies:
                    # Check response cookies first
                    if hasattr(response, "cookies") and cookie_name in response.cookies:
                        cookie_value = response.cookies[cookie_name]
                        if cookie_value and not self.session_id:
                            self.session_id = cookie_value
                            logger.debug(
                                f"Session ID extracted from {cookie_name}: {self.session_id[:10]}..."
                            )
                            break

                    # Check Set-Cookie header
                    if "Set-Cookie" in response.headers:
                        cookie_header = response.headers["Set-Cookie"]
                        if cookie_name in cookie_header:
                            match = re.search(rf"{cookie_name}=([^;]+)", cookie_header)
                            if match and not self.session_id:
                                self.session_id = match.group(1)
                                logger.debug(
                                    f"Session ID extracted from header {cookie_name}: {self.session_id[:10]}..."
                                )
                                break

            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise OekoboxAuthenticationError(
                    f"HTTP {e.response.status_code}: Authentication failed",
                    e.response.status_code,
                ) from e
            elif e.response.status_code == 403:
                raise OekoboxAuthenticationError(
                    f"HTTP {e.response.status_code}: Access forbidden",
                    e.response.status_code,
                ) from e
            else:
                # Try to get error message from response
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", e.response.text)
                except Exception:
                    error_msg = e.response.text

                raise OekoboxAPIError(
                    f"HTTP {e.response.status_code}: {error_msg}",
                    e.response.status_code,
                ) from e

        except httpx.RequestError as e:
            raise OekoboxConnectionError(f"Request failed: {e}") from e

        # Parse JSON response
        try:
            return response.json()
        except Exception as e:
            raise OekoboxValidationError(f"Invalid JSON response: {e}") from e

    async def _api_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make an API request and handle DataList responses."""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        response_data = await self._request(method, url, params, data, **kwargs)

        # Handle DataList responses
        if isinstance(response_data, list):
            return parse_data_list_response(response_data)

        return response_data

    # Authentication Methods
    async def logon(self, guest: bool = False) -> dict[str, Any]:
        """
        Authenticate with the API using username and password.

        Args:
            guest: If True, login as guest without credentials

        Returns:
            Logon response with session information

        Raises:
            OekoboxAuthenticationError: If authentication fails
        """
        params = {}
        if guest:
            params["guest"] = "true"
        else:
            params["cid"] = self.username
            params["pass"] = self.password

        response = await self._request(
            "GET", f"{self.api_base_url}/logon", params=params
        )

        # Ensure response is a dict for logon operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from logon endpoint")

        # Check logon result
        result = response.get("result")
        if result not in ["ok", "relogon", "guest"]:
            error_messages = {
                "no_data": "No authentication data provided",
                "empty": "Shop not loaded with data",
                "no_such_user": "User cannot be identified",
                "duplicate_user": "Email exists multiple times, access denied",
                "wrong_password": "Wrong password",
                "blocked": "User account temporarily blocked",
                "tblocked": "IP address temporarily blocked",
                "token_too_old": "Logon token too old",
                "wrong_token": "Token wrong",
                "use_id": "Use customer ID instead of email",
                "token_session": "Token not created by this session",
            }
            error_msg = error_messages.get(
                str(result) if result is not None else "unknown",
                f"Logon failed: {result}",
            )
            raise OekoboxAuthenticationError(error_msg)

        logger.info(f"Successfully logged in with result: {result}")
        return response

    async def logout(self) -> dict[str, Any]:
        """
        Logout and end the current session.

        Returns:
            Logout response
        """
        response = await self._request("GET", f"{self.api_base_url}/logout")

        # Ensure response is a dict for logout operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from logout endpoint")

        self.session_id = None
        logger.info("Successfully logged out")
        return response

    # Core Data Methods
    async def get_groups(self) -> list[Group]:
        """
        Get all product groups/categories.

        Returns:
            List of Group objects
        """
        response = await self._api_request("groups")
        return response  # type: ignore[no-any-return]

    async def get_subgroups(self, group_id: int | None = None) -> list[SubGroup]:
        """
        Get subgroups, optionally filtered by parent group.

        Args:
            group_id: Optional parent group ID to filter by

        Returns:
            List of SubGroup objects
        """
        params = {}
        if group_id is not None:
            params["g"] = str(group_id)
        response = await self._api_request("subgroup", params=params)
        return response  # type: ignore[no-any-return]

    async def get_items(
        self,
        group_id: int | None = None,
        subgroup_id: int | None = None,
        rubric_id: int | None = None,
        search: str | None = None,
        hidden: bool = False,
        timeless: bool = False,
    ) -> list[Item]:
        """
        Get items with optional filtering.

        Args:
            group_id: Filter by group ID
            subgroup_id: Filter by subgroup ID
            rubric_id: Filter by rubric ID
            search: Search term
            hidden: Include hidden items
            timeless: Include timeless items

        Returns:
            List of Item objects
        """
        params = {}
        if group_id is not None:
            params["g"] = str(group_id)
        if subgroup_id is not None:
            params["sg"] = str(subgroup_id)
        if rubric_id is not None:
            params["r"] = str(rubric_id)
        if search:
            params["s"] = search
        if hidden:
            params["hidden"] = "1"
        if timeless:
            params["timeless"] = "1"

        response = await self._api_request("items", params=params)
        return response  # type: ignore[no-any-return]

    async def get_item(self, item_id: int) -> list[Item]:
        """
        Get specific item by ID.

        Args:
            item_id: Item ID to retrieve

        Returns:
            List containing the Item object
        """
        response = await self._api_request(f"item/{item_id}")
        return response  # type: ignore[no-any-return]

    async def get_itemlist(
        self,
        item_ids: list[int],
        tour_id: int | None = None,
        order_id: int | None = None,
    ) -> list[Item | XUnit]:
        """
        This method allows to obtain the information for a set of items, provided as argument.

        It's an alternative to the item call, that only provides data for a single item.

        Args:
            item_ids: List of item IDs to retrieve

        Returns:
            List of Item objects
        """
        ids_param = ",".join(map(str, item_ids))
        params: dict[str, Any] = {"i": ids_param}
        if tour_id is not None:
            params["tourid"] = str(tour_id)
        if order_id is not None:
            params["oid"] = str(order_id)
        response = await self._api_request("itemlist16", params=params)
        return response  # type: ignore[no-any-return]

    # Cart Methods
    async def add_to_cart(
        self,
        item_id: int,
        amount: float = 1.0,
        note: str | None = None,
        repeat: int = 0,
        allow_duplicates: int = 0,
        position: int | None = None,
    ) -> dict[str, Any]:
        """
        Add item to cart.

        Args:
            item_id: ID of item to add
            amount: Amount in units (default: 1.0)
            note: Optional note for this cart position
            repeat: Repeated delivery every X weeks (default: 0 = one-time)
            allow_duplicates: 0=default, 1=clear existing, 2=add up
            position: Specific position to replace

        Returns:
            Cart operation response
        """
        data = {"id": str(item_id), "amount": str(amount)}
        if note:
            data["note"] = note
        if repeat:
            data["repeat"] = str(repeat)
        if allow_duplicates:
            data["ad"] = str(allow_duplicates)
        if position is not None:
            data["pos"] = str(position)

        response = await self._request(
            "POST", f"{self.api_base_url}/cart/add", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from cart operation")

        return response

    async def remove_from_cart(
        self, item_id: int | None = None, position: int | None = None
    ) -> dict[str, Any]:
        """
        Remove item from cart.

        Args:
            item_id: ID of item to remove
            position: Alternative: cart position to delete

        Returns:
            Cart operation response
        """
        data = {}
        if item_id is not None:
            data["id"] = item_id
        if position is not None:
            data["pos"] = position

        response = await self._request(
            "POST", f"{self.api_base_url}/cart/remove", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from cart operation")

        return response

    async def show_cart(self) -> list[Any]:
        """
        Show current cart contents.

        Returns:
            List of cart items and related data
        """
        response = await self._api_request("cart/show")
        return response  # type: ignore[no-any-return]

    async def reset_cart(self) -> dict[str, Any]:
        """
        Reset/clear the entire cart.

        Returns:
            Reset operation response
        """
        response = await self._request("POST", f"{self.api_base_url}/client/resetcart")

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from cart operation")

        return response

    # Order Methods
    async def get_orders(
        self,
        days_past: int | None = None,
        days_ahead: int | None = None,
        tour_ids: list[int] | None = None,
    ) -> list[Order]:
        """
        Lists orders that are currently in the system.

        Args:
            days_past: Days in the past from today (default 7)
            days_ahead: Days ahead of today (default 0)
            tour_ids: optional list of tourids

        Returns:
            List of Order objects
        """
        params = {}
        if days_past is not None:
            params["pd"] = str(days_past)
        if days_ahead is not None:
            params["ad"] = str(days_ahead)
        if tour_ids is not None:
            params["tours"] = ",".join(map(str, tour_ids))

        response = await self._api_request("orders", params=params)
        return response  # type: ignore[no-any-return]

    async def get_order(self, order_id: int) -> list[Order]:
        """
        Get specific order by ID.

        Args:
            order_id: Order ID to retrieve

        Returns:
            List containing the Order object
        """
        response = await self._api_request(f"order26/{order_id}")
        return response  # type: ignore[no-any-return]

    async def get_order_items(self, order_id: int) -> list[Item | XUnit]:
        """
        Provides the items of a given order. Other options for obtaining items are the itemlist or group calls.

        Args:
            order_id: the order id for which the items should be listed in the response

        Returns:
            List of Item and associated XUnit objects
        """
        response = await self._api_request(f"orderitems/{order_id}")
        return response  # type: ignore[no-any-return]

    async def new_order(
        self,
        delivery_date: str,
        tour_id: int | None = None,
        customer_note: str | None = None,
        delivery_note: str | None = None,
    ) -> dict[str, Any]:
        """
        Create new order from current cart.

        Args:
            delivery_date: Desired delivery date (ISO format)
            tour_id: Specific tour ID for delivery
            customer_note: Customer note for the order
            delivery_note: Note for delivery team

        Returns:
            Order creation response
        """
        data = {"ddate": delivery_date}
        if tour_id is not None:
            data["tour"] = str(tour_id)
        if customer_note:
            data["cnote"] = customer_note
        if delivery_note:
            data["rnote"] = delivery_note

        response = await self._request(
            "POST", f"{self.api_base_url}/client/neworder", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from order operation")

        return response

    async def cancel_order(self, order_id: int) -> dict[str, Any]:
        """
        Cancel an existing order.

        Args:
            order_id: Order ID to cancel

        Returns:
            Cancellation response
        """
        data = {"order": str(order_id)}
        response = await self._request(
            "POST", f"{self.api_base_url}/client/cancelorder", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from order operation")

        return response

    async def change_order(
        self,
        order_id: int,
        delivery_date: str | None = None,
        customer_note: str | None = None,
        delivery_note: str | None = None,
    ) -> dict[str, Any]:
        """
        Change an existing order.

        Args:
            order_id: Order ID to change
            delivery_date: New delivery date
            customer_note: New customer note
            delivery_note: New delivery note

        Returns:
            Change response
        """
        data = {"order": str(order_id)}
        if delivery_date:
            data["ddate"] = delivery_date
        if customer_note:
            data["cnote"] = customer_note
        if delivery_note:
            data["rnote"] = delivery_note

        response = await self._request(
            "POST", f"{self.api_base_url}/client/changeorder", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from order operation")

        return response

    # Tour and Delivery Methods
    async def get_tour(self, tour_id: int) -> list[Tour | DDate | Delivery | Address]:
        """
        Provides Tour Information.

        This includes everything to deliver the goods after on-site packing.
        The Tour-Objects contains the general tour info, together with associated DDate and a ordered sequence of Delivery-Objects. These Delivery-Objects reference addresses which are to be targeted in that tour.It further has a reference to the order, which provides many more details.
        Note that the reference is using a composite key Delivery.CustomerId-Delivery.AddressName to point to the right address, as customers might have multiple (named) addresses.
        Since these objects are provided separately, the could be updated separately too. Any update requires the submitting of a appropriate version reference to implement a optimistic locking.
        See also API.methods.driver, API.methods.tours

        Args:
            tour_id: The tour-instance-id (tid) is the ID provided from the API.methods.tours-Call. Its the Id of the DDate record.

        Returns:
            A sequence of these objects: Tour, DDate, a list of Deliveries, and a list of Addresses.
        """
        response = await self._api_request(f"tour30/{tour_id}")
        return response  # type: ignore[no-any-return]

    async def get_dates(
        self,
    ) -> list[
        ShopDate
        | Pause
        | Subscription
        | Favourite
        | AuxDate
        | DeselectedItem
        | DeselectedGroup
    ]:
        """
        Get available delivery dates.

        Returns:
            List of objects of type ShopDate, Pause, Subscription, Favourite, AuxDate, DeselectedItem, or DeselectedGroup
        """
        response = await self._api_request("dates7")
        return response  # type: ignore[no-any-return]

    async def set_tour(self, tour_id: int) -> dict[str, Any]:
        """
        Set preferred delivery tour for the customer.

        Args:
            tour_id: Tour ID to set as preference

        Returns:
            Tour setting response
        """
        data = {"tour": str(tour_id)}
        response = await self._request(
            "POST", f"{self.api_base_url}/client/settour", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError("Expected dict response from tour operation")

        return response

    async def add_subscription(
        self,
        item_id: int,
        amount: float,
        interval: int = 1,
    ) -> dict[str, Any]:
        """
        Add item subscription.

        Args:
            item_id: Item ID to subscribe to
            amount: Amount per delivery
            interval: Delivery interval in weeks

        Returns:
            Subscription response
        """
        data = {
            "item": str(item_id),
            "amount": str(amount),
            "interval": str(interval),
        }
        response = await self._request(
            "POST", f"{self.api_base_url}/client/addsubscription", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError(
                "Expected dict response from subscription operation"
            )

        return response

    async def change_subscription(
        self,
        subscription_id: int,
        amount: float | None = None,
        interval: int | None = None,
    ) -> dict[str, Any]:
        """
        Change existing subscription.

        Args:
            subscription_id: Subscription ID to change
            amount: New amount per delivery
            interval: New delivery interval in weeks

        Returns:
            Change response
        """
        data = {"subscription": str(subscription_id)}
        if amount is not None:
            data["amount"] = str(amount)
        if interval is not None:
            data["interval"] = str(interval)

        response = await self._request(
            "POST", f"{self.api_base_url}/client/changesubscription", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError(
                "Expected dict response from subscription operation"
            )

        return response

    async def drop_subscription(self, subscription_id: int) -> dict[str, Any]:
        """
        Cancel/drop a subscription.

        Args:
            subscription_id: Subscription ID to cancel

        Returns:
            Cancellation response
        """
        data = {"subscription": str(subscription_id)}
        response = await self._request(
            "POST", f"{self.api_base_url}/client/dropsubscription", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError(
                "Expected dict response from subscription operation"
            )

        return response

    # Favourites Methods
    async def get_favourites(self) -> list[Favourite]:
        """
        Get customer favourite items.

        Returns:
            List of Favourite objects
        """
        response = await self._api_request("client/favourites")
        return response  # type: ignore[no-any-return]

    async def add_favourites(self, item_ids: list[int]) -> dict[str, Any]:
        """
        Add items to favourites.

        Args:
            item_ids: List of item IDs to add to favourites

        Returns:
            Add favourites response
        """
        ids_param = ",".join(map(str, item_ids))
        data = {"items": ids_param}
        response = await self._request(
            "POST", f"{self.api_base_url}/client/addfavourites", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError(
                "Expected dict response from favourites operation"
            )

        return response

    async def drop_favourites(self, item_ids: list[int]) -> dict[str, Any]:
        """
        Remove items from favourites.

        Args:
            item_ids: List of item IDs to remove from favourites

        Returns:
            Remove favourites response
        """
        ids_param = ",".join(map(str, item_ids))
        data = {"items": ids_param}
        response = await self._request(
            "POST", f"{self.api_base_url}/client/dropfavourites", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError(
                "Expected dict response from favourites operation"
            )

        return response

    # User Profile Methods
    async def get_user_info(self) -> list[UserInfo]:
        """
        Get current user information.

        Returns:
            List containing UserInfo object
        """
        response = await self._api_request("user20")
        return response  # type: ignore[no-any-return]

    async def set_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """
        Update user profile information.

        Args:
            profile_data: Dictionary of profile fields to update

        Returns:
            Profile update response
        """
        response = await self._request(
            "POST", f"{self.api_base_url}/client/setprofile", data=profile_data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError(
                "Expected dict response from profile operation"
            )

        return response

    async def change_password(
        self, old_password: str, new_password: str
    ) -> dict[str, Any]:
        """
        Change user password.

        Args:
            old_password: Current password
            new_password: New password

        Returns:
            Password change response
        """
        data = {
            "oldpass": old_password,
            "newpass": new_password,
        }
        response = await self._request(
            "POST", f"{self.api_base_url}/client/password", data=data
        )

        # Ensure response is a dict for cart operations
        if not isinstance(response, dict):
            raise OekoboxValidationError(
                "Expected dict response from password operation"
            )

        return response

    # Search Methods
    async def search(self, query: str, limit: int | None = None) -> list[Item]:
        """
        Search for items.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Item objects
        """
        params = {"q": query}
        if limit is not None:
            params["limit"] = str(limit)

        response = await self._api_request("search", params=params)
        return response  # type: ignore[no-any-return]

    async def get_delivery_state(self) -> list[DeliveryState]:
        """
        Delivery State or forecast for a given customer.

        If the caller has administrative permissions, the preceding and following customer numbers are shown and a cid may be handed over. otherwise, the executers data is used.

        Returns:
            A API.objects.DeliveryState Object TBD
        """
        response = await self._api_request("client/delivery")
        return response  # type: ignore[no-any-return]

    # Shop Information Methods
    async def get_shop_info(self) -> list[Shop]:
        """
        Get shop information and configuration.

        Returns:
            List containing Shop object
        """
        # The shop info endpoint is not part of the standard API, so we fetch it directly.
        # Its response needs to be wrapped in a DataList format to handle it similar to
        # the other models.
        response_data = await self._request(
            "GET", "https://oekobox-online.eu/v3/shoplist.js.jsp"
        )
        return parse_data_list_response(
            [
                {
                    "type": "Shop",
                    "data": response_data,
                }
            ]
        )

    # Utility Methods
    async def find_shop(self, lat: float, lng: float) -> list[ShopUrl]:
        """
        Find shops by location.

        Args:
            lat: lat/lng are latitude/longitide parameters in the common wds84 decimal format
            lng: lat/lng are latitude/longitide parameters in the common wds84 decimal format

        Returns:
            List of Shop objects
        """
        params = {"lat": str(lat), "lng": str(lng)}
        response = await self._request(
            "GET", "https://oekobox-online.de/v3/findshop", params=params
        )
        return parse_data_list_response(response)

    # Start method - combines authentication with data fetching
    async def start(
        self,
        include_groups: bool = True,
        include_tours: bool = True,
        include_dates: bool = True,
    ) -> dict[str, Any]:
        """
        Combined start method that authenticates and fetches initial data.

        Args:
            include_groups: Include product groups in response
            include_tours: Include delivery tours in response
            include_dates: Include delivery dates in response

        Returns:
            Combined response with authentication and data

        Deprecated:
            This method is deprecated in favor of explicit calls to `logon` and data fetching methods.
        """
        params = {
            "cid": self.username,
            "pass": self.password,
        }
        if include_groups:
            params["groups"] = "1"
        if include_tours:
            params["tours"] = "1"
        if include_dates:
            params["dates"] = "1"

        response = await self._api_request("start", params=params)
        return response  # type: ignore[no-any-return]
