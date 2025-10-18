"""
Model definitions for the ÖkoBox Online API.

This module contains all the data models representing API objects as defined
in the comprehensive API documentation. Each model follows the DataList concept
where responses are wrapped in arrays with metadata.
"""

from __future__ import annotations

import datetime
from dataclasses import MISSING, dataclass, field
from typing import (
    Any,
    get_args,
    get_type_hints,
)


class DataListModel:
    """
    Base class for all API models that provides automatic parsing from DataList entries.

    Leverages PEP 520's stable field ordering to map data list array indices to
    dataclass fields automatically, eliminating the need for manual index mapping.
    """

    @classmethod
    def from_data_list_entry(cls, data: list[Any]) -> DataListModel:
        """
        Create model instance from DataList entry array.

        Uses the stable ordering of dataclass fields (PEP 520) to automatically
        map array indices to the corresponding field values with proper type conversion.

        Args:
            data: Array of values from DataList response

        Returns:
            Instance of the model class with populated fields
        """
        if not hasattr(cls, "__dataclass_fields__"):
            raise ValueError(
                f"{cls.__name__} must be a dataclass to use from_data_list_entry"
            )

        # Get field definitions in declaration order (stable since PEP 520)
        field_list = list(cls.__dataclass_fields__.items())
        type_hints = get_type_hints(cls)

        kwargs = {}

        for index, (field_name, field_def) in enumerate(field_list):
            if index >= len(data):
                # Use default value if data array is shorter than expected
                kwargs[field_name] = (
                    field_def.default if field_def.default != MISSING else None
                )
                continue

            value = data[index]

            # Skip empty/null values
            if value is None or value == "":
                kwargs[field_name] = None
                continue

            # Get the field type for conversion
            field_type = type_hints.get(field_name, Any)
            types = get_args(field_type)

            # Convert value based on field type
            try:
                if int in types:
                    kwargs[field_name] = int(value) if value is not None else None
                elif datetime.datetime in types:
                    kwargs[field_name] = (
                        datetime.datetime.fromisoformat(value)
                        if value is not None
                        else None
                    )
                elif datetime.date in types:
                    kwargs[field_name] = (
                        datetime.datetime.strptime(value, "%Y-%m-%d")
                        if value is not None
                        else None
                    )
                elif float in types:
                    kwargs[field_name] = float(value) if value is not None else None
                elif bool in types:
                    kwargs[field_name] = bool(value) if value is not None else None
                elif str in types:
                    kwargs[field_name] = str(value) if value else None
                else:
                    # For other types, just use the value as-is
                    kwargs[field_name] = value
            except (ValueError, TypeError):
                # If conversion fails, use None
                kwargs[field_name] = None

        return cls(**kwargs)


@dataclass
class DataListResponse:
    """
    Base response structure for DataList API responses.

    According to the DataList concept, responses are always wrapped in arrays
    containing type metadata and data arrays.
    """

    type: str = field(metadata={"description": "The type name of the object"})
    version: int | None = field(
        default=None, metadata={"description": "API version number"}
    )
    cnt: int | None = field(
        default=None, metadata={"description": "Number of records in data"}
    )
    data: list[list[Any]] = field(
        default_factory=list, metadata={"description": "Array of data records"}
    )


@dataclass
class Address(DataListModel):
    """
    Address object representing a delivery or customer address.

    Description: entry, Grundstück (Name des Gebäudes/Grundstücks, Einkaufszentrum usw.)
    """

    customer_id: int | None = field(
        default=None,
        metadata={
            "description": "The id of the customer this address belongs to (if known)"
        },
    )
    address_name: str | None = field(
        default=None,
        metadata={
            "description": 'The name of the address (each address for a customer might have a unique name). If null or empty, this address is the "default" address (if known)'
        },
    )
    name: str | None = field(
        default=None,
        metadata={"description": "Family Name of the addressee (if known)"},
    )
    firstname: str | None = field(
        default=None, metadata={"description": "First name (if known)"}
    )
    street: str | None = field(
        default=None, metadata={"description": "Street of Address"}
    )
    city: str | None = field(default=None, metadata={"description": "City name"})
    zip: str | None = field(default=None, metadata={"description": "ZIP code"})
    zip_code: str | None = field(
        default=None, metadata={"description": "Alternative ZIP code field"}
    )
    lat: float | None = field(
        default=None,
        metadata={
            "description": "Latitude of the Address in WDS84/Decimal Geocode (primarily vehicle position)"
        },
    )
    lng: float | None = field(
        default=None,
        metadata={
            "description": "Longtitude of the Address in WDS84/Decimal Geocode (primarily vehicle position)"
        },
    )
    llq: int | None = field(
        default=None,
        metadata={
            "description": "Accuracy of the Lat/Lng Geo-Reference. (Since Version 2)"
        },
    )
    phone: str | None = field(
        default=None,
        metadata={"description": "phone number (if available). (Since Version 3)"},
    )
    mobile: str | None = field(
        default=None,
        metadata={"description": "mobile number (if available). (Since Version 3)"},
    )
    todohint: str | None = field(
        default=None,
        metadata={"description": "Advice related to this address (Since Version 4)"},
    )
    wayhint: str | None = field(
        default=None,
        metadata={"description": "Advice related to way. (Since Version 4)"},
    )
    packhint: str | None = field(
        default=None,
        metadata={"description": "Driver/Packing information (Since Version 5)"},
    )


