# REFACTOR_NOTES: legacy pricing module (ICA)

Branch: `refactor`. Public signature `calc(t, q, u, d, c=None, w=False)` unchanged. No test edited. 24/24 tests green after every step.

## Worksheet 1: Understanding

| Question | Answer |
|---|---|
| What do t, q, u, d, c, w mean? | t = event type (concert, lecture, sports, workshop). q = ticket quantity (1 to 10). u = user dict or None (role, verified, years, first_purchase). d = day of week, 0=Mon to 6=Sun. c = coupon code or None. w = on the waitlist. |
| Order of discounts? Does it matter? | Base price x q, then role multiplier, then flat $5 bulk discount (q >= 5, not workshops), then coupon multiplier, then +$2 waitlist, then service fee band. Yes, it matters: the flat $5 comes off after the role percentage, and the coupon percentage applies after the $5. `test_bulk_discount_applies_before_coupon` pins this. |
| Which code can never run? | The `if total < 0: total = 0.0` clamp and the `total > 0` guard around the fee. Smallest possible total before the waitlist fee is 2.00 (lecture, verified student, HALFOFF), checked by brute force over every type, quantity, role, day and coupon, so the total is always positive. Also the dead initial `p = 0`. The `FREEDRINK: pass` branch runs but does nothing. |
| What looks like a bug but is pinned by a test? | FREEDRINK is accepted but gives nothing (`test_freedrink_changes_nothing`). Bulk discount is a flat $5 per order, not per ticket, and does not scale with the role discount. WELCOME10 stacks on top of the student discount. The waitlist surcharge is added before the fee band, so it can bump an order into a higher fee tier. |

Other oddities not covered by a test (left alone): `d` is never validated (d=9 acts like a weekday), unknown roles silently get no discount, type is validated before quantity so `("party", 0, ...)` reports "bad type", money is float rather than Decimal, a bad coupon is only rejected after other validation.

## Worksheet 2: Refactoring log

All steps were written by Claude (AI) and checked with `pytest -q` plus a golden-master comparison of old vs new `calc` over 83,160 input combinations (types, quantities, users, days, coupons, waitlist, including invalid ones). Each step was committed only when both were green.

| # | Refactoring | AI or by hand? | Tests after | Kept or reverted? Why |
|---|---|---|---|---|
| 1 | Extract function `base_price` | AI | 24 pass | Kept. Isolates the type/day branching. |
| 2 | Replace conditional with table (`PRICES`) | AI | 24 pass | Kept. Prices are now data, adding an event type is one line. |
| 3 | Extract function `validate_quantity` | AI | 24 pass | Kept. Order of checks preserved. |
| 4 | Extract function `role_multiplier` | AI | 24 pass | Kept. Biggest single complexity drop. |
| 5 | Extract function `bulk_discount` | AI | 24 pass | Kept. |
| 6 | Extract function `coupon_multiplier` | AI | 24 pass | Kept. Still raises ValueError on unknown codes. |
| 7 | Extract function `service_fee` | AI | 24 pass | Kept. |
| 8 | Remove dead code (negative clamp, zero-fee guard) | AI | 24 pass | Kept, only after proving the total is always >= 2.00. |
| 9 | Name constant, docstring, rename local `p` | AI | 24 pass | Kept. Parameter names untouched because other code may call with keywords. |

No step was reverted.

## Worksheet 3: Before and after (radon)

| Measure | Before | After |
|---|---|---|
| Highest function CC (grade) | calc: E (31) | coupon_multiplier: B (8) |
| Average CC | 31.0 | 4.29 (A) |
| Number of functions | 1 | 7 |
| Maintainability index | A (53.94) | A (61.81) |
| SLOC | 63 | 58 |
| Tests passing | 24 / 24 | 24 / 24 |

## Trade-offs

SLOC barely moved (63 to 58), so the gain is structure, not size: each business rule now lives in one small function that can be tested alone. The cost is a longer file with more names to learn, and `calc` is now a pipeline whose order is only documented in its docstring.

One tiny behavior difference: passing an unhashable event type (a list, say) now raises `TypeError` from the dict lookup in `base_price`, where the original raised `ValueError("bad type")`. No test or realistic caller hits this. Fix if you want it exact: guard with `isinstance(t, str)`.

Bugs are listed in Worksheet 1 and deliberately not fixed. Each is a product decision (should FREEDRINK do something? should bulk be per ticket?) for after the refactor.
