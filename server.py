"""
EmpoweredWear by Dr. Tina — Stripe Checkout Backend
FastAPI server that creates Stripe Checkout Sessions with the correct
Price ID per size, supporting multiple line items (full cart).
Shipping options are shown dynamically based on order subtotal.
"""

import os
import stripe
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# ── Stripe configuration ──────────────────────────────────────────────────────
# Set STRIPE_SECRET_KEY as an environment variable in your hosting provider.
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# ── Production domain ─────────────────────────────────────────────────────────
# Override with PRODUCTION_DOMAIN env var on your host (e.g. Render).
PRODUCTION_DOMAIN = os.environ.get("PRODUCTION_DOMAIN", "https://empoweredwearbydrtina.com")

# Price in cents per size tier
PRICE_CENTS = {
    "S":  1700,
    "M":  1700,
    "L":  1700,
    "XL": 1700,
    "1X": 2000,
    "2X": 2000,
    "3X": 2000,
    "4X": 2200,
    "5X": 2200,
    "6X": 2200,
}

FREE_SHIP_THRESHOLD = 7500  # $75.00 in cents

# ── Shipping option definitions ───────────────────────────────────────────────
SHIP_STANDARD = {
    "shipping_rate_data": {
        "type": "fixed_amount",
        "fixed_amount": {"amount": 499, "currency": "usd"},
        "display_name": "Standard Shipping",
        "delivery_estimate": {
            "minimum": {"unit": "business_day", "value": 5},
            "maximum": {"unit": "business_day", "value": 7},
        },
    }
}
SHIP_PRIORITY = {
    "shipping_rate_data": {
        "type": "fixed_amount",
        "fixed_amount": {"amount": 999, "currency": "usd"},
        "display_name": "Priority Shipping",
        "delivery_estimate": {
            "minimum": {"unit": "business_day", "value": 2},
            "maximum": {"unit": "business_day", "value": 3},
        },
    }
}
SHIP_IN_PERSON = {
    "shipping_rate_data": {
        "type": "fixed_amount",
        "fixed_amount": {"amount": 0, "currency": "usd"},
        "display_name": "In-Person Pickup — FREE",
        "delivery_estimate": {
            "minimum": {"unit": "business_day", "value": 1},
            "maximum": {"unit": "business_day", "value": 1},
        },
    }
}
SHIP_FREE_75 = {
    "shipping_rate_data": {
        "type": "fixed_amount",
        "fixed_amount": {"amount": 0, "currency": "usd"},
        "display_name": "Free Shipping — Orders $75.00 & Over",
        "delivery_estimate": {
            "minimum": {"unit": "business_day", "value": 5},
            "maximum": {"unit": "business_day", "value": 7},
        },
    }
}

# ── Pydantic models ───────────────────────────────────────────────────────────
class CartItem(BaseModel):
    name: str        # e.g. "My Moves Tee"
    color: str       # e.g. "Purple"
    size: str        # e.g. "M"
    quantity: int    # e.g. 1

class CheckoutRequest(BaseModel):
    items: List[CartItem]

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="EmpoweredWear Checkout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/create-checkout-session")
async def create_checkout_session(req: CheckoutRequest):
    """
    Accepts a cart (list of items with size/color/quantity),
    maps each size to its Stripe Price ID, creates a Stripe Checkout
    Session with shipping options and all available payment methods.
    Returns the session URL to redirect the customer.
    """
    line_items = []
    subtotal_cents = 0

    for item in req.items:
        size_key = item.size.strip().upper()
        unit_amount = PRICE_CENTS.get(size_key)
        if not unit_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown size '{item.size}'. Valid sizes: {list(PRICE_CENTS.keys())}"
            )
        # Build a descriptive line item so customers see exactly what they ordered
        # on the Stripe Checkout page (e.g. "My Moves Tee — Purple, Size M")
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": unit_amount,
                "product_data": {
                    "name": f"{item.name} — {item.color}, Size {item.size}",
                    "description": "EmpoweredWear by Dr. Tina",
                },
            },
            "quantity": item.quantity,
        })
        subtotal_cents += unit_amount * item.quantity

    # Choose shipping options based on subtotal:
    # - Always show Standard, Priority, and In-Person Pickup
    # - Only show Free Shipping ($75+) option when subtotal qualifies
    if subtotal_cents >= FREE_SHIP_THRESHOLD:
        shipping_options = [SHIP_FREE_75, SHIP_STANDARD, SHIP_PRIORITY, SHIP_IN_PERSON]
    else:
        shipping_options = [SHIP_STANDARD, SHIP_PRIORITY, SHIP_IN_PERSON]

    success_url = f"{PRODUCTION_DOMAIN}/thank-you.html?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url  = f"{PRODUCTION_DOMAIN}/order-cancelled.html"

    try:
        session = stripe.checkout.Session.create(
            line_items=line_items,
            mode="payment",
            shipping_options=shipping_options,
            shipping_address_collection={"allowed_countries": ["US"]},
            success_url=success_url,
            cancel_url=cancel_url,
            # Order details (shirt name, color, size) stored in Stripe metadata
            metadata={
                "order_details": "; ".join(
                    [f"{i.name} ({i.color}, {i.size}) x{i.quantity}" for i in req.items]
                )
            },
        )
        return JSONResponse({"url": session.url})

    except stripe.error.InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message or e))

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message or e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "EmpoweredWear Checkout API"}


# ── Serve index.html with no-cache headers ───────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve index.html with no-cache headers to ensure fresh content on every deploy."""
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

# ── Serve static files (assets, JS, CSS, etc.) ───────────────────────────────
app.mount("/", StaticFiles(directory=".", html=True), name="static")