@dataclass
class Item(DataListModel):
    """
    Describes an Item of the Online-Shop.

    Currently supports multiple versions of this object within API calls.
    Version history spans from 1 to 20 with various feature additions.
    """

    id: int | None = field(
        default=None, metadata={"description": "Item Id as found in the online shop"}
    )
    name: str | None = field(
        default=None, metadata={"description": "generic name. Subject to localization."}
    )
    price: float | None = field(
        default=None,
        metadata={
            "description": "Price in base units of the online Shop. Subject to localization."
        },
    )
    unit: str | None = field(
        default=None,
        metadata={
            "description": "Base unit of that Item. See API.objects.XUnit for referenced alternative units"
        },
    )
    description: str | None = field(
        default=None,
        metadata={
            "description": "the plain text description. Subject to localization and rather short."
        },
    )
    category_id: int | None = field(
        default=None,
        metadata={
            "description": "References its default category. A Item might be member of other rubrics too."
        },
    )
    vat: float | None = field(
        default=None,
        metadata={
            "description": "VAT in percent that applies. May depend on Shop Settings and user that is executing this call."
        },
    )
    flag: int | None = field(
        default=None,
        metadata={"description": "unused, see flagsX below, not in Version 2 anymore"},
    )
    refund: float | None = field(
        default=None, metadata={"description": "Refund when ordering this item"}
    )
    item_type: str | None = field(
        default=None,
        metadata={
            "description": "S for items that come in pieces, W for items delivered in weightable units, 1: Package, 2:Organizational Item, 6: voucher for new customer, 7: voucher for new customers, 8: generic voucher, 9: indiv. voucher, 10: resolvable recipe, 11: unresolvable recipe, 20: points to one or all aboboxes, 21: points to one or all abogroups, 22: points to one or all item rubrics, 23: points to one or all item groups, 24: points to one or all subgroups 25: Points to one top level navigation item, 30..39: %-Voucher, (previously unitid, since V4), see also pointer below and ZeigerArtikel."
        },
    )
    hidden: str | None = field(
        default=None,
        metadata={
            "description": "If '1', the item should not be offered. Nevertheless, this item might be required to display existing orders or historical orders."
        },
    )
    ref_price: str | None = field(
        default=None,
        metadata={
            "description": "official comparison reference price as required by law (in europe) (Since Version2, its not a combined value proce/unit anymore, but just price. See below for the unit)"
        },
    )
    has_tn_url: str | None = field(
        default=None,
        metadata={
            "description": "<not empty> if a thumbnail url can be derived using the mechanism described in API.concepts.proxy.The value is a hash."
        },
    )
    has_info: str | None = field(
        default=None,
        metadata={
            "description": "1 if there is more information that can be obtained using the API.methods.item call."
        },
    )
    can_be_preordered: int | None = field(
        default=None,
        metadata={
            "description": "1 if that item can be pre-ordered should the delivery timeframe (see b_start/b_ende below) should not match the selected order date."
        },
    )
    oi: int | None = field(
        default=None,
        metadata={
            "description": "1 indicates that there is more information available from ecoinform , 2 indicates that there more info from DataNatuRe"
        },
    )
    b_start: str | None = field(
        default=None,
        metadata={
            "description": "start of order period. Use moment.js to parse this shortened iso8601 format from Version 2"
        },
    )
    b_ende: str | None = field(
        default=None, metadata={"description": "End of order period in Version 2"}
    )
    b_von: str | None = field(
        default=None, metadata={"description": "start of delivery period in Version 2"}
    )
    b_bis: str | None = field(
        default=None, metadata={"description": "end of delivery period in Version 2"}
    )
    weighted: str | None = field(
        default=None,
        metadata={
            "description": "If 1, it should trigger a additional warning to the custoemr, that additional measuring is done in order to exactly provide the price in a final delivery and invoice."
        },
    )
    order_stop_new: int | None = field(
        default=None,
        metadata={
            "description": "if 1 , it is ok to offer the given item for a delivery that follows the given selected delivery date (if the item-specific orderstop is over, or if the saleamount is over for saletype > 1)."
        },
    )
    pointer: int | None = field(
        default=None,
        metadata={
            "description": 'id for a unit, which is elsewhere transferred as String. In case of a pointer item (see itemtype above), this field carries the id of the entity this item points to. if "0", it points to the menu level. (previously unitid)'
        },
    )
    special_offer: int | None = field(
        default=None, metadata={"description": "if 1, this item is a special offer."}
    )
    search: str | None = field(
        default=None, metadata={"description": "additional serchterms"}
    )
    reference_unit: str | None = field(
        default=None, metadata={"description": "unit for the reference price"}
    )
    has_images: str | None = field(
        default=None,
        metadata={
            "description": "<not empty> if a one or more images exist for this item. The url(s) can be derived using the mechanism described in API.concepts.proxy.The value is a hash."
        },
    )
    packname: str | None = field(
        default=None,
        metadata={"description": "alternative internal name of this item (Since V4)"},
    )
    association: str | None = field(
        default=None,
        metadata={
            "description": 'aka "verband", eco verifying organization (Since V5)'
        },
    )
    source: str | None = field(
        default=None, metadata={"description": "origin or provider"}
    )
    regioflag: int | None = field(
        default=None, metadata={"description": '"1" if regional'}
    )
    amount_min: float | None = field(
        default=None,
        metadata={
            "description": "float, minimal amount to be ordered (default 0 == unset)"
        },
    )
    amount_max: float | None = field(
        default=None,
        metadata={
            "description": "float, max amount to be ordered (default 0 == unset)"
        },
    )
    amount_def: float | None = field(
        default=None,
        metadata={
            "description": "float, default amount to be ordered (default 0 == unset)"
        },
    )
    amount_step: float | None = field(
        default=None,
        metadata={
            "description": "float, increment value for simpel +/- controls (default 0 == unset)"
        },
    )
    image_count: int | None = field(
        default=None,
        metadata={
            "description": "a number from 0 to 9, telling how many extra images are available for this item (see API.concepts.proxy)"
        },
    )
    old_price: float | None = field(
        default=None,
        metadata={
            "description": "if >0, it represents an old price that can be shown strike-through"
        },
    )
    labels: str | None = field(
        default=None,
        metadata={
            "description": "space-delimited list of label id's. Label information is part of the API.methods.navigation response."
        },
    )
    has_related: int | None = field(
        default=None,
        metadata={
            "description": "1 if this item has references to other items (e.g. a recipe item). Use API.mentods.related to get more information."
        },
    )
    producer_id: int | None = field(
        default=None, metadata={"description": "references a producer or 0."}
    )
    has_nutrition_info: int | None = field(
        default=None,
        metadata={
            "description": "if 1, nutrition info can be requested and rendered from server"
        },
    )
    onsale: int | None = field(
        default=None,
        metadata={
            "description": "if > -1, the remaining items for sale (may be 0). if -1, then this item is not subject to a saleout ."
        },
    )
    cert: str | None = field(
        default=None,
        metadata={
            "description": "eco/bio certificate, if any. Some countries and regulations require a display"
        },
    )
    protected: int | None = field(
        default=None,
        metadata={
            "description": "if 1, the item can not be deleted from a preloaded cart and also prevent a cancellation of an order"
        },
    )
    unit_translated: str | None = field(
        default=None,
        metadata={
            "description": "like pos 3 (unit), but comes as translated version for display only.(since V9)"
        },
    )
    package: int | None = field(
        default=None,
        metadata={
            "description": "type of packageing (0:unset, 1:EINWEG, 2:MEHRWEG or 3:none/unknown)"
        },
    )
    eu_origin: str | None = field(
        default=None,
        metadata={
            "description": "eu origin indication, a microformat xxx:origintext ( POD: or PGI: or TSG:) (Since V10)"
        },
    )
    alcohol: int | None = field(
        default=None,
        metadata={
            "description": "product contains alcohol (if 1) , has commercial consequences."
        },
    )
    commercial_class: str | None = field(
        default=None, metadata={"description": "commercial class (Handelsklasse)"}
    )
    season: int | None = field(
        default=None,
        metadata={"description": "if 1, this product is seasonally available only."},
    )
    packstation: int | None = field(
        default=None, metadata={"description": "packstation reference"}
    )
    weight: float | None = field(
        default=None,
        metadata={
            "description": "if -1 , weight is unknown, 0 means the item is weight-less"
        },
    )
    rfactor: float | None = field(
        default=None,
        metadata={
            "description": "relation between the sale unit and the reference unit (0 if there is none)"
        },
    )
    max_discount: int | None = field(
        default=None,
        metadata={
            "description": "max discounts that can add up for this product. Default is 100."
        },
    )
    unit_hint: str | None = field(
        default=None,
        metadata={
            "description": "hint that should be placed next to the price (contains things like packages)"
        },
    )
    bulk_price: float | None = field(
        default=None, metadata={"description": "any bulkprice if defined for this item"}
    )
    bulk_amount: float | None = field(
        default=None,
        metadata={"description": "bulkprice is valid from this amount (in base units)"},
    )
    bulk_ref_price: str | None = field(
        default=None, metadata={"description": "reference price for this bulk price"}
    )
    noabo: int | None = field(
        default=None,
        metadata={"description": "if 1, this item is not available as subscription"},
    )
    active_a: str | None = field(
        default=None,
        metadata={
            "description": "Datetime in iso8601 giving the time after which the price changes"
        },
    )
    brand: str | None = field(
        default=None, metadata={"description": "the items brand name if known"}
    )
    references: str | None = field(
        default=None,
        metadata={
            "description": "references to external databases, may contain EAN (Gtin), ecorinformid or Bioid (Datanature). Data is provided only, of the calling IP is whitelistet."
        },
    )
    producer_name: str | None = field(
        default=None, metadata={"description": "name of the referenced producer"}
    )
    sale_type: int | None = field(
        default=None,
        metadata={
            "description": "0: no special sale, 1,2: always remaining are always relevant, 3,4: check remaining only after item order stop, see tourlimit"
        },
    )
    brand_name: str | None = field(
        default=None, metadata={"description": "name of the referenced dnr brand"}
    )


