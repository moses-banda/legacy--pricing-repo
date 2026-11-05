"""Ticket pricing for CampusEvents -- legacy module (ICA 24A).

This works, and it is tested (see test_legacy_pricing.py), but nobody wants to touch it.
Your job: refactor it without changing behavior, and measure the result with radon.
"""


# (weekday price, weekend price) per event type
PRICES = {
    "concert": (20.0, 25.0),
    "lecture": (5.0, 5.0),
    "sports": (12.0, 15.0),
    "workshop": (30.0, 30.0),
}


def base_price(t, d):
    """Per-ticket price for an event type on a given day (0=Mon..6=Sun)."""
    if t not in PRICES:
        raise ValueError("bad type")
    weekday, weekend = PRICES[t]
    return weekend if d == 5 or d == 6 else weekday


def validate_quantity(q):
    if q <= 0:
        raise ValueError("bad qty")
    if q > 10:
        raise ValueError("too many")


def role_multiplier(u):
    """Price multiplier for the user's role (1.0 = no discount)."""
    if u is None:
        return 1.0
    role = u.get("role")
    if role == "student":
        return 0.8 if u.get("verified") else 0.9
    if role == "staff":
        return 0.85
    if role == "alumni":
        return 0.85 if u.get("years", 0) >= 10 else 0.95
    return 1.0


def bulk_discount(t, q):
    """Flat amount off for orders of 5+ tickets (workshops excluded)."""
    if q >= 5 and t != "workshop":
        return 5.0
    return 0.0


def coupon_multiplier(c, t, u):
    """Price multiplier for a coupon code; raises ValueError for unknown codes."""
    if c is None:
        return 1.0
    if c == "WELCOME10":
        return 0.9 if u is not None and u.get("first_purchase") else 1.0
    if c == "HALFOFF":
        return 0.5 if t == "lecture" else 1.0
    if c == "FREEDRINK":
        return 1.0
    raise ValueError("bad coupon")


def service_fee(total):
    """Service fee by price band."""
    if total < 20:
        return 1.0
    if total < 100:
        return 2.5
    return 5.0


def calc(t, q, u, d, c=None, w=False):
    # t = event type, q = quantity, u = user dict, d = day of week (0=Mon..6=Sun),
    # c = coupon code, w = waitlist
    p = base_price(t, d)
    validate_quantity(q)
    total = p * q
    total = total * role_multiplier(u)
    total = total - bulk_discount(t, q)
    total = total * coupon_multiplier(c, t, u)
    if w:
        total = total + 2.0
    fee = service_fee(total)
    return round(total + fee, 2)