@dataclass
class Order(DataListModel):
    """
    Represents a customer order in the system.
    """

    id: int | None = field(default=None, metadata={"description": "The Order Id"})
    ddate: str | None = field(
        default=None,
        metadata={"description": "The (planned or happened) delivery date"},
    )
    state: str | None = field(
        default=None,
        metadata={
            "description": "one of: -2: Open order, unchangeable (by setting), -1: cancelled order, unchangeable, 0: regular open (outstanding) order, 1:fullfillment in process, unchangeable, 2: order fulfilled, unchangeable"
        },
    )
    tour_id: int | None = field(
        default=None,
        metadata={
            "description": "The ID of the customer delivery tour this order is booked on"
        },
    )
    cnote: str | None = field(
        default=None,
        metadata={
            "description": "Any arbitrary customer note related to the whole order"
        },
    )
    rnote: str | None = field(
        default=None,
        metadata={"description": "Any arbitrary message to the delivery team"},
    )
    osh: str | None = field(
        default=None,
        metadata={
            "description": "OrderStopHour - the time when this order can not be changed anymore. Note that individual items of that order may have their own (earlier) osh."
        },
    )
    last_changed: str | None = field(
        default=None,
        metadata={
            "description": "timestamp of last change, whether from a client or from the warehouse. Use it to sync that object before usage. (Since V4)"
        },
    )
    paid: int | None = field(
        default=None,
        metadata={
            "description": 'if "1", the order was paid or authorized with Paypal (Since V5)'
        },
    )
    delivery_cost: float | None = field(
        default=None,
        metadata={
            "description": "if -1 its unset, the shop system needs to calculate it from its settings. If > 0 , that's the cost to be used, if 0 , there exists an order position to express this. (Since V6)"
        },
    )
    has_alcohol: int | None = field(
        default=None,
        metadata={
            "description": "indicatesthat the order has at least one item that has alcohol or needs children checking (since V7)"
        },
    )
    adrid: int | None = field(
        default=None,
        metadata={"description": "reference to an address of a customer (since V8)"},
    )
    cid: int | None = field(
        default=None, metadata={"description": "customers id (since V9)"}
    )
    shipcode: str | None = field(
        default=None,
        metadata={
            "description": "code relevant to shipping or storage access (with V10)"
        },
    )
    used_paycode: int | None = field(
        default=None,
        metadata={
            "description": "Used Paymethod for this Order, (0: Unbekannt, 1: Lastschrift, 2: Paypal, 3: Vereinbart, 4: Zahlung tel. bestätigt, 5: Rechnung, 6: Vorkasse, 7: Barzahlung)"
        },
    )
    invnum: int | None = field(
        default=None,
        metadata={"description": "Invoice Number related to Order (with V11)"},
    )
    invtotal: float | None = field(
        default=None, metadata={"description": "Invoice total to pay (with V11)"}
    )


@dataclass
class Assorted(DataListModel):
    """
    A order position that defines an Assortment.

    A Assortment groups some items that typically are delivered together (aka Ökobox, Biobox, Abobox)

    See also See also API.methods.order, API.objects.Order

    While the Id references a Assortment, the assortment call provides all details of the contained items.
    """

    id: int | None = field(
        default=None, metadata={"description": "Id of the assortment"}
    )
    deleted: int | None = field(
        default=None,
        metadata={
            "description": 'Deletion Indicator. If that position is "1", the item is still listed but it should be assumed as being deleted already. Typically, it was not (yet) processed by PCG.'
        },
    )
    subscription_reference: int | None = field(
        default=None,
        metadata={"description": "pointing to an subscription, if != 0. Since V2."},
    )


@dataclass
class Assortment(DataListModel):
    """
    Describes one assortment.

    An assortment is a collection of items that make up e.g. a recipe. Or a fruit-box with a certain amount of fruits, but the exact fruits and their amount is or is not not yet specified.

    This object describes the base properties of such an assortment without its content (if its defined). Its content can be obtained using the API.methods.assortment call.
    """

    id: int | None = field(default=None, metadata={"description": "Assortment id"})
    name: str | None = field(
        default=None,
        metadata={"description": "Name of this assortment, possibly localized"},
    )
    description: str | None = field(
        default=None, metadata={"description": "The localized (long) description"}
    )
    person_count: int | None = field(
        default=None,
        metadata={
            "description": "The intended number of persons to consume this assortment"
        },
    )
    price: float | None = field(
        default=None, metadata={"description": "Price of that assortment"}
    )
    resolved: int | None = field(
        default=None,
        metadata={
            "description": 'If this field is "1", the assortment was already resolved to individual items. This means, if part of an order, this assortment will not be listed there anymore, but its individual items. AKA "Planned"'
        },
    )
    picture_url: str | None = field(
        default=None,
        metadata={
            "description": "if given, it represents a hash of an backend image (since V6, before always 1 if an image exists)"
        },
    )
    valid_from: datetime.datetime | None = field(
        default=None,
        metadata={
            "description": 'Start of the validity time frame (a date in JSON-ISO8601 Format, since version 3). May be "0", is there is no information or if not yet planned (aka "resolved").'
        },
    )
    valid_to: datetime.datetime | None = field(
        default=None,
        metadata={
            "description": 'End of validity time frame (a date in JSON-ISO8601 Format, since version 3). May be "0", is there is no information or if not yet planned (aka "resolved").'
        },
    )
    item_count: int | None = field(
        default=None,
        metadata={
            "description": "Number of Items in this assortment. May be 0 if the assortment is not yet planned in detail. (Since V4)"
        },
    )
    group_id: int | None = field(
        default=None,
        metadata={
            "description": "reference to an API.objects.AssortmentGroup. Such a group might group Boxes by similar content or slogan (e.g. Mother-Child-Box or Office-Fruits)"
        },
    )
    variant_id: int | None = field(
        default=None,
        metadata={
            "description": "reference to a variant. A variant can further group boxes (e.g. by size: small/medium/big)"
        },
    )
    short_info: str | None = field(
        default=None, metadata={"description": "The localized (short) description"}
    )
    is_hidden: bool | None = field(
        default=None, metadata={"description": "true or false. Dont offer if false."}
    )
    pack_station: int | None = field(
        default=None,
        metadata={
            "description": "if > 0, defines the packing station, any minimum order value is calculated against"
        },
    )
    thumb_hash: str | None = field(
        default=None,
        metadata={
            "description": "if given, it represents a hash of an backend image (since V6, before always 1 if an image exists)"
        },
    )


@dataclass
class AssortmentGroup(DataListModel):
    """
    Describes one assortment group.

    Assortments can be grouped in various ways (by Topic or by Size). If an assortment is part of a group, the web shop might decide to show the description of that group instead of the individual descriptions.
    """

    id: int | None = field(default=None, metadata={"description": "Assortment Id"})
    name: str | None = field(
        default=None,
        metadata={"description": "Name of this assortment, possibly localized"},
    )
    description: str | None = field(
        default=None, metadata={"description": "The localized (short) description"}
    )
    count: int | None = field(
        default=None, metadata={"description": "number of assortments in this group"}
    )
    type: int | None = field(
        default=None,
        metadata={
            "description": 'type or grouping: 0: group ("roots") 1:variant ("small"), 2: Container ("Boxes with greens")'
        },
    )
    has_image: bool | None = field(
        default=None,
        metadata={"description": "1 if there is a image assigned to this Group"},
    )
    has_thumb: bool | None = field(
        default=None, metadata={"description": "if a thumbnail exists"}
    )
    search: str | None = field(default=None, metadata={"description": "searchterms"})
    hidden: bool | None = field(
        default=None,
        metadata={
            "description": "1 if effectively hidden (because all content is hidden)"
        },
    )


@dataclass
class AssortmentPosition(DataListModel):
    """
    Provides an Mapping between the API.objects.Assortment and the API.objects.Item and is very similar to API.objects.CartItem.
    """

    assortment_id: int | None = field(
        default=None, metadata={"description": "the reference to the assortment"}
    )
    item_id: int | None = field(
        default=None, metadata={"description": "the reference to the item"}
    )
    amount: float | None = field(
        default=None, metadata={"description": "amount in units"}
    )
    unit: str | None = field(default=None, metadata={"description": "clear-text unit"})
    discount: float | None = field(
        default=None,
        metadata={
            "description": "discount that may apply to this item within an assortment in percentage (-x% means a discount of x)."
        },
    )


@dataclass
class AuxDate(DataListModel):
    """
    Auxiliary date object.
    """

    name: str | None = field(
        default=None,
        metadata={"description": "the name of the event(calendar summary field)"},
    )
    description: str | None = field(
        default=None, metadata={"description": "long calendar description"}
    )
    from_date: str | None = field(
        default=None, metadata={"description": "starting date"}
    )
    to_date: str | None = field(default=None, metadata={"description": "ending date"})


@dataclass
class Box(DataListModel):
    """
    Refund Boxes registered for a given user.
    """

    id: str | None = field(default=None, metadata={"description": "Box id"})
    since: datetime.datetime | None = field(
        default=None, metadata={"description": "at customer since"}
    )


@dataclass
class CartItem(DataListModel):
    """
    An Item (to be) placed into current) Cart
    """

    item_id: int | None = field(
        default=None, metadata={"description": "The item this position refers to."}
    )
    amount: float | None = field(
        default=None,
        metadata={
            "description": "The amount it item-suitable units (can be an alternative unit, see next field)"
        },
    )
    unit: str | None = field(
        default=None,
        metadata={
            "description": "the unit this position is measured in (can be a alternative unit for this item)"
        },
    )
    note: str | None = field(
        default=None,
        metadata={
            "description": "Note related to this position. Its source depends on the context (might be form the customer or the system)"
        },
    )


@dataclass
class CustomerInfo(DataListModel):
    """
    Customer information object.
    """

    id: int | None = field(
        default=None, metadata={"description": "Customer identifier"}
    )
    name: str | None = field(default=None, metadata={"description": "Customer name"})
    email: str | None = field(
        default=None, metadata={"description": "Customer email address"}
    )


@dataclass
class DDate(DataListModel):
    """
    Provides Details of a Delivery Date. All DDates are associated with a given tour by its tourid.

    See also API.methods.tour, API.methods.tours
    """

    id: int | None = field(
        default=None,
        metadata={
            "description": "The Id of the DDate Object. Its is required as reference for other information elsewhere. Occasionally this is referred to as Tour-Instance-Id."
        },
    )
    tour_id: int | None = field(
        default=None, metadata={"description": "The reference to the API.objects.Tour"}
    )
    delivery_date: str | None = field(
        default=None,
        metadata={"description": "The Date of the delivery in YYYY-MM-DD form"},
    )
    week: int | None = field(
        default=None,
        metadata={
            "description": "Week of the delivery Day. Note that this might depend on the locale."
        },
    )
    packing_day: str | None = field(
        default=None,
        metadata={
            "description": "The date when the delivery is supposed to be packed."
        },
    )
    main_day: int | None = field(
        default=None,
        metadata={
            "description": 'For Selection by a customer, there can be main and extraordinary delivery days. Main delivery days have a "1" here.'
        },
    )
    note: str | None = field(
        default=None,
        metadata={
            "description": "arbitrary notes associated with that tour on this date."
        },
    )
    customers: int | None = field(
        default=None,
        metadata={
            "description": "The number of customer orders being already prepared in that tour. This number represents the current plan, it may be set or changed until just before the tour starts. Since Version 2"
        },
    )
    orders: int | None = field(
        default=None,
        metadata={
            "description": "The number of orders currently scheduled for this tour. This number may change until a tour is final. (Since V3)"
        },
    )


@dataclass
class Delivery(DataListModel):
    """
    One tour consists of many deliveries. This object provides information about one delivery, such as the customer to be delivered, the order served and other things relevant to the person or process that works on the delivery.

    See also API.methods.tour, API.objects.Address

    The sequence in the Delivery Object defines the tour sequence as planned elsewhere.
    """

    id: int | None = field(
        default=None,
        metadata={
            "description": " Internal Id of this delivery record. This id is needed if the order of the delivery within the tour needs to be changed."
        },
    )
    customer_id: int | None = field(
        default=None,
        metadata={"description": "The Id of the customer within the system"},
    )
    delivery_address_id: int | None = field(
        default=None,
        metadata={
            "description": "If given and not 0 , the address of this customer should be used instead of the addressid (below) (UseCase: Delivery to A goes to B's house too). If this field is 0, there is not alternative delivery location used (this is the regular case). Since V13: -2: private Depot, -3: public Depot, -4: Depot, but full"
        },
    )
    address_name: str | None = field(
        default=None,
        metadata={
            "description": 'references the Address of the customer. A customer may have multiple addresses. "null" (or empty) defines the "default address to be used for this customer.'
        },
    )
    order_id: int | None = field(
        default=None,
        metadata={
            "description": 'The reference to the order that gets fulfilled with that delivery. If that field is "0", the respective order was not yet transferred to the database, which indicates a timing problem at the packer\'s source.'
        },
    )
    todo_hint: str | None = field(
        default=None,
        metadata={
            "description": "Hint to the driver on what needs to be done when arriving with the parcel"
        },
    )
    way_hint: str | None = field(
        default=None,
        metadata={
            "description": "Hint to find the right way, beside the address and the geo coords given in the address reference"
        },
    )
    done_at: str | None = field(
        default=None,
        metadata={
            "description": "Timestamp that tells if the delivery was done already and when."
        },
    )
    box_name: str | None = field(
        default=None,
        metadata={
            "description": "ID (Label, barcode) of the pack box containing the goods (since Version 2); may not be authoritative, better check the name provided in the order position. Depending on the settings, a virtual boxname is provided (that will match the one in the Positions-Object)"
        },
    )
    packstation_id: int | None = field(
        default=None,
        metadata={
            "description": "References the Packing Station for the items in that delivery. '-1' means undefined. (since version 3)"
        },
    )
    addressid: int | None = field(
        default=None,
        metadata={
            "description": "references the address to be used with that delivery"
        },
    )
    prediction: int | None = field(
        default=None,
        metadata={
            "description": "prediction of minutes needed to arrive at this address from previous position. If 0, no prediction is available. Since V5"
        },
    )
    box_count: int | None = field(
        default=None,
        metadata={
            "description": "Number of packaging boxes assigned to this customer (provided only in preview calls)"
        },
    )
    box_type: str | None = field(
        default=None,
        metadata={"description": "type of box (provided in some calls)"},
    )
    last: str | None = field(
        default=None,
        metadata={
            "description": "last assignment, can be used for ordering. May be empty, if not known."
        },
    )
    weight: float | None = field(
        default=None,
        metadata={
            "description": "total weight for goods in this Box/Delivery. A value of 0.0 indicates that no value can be provided. Otherwise its at least 0.0001"
        },
    )
    weigh_quality: int | None = field(
        default=None,
        metadata={
            "description": "the percentage of positions, that do have a good estimation. 100% means the weight for this delivery should be pretty accurate."
        },
    )
    position: str | None = field(
        default=None,
        metadata={
            "description": "position indicator (sequence, may be used as label too), since V13"
        },
    )


@dataclass
class DeliveryState(DataListModel):
    """
    Delivery state object.
    """

    cid: int | None = field(
        default=None,
        metadata={
            "description": "(shop side) Customer ID if allowed to see, otherwise 0"
        },
    )
    estimatedArrival: str | None = field(
        default=None,
        metadata={
            "description": "timestamp of estimated arrival time at this Customer ID"
        },
    )
    prediction: int | None = field(
        default=None,
        metadata={
            "description": "estimated minutes until delivery to this Customer from the last one"
        },
    )
    lat: float | None = field(
        default=None,
        metadata={"description": "latitude of delivery point (if eligible)"},
    )
    lng: float | None = field(
        default=None,
        metadata={"description": "longitude of delivery point (if eligible)"},
    )
    done: int | None = field(
        default=None,
        metadata={"description": "if provided, this delivery was already done."},
    )
    oid: int | None = field(
        default=None,
        metadata={"description": "optional order references (if eligible)"},
    )


@dataclass
class DeselectedGroup(DataListModel):
    """
    Deselected group object.
    """

    name: str | None = field(
        default=None,
        metadata={"description": "the name of the Group (defined within PCG)"},
    )
    group_id: int | None = field(
        default=None,
        metadata={"description": "the group id at the time of keeping this record"},
    )


@dataclass
class DeselectedItem(DataListModel):
    """
    Deselected item object.
    """

    id: str | None = field(
        default=None,
        metadata={
            "description": "the name of the Item (at the time of saving it, may be a textual hint only"
        },
    )
    item_id: int | None = field(
        default=None,
        metadata={"description": "the item id at the time of keeping this record"},
    )


@dataclass
class Discount(DataListModel):
    """
    Discount object.
    """

    id: int | None = field(
        default=None, metadata={"description": "Discount identifier"}
    )
    name: str | None = field(default=None, metadata={"description": "Discount name"})
    percentage: float | None = field(
        default=None, metadata={"description": "Discount percentage"}
    )


@dataclass
class Favourite(DataListModel):
    """
    Favourite item object.
    """

    entity: int | None = field(
        default=None,
        metadata={
            "description": "the entity, one of the values listed in API.objects.NavigationDetail"
        },
    )
    id: int | None = field(default=None, metadata={"description": "the entity's id."})


@dataclass
class Group(DataListModel):
    """
    Items are naturally a member of exactly one category (aka group).

    See also API.methods.groups, API.methods.navigation, API.objects.Item.
    """

    id: int | None = field(
        default=None,
        metadata={
            "description": "(internal) ID of this category. Used as reference from items."
        },
    )
    name: str | None = field(
        default=None, metadata={"description": "(localized) Name of this category."}
    )
    infotext: str | None = field(
        default=None,
        metadata={"description": "(localized) description text of this category."},
    )
    count: int | None = field(
        default=None,
        metadata={
            "description": "The number of Items in that category. This number is depended on the executing user and the timing constraints of the items. It refelcts only items directly in that group."
        },
    )
    subgroup_count: int | None = field(
        default=None,
        metadata={
            "description": "The number of items in all subgroups (if there are any). (since V2)"
        },
    )
    labels: str | None = field(
        default=None,
        metadata={
            "description": "a comma-separated list of API.objects.Labels that are assigned to this item (Since V3)."
        },
    )
    has_img: int | None = field(
        default=None,
        metadata={"description": "1 if the group has an big image assigned (Since V4)"},
    )
    has_tn: int | None = field(
        default=None,
        metadata={
            "description": "1 if the group has an small (icon-) image assigned (Since V4)"
        },
    )


@dataclass
class KeyValue(DataListModel):
    """
    An Object to transmit arbitrary properties. In order to keep the general Conract in this API (transferring Data Lists), occasionally this Object is used in addition to other Data Lists in the response..
    """

    key: str | None = field(default=None, metadata={"description": "Key name"})
    value: str | None = field(default=None, metadata={"description": "Key value"})


@dataclass
class Pause(DataListModel):
    """
    This Object describes a subscription pause.

    See also API.methods.dates
    """

    id: int | None = field(
        default=None, metadata={"description": "referenceable id for this pause record"}
    )
    start_date: datetime.date | None = field(
        default=None, metadata={"description": "Pause start date"}
    )
    end_date: datetime.date | None = field(
        default=None, metadata={"description": "Pause end date"}
    )
    dt: datetime.datetime | None = field(
        default=None, metadata={"description": "Date/time when entered"}
    )
    note: str | None = field(default=None, metadata={"description": "arbitrary note"})
    type: int | None = field(
        default=None,
        metadata={
            "description": "pause-type: 0: general stop; 1: stop for a specific address (refid contains the id of that address); 2: stop for a assortment subscription; 3: stop for a item subscription"
        },
    )
    ref_id: int | None = field(
        default=None, metadata={"description": "reference as defined by type"}
    )


@dataclass
class Position(DataListModel):
    """
    Provides the order details, usually obtained through the API.methods.order-Method. Its the same for a position or a permanentPosition when provided in that call.
    """

    id: int = field(default=0, metadata={"description": "The Item Reference."})
    amount: float = field(
        default=0.0, metadata={"description": "The Amount with respect to the Units."}
    )
    unit_name: str = field(
        default="",
        metadata={
            "description": "The clear text name of the unit (typically localized for the Shop, possibly for the locale of the Customer)"
        },
    )
    price: float = field(
        default=0.0,
        metadata={
            "description": "Price in Shop Units, possibly localized for the given customer of that order."
        },
    )
    assortment_reference_id: int = field(
        default=0,
        metadata={
            "description": "If not 0,it represents the a assortment, this position was generated from. For other values see Abosystem."
        },
    )
    deleted: int = field(
        default=0,
        metadata={
            "description": 'Deletion Indicator. If that position is "1", the item is still listed but it should be assumed as being deleted already. Typically, it was not (yet) processed by PCG.'
        },
    )
    pack_station: str | None = field(
        default=None,
        metadata={
            "description": "The name of the packstation that this position got packed. Since Version 2, omitted if empty, removed in Version 4!"
        },
    )
    pack_station_id: int = field(
        default=0,
        metadata={
            "description": "The Id of the packstation. Since version 4 instead of PackStation"
        },
    )
    packed_late: int = field(
        default=0,
        metadata={
            "description": 'if not "0", this indicates that this position need to be packed "late", usually from the driver delivering the goods. Since Version 2,"0" is default'
        },
    )
    driver_note: str | None = field(
        default=None,
        metadata={
            "description": "Hint to the Driver, related to that position. Since Version 2, may be empty if disabled by PCG. Since Version 5 this field is only provided non empty if there is data, the driver hint flag set and if "
        },
    )
    box_name: str | None = field(
        default="",
        metadata={
            "description": "Name/Label of the delivery box used to pack this item.Since Version 3, may be a empty String , if unknown"
        },
    )
    delivered_amount: float = field(
        default=0.0,
        metadata={
            "description": "The amount of good actually delivered. This might differ from the ordered amount. This value is only available shortly before the order is being delivered. Since Version 6"
        },
    )
    subscription_reference_id: int = field(
        default=0,
        metadata={
            "description": "if this item comes from a subscription, this id references it.It may point to a assortment subscription (if AssortmentReferenceId > 0) or item subscription. Subscription data is provided in the dates "
        },
    )
    discount: int = field(
        default=0,
        metadata={"description": "Discount that resulted in the price given above"},
    )
    protection: int = field(
        default=0,
        metadata={
            "description": "an id that tells about changability of this position. Currently there is 50 (can not be changed) and 60 (out of stock). In both cases, that position can not be changed, but the order may still be canc"
        },
    )
    note: str | None = field(
        default=None,
        metadata={
            "description": "note related to the position, typically a message from or to the customer."
        },
    )
    base_unit: str | None = field(
        default=None,
        metadata={
            "description": "a potentially different baseunit for this positions item (with V9)"
        },
    )


@dataclass
class PermanentPosition(Position):
    """
    The PermanentPosition Object is the same than the API.objects.Position object. Please check there..
    """


@dataclass
class RelatedItem(DataListModel):
    """
    Related item object.
    """

    id: int | None = field(
        default=None, metadata={"description": "Related item relationship identifier"}
    )
    item_id: int | None = field(
        default=None, metadata={"description": "Reference to primary item"}
    )
    related_item_id: int | None = field(
        default=None, metadata={"description": "Reference to related item"}
    )


@dataclass
class ShopDate(DataListModel):
    """
    Shop date object.
    """

    order_id: int = field(
        default=0,
        metadata={
            "description": "if the object specifies an existing order, this is the order id, which is > 0. If this number id -1, it denotes that there is a subscription planned to be executed on that date. 0 means, that nothing "
        },
    )
    order_state: int = field(
        default=0,
        metadata={
            "description": "In case this object denotes an order (id > 0), the meaning is -1: cancelled, 0: pending, 1: in preparation/in delivery , 2 done. If the object just specifies a day (without an order), this value is always 0"
        },
    )
    delivery_date: datetime.date = field(
        default=datetime.date.today(),
        metadata={
            "description": "The date of the order delivery or the possible delivery day in format YYYY-MM-DD"
        },
    )
    delivery_week: int | None = field(
        default=None, metadata={"description": "the week of the delivery day"}
    )
    last_order_change: datetime.datetime | None = field(
        default=None,
        metadata={
            "description": "individual positions may have even more restrictive timings, but after that time, no change is allowed anymore. This has to be ensured by the clients user interface. Can be empty for orders in the past"
        },
    )
    tour_id: int | None = field(
        default=None,
        metadata={
            "description": "the ID of the delivery tour. Tour-Information can be obtained by the gettours-Method"
        },
    )
    note: str | None = field(
        default=None,
        metadata={
            "description": "Notes related to that delivery (in case of an order) or the tour (in case, no order exists yet)."
        },
    )
    count: int | None = field(
        default=None,
        metadata={
            "description": "the number of order positions (if the date has an order)"
        },
    )
    is_changeable: int = field(
        default=0,
        metadata={
            "description": "Value is 1 if the order can be changed; 0 otherwise. There are many reasons why an order can not be changed anymore using that API."
        },
    )
    total: float | None = field(
        default=None, metadata={"description": "The sum in the shop's currency."}
    )
    delivery_cost: float | None = field(
        default=None,
        metadata={
            "description": "The extra cost that may apply for a delivery to the address (in that tour). The final value further depends on the settings for the Shop (add always or only if below a certain value) and possibly the total cart value. Note, this value may be caller and country dependent. Since V2"
        },
    )
    delivery_cost_limit: float | None = field(
        default=None,
        metadata={
            "description": 'Delivery Costs apply if the order total is below this value. The special value of "999" tells that the delivery costs apply regardless of the order value.'
        },
    )
    delivery_cost_when: int = field(
        default=0,
        metadata={
            "description": "when 0 it applies never, 1 means that DeliveryCostLimit applies."
        },
    )
    last_changed: datetime.datetime | None = field(
        default=None,
        metadata={
            "description": "Iso date of the last change on server side, if that record is an order (see Orderid above). Otherwise an empty string."
        },
    )
    last_cancel: datetime.datetime | None = field(
        default=None,
        metadata={"description": "last datetime when this order can be cancelled"},
    )
    assigned: int = field(
        default=0,
        metadata={
            "description": "if 1, this tour is already assigned to the customer; otherwise its an optional tour"
        },
    )
    hidden: str | None = field(
        default=None,
        metadata={
            "description": "tour is not normally available for the customer; its referenced only, because it has orders (V3)"
        },
    )
    min_order_value: float = field(
        default=0.0,
        metadata={
            "description": 'minimal order value for the calling customer for the given address/tour/date. -1 means "unset". (V4)'
        },
    )
    address_id: int | None = field(
        default=None, metadata={"description": "internal address id"}
    )
    address_hint: str | None = field(
        default=None, metadata={"description": "address name or hint"}
    )
    depot_full: int = field(
        default=0,
        metadata={
            "description": "if 1, this address is a depot but its full for the given date"
        },
    )
    show_tour_note: int = field(
        default=0,
        metadata={
            "description": "if 1, alert the customer on the tour note (time frame)"
        },
    )
    no_pre_order: int = field(
        default=0,
        metadata={"description": "if 1, no preorders can be taken on that day"},
    )
    fix_date: str | None = field(
        default=None,
        metadata={
            "description": "the original delivery date, in cas the date was moved (since V5)"
        },
    )
    address_street: str | None = field(
        default=None,
        metadata={"description": "cleartext delivery address street (since V6)"},
    )
    address_zip: int | None = field(
        default=None, metadata={"description": "cleartext delivery address zip"}
    )
    address_city: str | None = field(
        default=None, metadata={"description": "cleartext delivery address city"}
    )
    delivery_address_id: int = field(
        default=0,
        metadata={
            "description": "reference to another addressid (depot), or -1 (no reference) , -2 (this address is a private Depot, -3 (this address is a public depot)"
        },
    )
    max_order_value: float = field(
        default=0.0,
        metadata={
            "description": "overrides users order limit on a per date or per address base"
        },
    )
    is_packed: int = field(
        default=0,
        metadata={
            "description": "if treu, this is a reference date only: its not available for a selection by the user, it serves just a reference for existing orders"
        },
    )


@dataclass
class ShopUrl(DataListModel):
    """
    Provides some information about a online shop tenant. Its intended to be used to provide a nicely formatted opener screen for a online shop.
    """

    display_name: str | None = field(
        default=None,
        metadata={
            "description": "The display name of the shop, as configured in the ShopSettings."
        },
    )
    http_url: str | None = field(
        default=None,
        metadata={
            "description": "The base url, all calls to other operations need to get prefixed by this path (an address at oekobox-online or proxie'd to oekobox-online)"
        },
    )
    https_url: str | None = field(
        default=None,
        metadata={
            "description": "The SSL Url, should one be configured (an address at oekobox-online or proxie'd to oekobox-online)"
        },
    )
    site_url: str | None = field(
        default=None,
        metadata={
            "description": "The URL pointing to the HomeSite of the given Shop. Useful as a link reference."
        },
    )
    logo_url: str | None = field(
        default=None,
        metadata={
            "description": "if 1, a logo exists that can be fetched from https://oekobox-online.DE|EU/v3/shop/SYSNAME/f.px?bs.i=logo"
        },
    )
    sysname: str | None = field(
        default=None,
        metadata={"description": "The (internal) System name (Since Version 2)"},
    )
    is_test_mode: str | None = field(
        default=None,
        metadata={
            "description": '"1", if the system is currently addressed in testmode (since V3)'
        },
    )
    lat: float | None = field(
        default=None,
        metadata={
            "description": "Geolocation of the main site (as set up in the configuration of the online shops) , Latitude (since V4)"
        },
    )
    lng: float | None = field(
        default=None, metadata={"description": "Geolocation , Longitude (since V4)"}
    )
    dbid: int | None = field(
        default=None,
        metadata={
            "description": "internal reference to the database (since V4) 0->DE, 1->EU"
        },
    )
    anw_id: int | None = field(
        default=None, metadata={"description": "backend customer id (since V5)"}
    )
    seo_desc: str | None = field(
        default=None, metadata={"description": "SEO Description"}
    )
    seo_cities: str | None = field(
        default=None,
        metadata={"description": 'Supported cities, "DE*" means shipping germany-wide'},
    )
    seo_organic: int | None = field(
        default=None,
        metadata={"description": "if 1, shop sells solely organic products"},
    )


@dataclass
class SubGroup(DataListModel):
    """
    Sub group object.
    """

    id: int | None = field(
        default=None, metadata={"description": "Sub group identifier"}
    )
    name: str | None = field(default=None, metadata={"description": "Sub group name"})
    parent_group_id: int | None = field(
        default=None, metadata={"description": "Reference to parent group"}
    )


@dataclass
class SubGroupMap(DataListModel):
    """
    Sub group mapping object.
    """

    id: int | None = field(
        default=None, metadata={"description": "Sub group mapping identifier"}
    )
    subgroup_id: int | None = field(
        default=None, metadata={"description": "Reference to sub group"}
    )
    item_id: int | None = field(
        default=None, metadata={"description": "Reference to item in sub group"}
    )


@dataclass
class Subscription(DataListModel):
    """
    Subscription object.
    """

    id: int | None = field(
        default=None, metadata={"description": "internal subscription id"}
    )
    item_id: int | None = field(
        default=None,
        metadata={
            "description": "the Item that shall be delivered regularly. If negative, a Assortment is referenced."
        },
    )
    amount: str | None = field(
        default=None,
        metadata={
            "description": 'amount. For Assortments, this field cvan be an empty String , it indicates "piece".'
        },
    )
    unit: str | None = field(
        default=None, metadata={"description": "localized unit name"}
    )
    start: str | None = field(
        default=None, metadata={"description": "start of the subscription"}
    )
    end: str | None = field(
        default=None, metadata={"description": "end date of the subscription"}
    )
    period: int | None = field(
        default=None,
        metadata={"description": "periodicy of the delivery in weeks (1..4)"},
    )
    last_delivery: str | None = field(
        default=None, metadata={"description": "date of last delivery"}
    )
    tour_id: int | None = field(
        default=None,
        metadata={"description": "the tour that this item is to be delivered on"},
    )
    notes: str | None = field(default=None, metadata={"description": "arbitrary nodes"})
    season: int | None = field(
        default=None,
        metadata={
            "description": "if 1, the underlying item may not always be available"
        },
    )
    mperiod: int | None = field(
        default=None,
        metadata={
            "description": "alternatively to period, a monthly period. Remember, monthly is not the same than a 4 weeks cycle."
        },
    )
    address_id: int | None = field(
        default=None,
        metadata={
            "description": "address reference (see API.objects.ShopDate). Subscriptions might be for different delivery addresses."
        },
    )


@dataclass
class Tour(DataListModel):
    """
    Tour object representing delivery tours.
    """

    id: int | None = field(
        default=None, metadata={"description": "The internal ID of the tour"}
    )
    name: str | None = field(
        default=None, metadata={"description": "The name of the tour"}
    )
    description: str | None = field(
        default=None,
        metadata={"description": "The human readable description of the tour."},
    )
    zipcodes: list[str] | None = field(
        default=None,
        metadata={
            "description": "a comma separated list of zipcodes that this delivery tour covers. Values here depend on the features being used in the warehouse. Thus the exact meaning of the code may be locale specific. (Since V1)"
        },
    )
    driver_note: str | None = field(
        default=None, metadata={"description": "textual advice for the driver"}
    )
    next_date: str | None = field(
        default=None,
        metadata={
            "description": "XML Schema time stamp (V4), not available in all calls"
        },
    )
    hidden: str | None = field(
        default=None,
        metadata={
            "description": "1, if that tour is normally not available for a customer to pick. If its there, its an exceptional case (like an exceptional sunday delivery) and there are currently orders for that tour (and customer"
        },
    )
    incomplete: int | None = field(
        default=None, metadata={"description": "number of incomplete records"}
    )
    color: str | None = field(
        default=None, metadata={"description": "color indicator for maps"}
    )
    poly: str | None = field(
        default=None,
        metadata={
            "description": "polygon definition, format like in geojson , but without features"
        },
    )
    poly1: str | None = field(
        default=None,
        metadata={
            "description": "(Pos 10) alternative, added from backend. To be used if poly is empty or the null-Polygon"
        },
    )
    target: str | None = field(
        default=None,
        metadata={
            "description": "1: for companies, 2: for private customers, 0: no specific"
        },
    )
    has_poly: str | None = field(
        default=None,
        metadata={"description": "if the polygon represents a real tour area"},
    )
    has_poly1: str | None = field(
        default=None,
        metadata={"description": "if the polygon represents a real tour area"},
    )
    count: int | None = field(
        default=None, metadata={"description": "current position count"}
    )
    visible: str | None = field(
        default=None, metadata={"description": "if the tour is available for customers"}
    )
    bike: str | None = field(
        default=None,
        metadata={"description": "1 if this tour is primarily served by bikes"},
    )


@dataclass
class UserInfo(DataListModel):
    """
    User information object.
    """

    authentication_state: str | None = field(
        default="NONE",
        metadata={
            "description": "NONE: nothing known; INVALID: (long term-) Cookie exists, but seems to be invalid (perhaps password changed meanwhile); VALID: valid (long term-) cookie exists, but user is not yet logged on; AUTH: User is authenticated; SUPER: the authenticated user is a super user,; ADMIN: the authenticated user is in a admin role."
        },
    )
    user_id: int | None = field(
        default=None, metadata={"description": "The userid in the shop"}
    )
    opener: str | None = field(
        default=None, metadata={"description": "Title or addressing opener"}
    )
    firstname: str | None = None
    lastname: str | None = field(
        default=None, metadata={"description": "lastname (Position 5)"}
    )
    role: str | None = field(
        default=None,
        metadata={
            "description": "The role this user has in the shop system (since version 2): 0: regular customer (AuthenticationState is AUTH or VALID); 1:Web-Admin; 2:Driver; 3,5,6:Driver with additional permission to modify Positions; 4: Admin (All company wide permissions)"
        },
    )
    debug: str | None = field(
        default=None,
        metadata={
            "description": "Debuglevel to be used for any client app for THIS client (since version 3):"
        },
    )
    driver_load: str | None = field(
        default=None,
        metadata={
            "description": "App Setting, a value of 0 (unused),1,2,3. Controls the display behavior at load time (if this user is in role driver, since version 4)"
        },
    )
    driver_serve: str | None = field(
        default=None,
        metadata={
            "description": "App Setting, a value of 0 (unused),1,2,3. Controls the display behavior at load time (if this user is in role driver, since version 4)"
        },
    )
    driver_next: int = field(default=0, metadata={"description": "Position 10"})
    driver_next_load: str | None = field(
        default=None,
        metadata={
            "description": "App Setting, if 1, automatically mark position as loaded when switching to the next address (if this user is in role driver, since version 6)"
        },
    )
    driver_tracking: str | None = field(
        default=None,
        metadata={
            "description": "App Setting, enables tracking for the given user (aka driver, since Version 7 )"
        },
    )
    pref_asdc: str | None = field(
        default=None,
        metadata={
            "description": "User Preference, if 1, a changed order will be submitted automatically when the user switches away ( since Version 8 )"
        },
    )
    email: str | None = field(
        default=None, metadata={"description": "primary Email Address (Since V8)"}
    )
    email1: int = field(
        default=0, metadata={"description": "secondary Email Address (Since V8)"}
    )
    phone: str | None = field(
        default=None, metadata={"description": "primary phone number (Since V8)"}
    )
    phone_mobile: str | None = field(
        default=None, metadata={"description": "secondary phone number (Since V8)"}
    )
    country: str | None = field(
        default=None, metadata={"description": "ISO country code (Since V8)"}
    )
    zip: str | None = field(
        default=None, metadata={"description": "country specific zip code"}
    )
    city: str | None = field(default=None, metadata={"description": "city"})
    street: str | None = field(
        default=None, metadata={"description": "street address including house number"}
    )
    account_number: int | None = field(
        default=None,
        metadata={
            "description": "account number. When this object comes as response, the coount number comes as dotted with only the last digits readable."
        },
    )
    paycode: int | None = field(
        default=None,
        metadata={
            "description": "payment option used/desired: 0: unknown; 1: sepa; 2: paypal; 3: other (not unknown); 4: phone; 5: Invoice"
        },
    )
    note: str | None = field(
        default=None,
        metadata={
            "description": "arbitrary note, typically provided from customer (once/at registration)"
        },
    )
    placecode: str | None = field(
        default=None,
        metadata={
            "description": "codes the storage, when nobody is at home. Concatenated Bit Pattern: 0: nothing known, 1: I am usually at home (pc=1,5,7), 2: If I am not at home, store at... (see note, pc=2,3,6,7), 3 :If I am not at home,hand over to neighbour.. (see note pc=4,6,7)"
        },
    )
    sepa_info: str | None = field(
        default=None,
        metadata={"description": "number and date of a SEPA system mandate."},
    )
    delivery_name: str | None = field(
        default=None,
        metadata={"description": "name for an optional different delivery address"},
    )
    delivery_zip: str | None = field(
        default=None,
        metadata={
            "description": "zip code for an optional different delivery address. If this delivery values are provided, the main address becomes the invoicing address."
        },
    )
    delivery_city: str | None = field(
        default=None,
        metadata={"description": "city for an optional different delivery address"},
    )
    delivery_street: str | None = field(
        default=None,
        metadata={"description": "street for an optional different delivery address"},
    )
    company: str | None = field(
        default=None,
        metadata={"description": "optional company name (for the first address)"},
    )
    no_ad: int = field(
        default=0,
        metadata={"description": 'dont send adverticements to this user if "1"'},
    )
    place_note: str | None = field(
        default=None, metadata={"description": "Delivery placement note (V9)"}
    )
    pref_abocart: int = field(
        default=0,
        metadata={
            "description": "User Preference: show or hide inactive subscription positions in cart view (V10)"
        },
    )
    pref_partial: int = field(
        default=0, metadata={"description": "show or hide partial delivery pauses"}
    )
    department: str | None = field(
        default=None, metadata={"description": "customers department"}
    )
    vat_id: str | None = field(default=None, metadata={"description": "of company"})
    delivery_company: str | None = field(
        default=None,
        metadata={"description": "company of (first) delivery address (if it exists)"},
    )
    delivery_department: str | None = field(
        default=None,
        metadata={
            "description": "department of (first) delivery address (if it exists)"
        },
    )
    driver_note: str | None = field(
        default=None, metadata={"description": "individual notes for the driver (V13)"}
    )
    balance: float | None = field(
        default=None, metadata={"description": "customer account balance"}
    )
    traceme: int = field(
        default=0, metadata={"description": "user denied analytics tracking"}
    )
    trivial_warning: int = field(
        default=0, metadata={"description": "user seems to use a very simple password"}
    )
    order_limit: float | None = field(
        default=None,
        metadata={"description": "total limit of open orders (sum) (Setting)"},
    )
    needs_tc: int = field(
        default=0,
        metadata={"description": "User need to reconfirm T&C (as it changed)"},
    )
    bic: str | None = field(
        default=None, metadata={"description": "BIC banking code (non german users)"}
    )
    active: int = field(
        default=1,
        metadata={
            "description": "customer may be marked as not active (==0) in the backend"
        },
    )
    boxcnt: int = field(
        default=0, metadata={"description": "number of assigned refund boxes (V16)"}
    )
    rgroup_until: str | None = field(
        default=None, metadata={"description": "member of discount group until"}
    )
    notification_order: int = field(
        default=0, metadata={"description": "(1) (see below) order confirmation"}
    )
    notification_cart: int = field(
        default=0, metadata={"description": "(2)cart submit forgotten reminder enabled"}
    )
    notification_delivery: int = field(
        default=0, metadata={"description": "(3)delivery notice enabled"}
    )
    notification_order_change: int = field(
        default=0, metadata={"description": "(4) order changed in backend"}
    )
    notification_reminder: int = field(
        default=0, metadata={"description": "(5) order deadline due soon"}
    )
    notification_profile: int = field(
        default=0, metadata={"description": "(6) profile changed"}
    )
    notification_newsletter: int = field(
        default=0, metadata={"description": "(7) newsletter (aka noAd above)"}
    )
    notification_refund: int = field(
        default=0, metadata={"description": "(8) box/refund deposit/return processed."}
    )
    norefund: int = field(
        default=0,
        metadata={
            "description": "if 1, this customer does not get refund invoiced (V17)"
        },
    )
    has_orders: int = field(
        default=0,
        metadata={
            "description": "if this customer has more than 0 orders in the system. useful to identify fresh customers."
        },
    )


@dataclass
class XUnit(DataListModel):
    """
    Extended unit object representing alternative units for items.
    """

    item_id: int = field(
        default=0, metadata={"description": "The Item this alternative unit refers to."}
    )
    name: str | None = field(
        default=None, metadata={"description": "Clear text localized name"}
    )
    parts: str | None = field(
        default=None,
        metadata={
            "description": "parts of this alternative unit, that make up one item base unit. Allows to build a unit switching UI control."
        },
    )
    type: str | None = field(
        default=None,
        metadata={
            "description": "\"S\" is a 'by piece' item, 'W' defines a weighted item that has a measured value"
        },
    )
    unit_id: int = field(
        default=0,
        metadata={"description": "id for internal references (the unique identifier)"},
    )
    preferred: str | None = field(
        default=None,
        metadata={
            "description": "if that unit is to be used as preferred selection (Since V2)"
        },
    )


@dataclass
class Shop(DataListModel):
    """
    Shop object representing available shops.
    """

    latitude: float | None = field(
        default=None, metadata={"description": "Shop latitude"}
    )
    longitude: float | None = field(
        default=None, metadata={"description": "Shop longitude"}
    )
    name: str | None = field(default=None, metadata={"description": "Shop name"})
    delivery_lat: float | None = field(
        default=None, metadata={"description": "Delivery area latitude"}
    )
    delivery_lng: float | None = field(
        default=None, metadata={"description": "Delivery area longitude"}
    )
    id: str | None = field(default=None, metadata={"description": "Shop identifier"})


@dataclass
class Rubric(DataListModel):
    """
    Items naturally belong into exactly one category. Besides that, they can be ordered into one or many additional Rubric's. There is a API.objects.RubricMap Object that connects them.

    There are also API.objects.SubGroup's to present items.

    See also API.methods.groups, API.methods.navigation, API.objects.Item, Group
    """

    id: int = field(
        default=0, metadata={"description": "The internal ID of this category."}
    )
    name: str | None = field(
        default=None, metadata={"description": "The (localized) name of this category."}
    )
    infotext: str | None = field(
        default=None,
        metadata={"description": "The (localized) description text of this category."},
    )
    count: int = field(
        default=0,
        metadata={
            "description": "The number of Items in that category. This number is dependent on the executing user and the timing constraints of the items."
        },
    )
    is_special: int = field(
        default=0,
        metadata={"description": "If the rubric is marked special"},
    )
    has_img: int = field(
        default=0,
        metadata={"description": "1 if the group has an big image assigned (Since V2)"},
    )
    has_tn: int = field(
        default=0,
        metadata={
            "description": "1 if the group has an small (icon-) image assigned (Since V2)"
        },
    )


# Model registry for dynamic model creation
MODEL_REGISTRY = {
    "Address": Address,
    "Assorted": Assorted,
    "Assortment": Assortment,
    "AssortmentGroup": AssortmentGroup,
    "AssortmentPosition": AssortmentPosition,
    "AuxDate": AuxDate,
    "Box": Box,
    "CartItem": CartItem,
    "CustomerInfo": CustomerInfo,
    "DDate": DDate,
    "Delivery": Delivery,
    "DeliveryState": DeliveryState,
    "DeselectedGroup": DeselectedGroup,
    "DeselectedItem": DeselectedItem,
    "Discount": Discount,
    "Favourite": Favourite,
    "Group": Group,
    "Item": Item,
    "KeyValue": KeyValue,
    "Order": Order,
    "Pause": Pause,
    "PermanentPosition": PermanentPosition,
    "Position": Position,
    "RelatedItem": RelatedItem,
    "Rubric": Rubric,
    "Shop": Shop,
    "ShopDate": ShopDate,
    "ShopUrl": ShopUrl,
    "SubGroup": SubGroup,
    "SubGroupMap": SubGroupMap,
    "Subscription": Subscription,
    "Tour": Tour,
    "UserInfo": UserInfo,
    "XUnit": XUnit,
}


def parse_data_list_response(response_data: list[dict[str, Any]]) -> list[Any]:
    """
    Parse a DataList response into model instances.

    Args:
        response_data: Raw JSON response data following DataList format

    Returns:
        List of parsed model instances

    Example:
        response = [{"type": "Item", "data": [[1, "Apple", 2.50, ...]]}]
        items = parse_data_list_response(response)
    """
    parsed_objects = []

    for response_item in response_data:
        if not isinstance(response_item, dict) or "type" not in response_item:
            continue

        object_type = response_item["type"]
        model_class = MODEL_REGISTRY.get(object_type)

        if not model_class:
            continue

        data_entries = response_item.get("data", [])

        for data_entry in data_entries:
            # Skip the terminating [0] entry
            if data_entry == [0]:
                continue

            try:
                # Type check: ensure model_class has the from_data_list_entry method
                if hasattr(model_class, "from_data_list_entry"):
                    model_instance = model_class.from_data_list_entry(data_entry)
                    parsed_objects.append(model_instance)
            except (IndexError, ValueError, TypeError):
                # Log error but continue processing other entries
                continue

    return parsed_objects
