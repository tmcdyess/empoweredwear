"""
EmpoweredWear by Dr. Tina — Stripe Checkout Backend
FastAPI server that creates Stripe Checkout Sessions with the correct
Price ID per size, supporting multiple line items (full cart).
Shipping options are shown dynamically based on order subtotal.
"""

import os
import stripe
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
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

# Stripe Price IDs per size (from TshirtPrompts.docx)
PRICE_IDS = {
    "S":  "price_1TG2o8I2HBlCm4koQSprLsZ1",
    "M":  "price_1TG2o8I2HBlCm4koXQxsLtdu",
    "L":  "price_1TG2o8I2HBlCm4koo3SBYTSY",
    "XL": "price_1TG2o8I2HBlCm4kobCqlOjJi",
    "1X": "price_1TG2o8I2HBlCm4ko2CYIcu1k",
    "2X": "price_1TG2o8I2HBlCm4ko9X8qjBvr",
    "3X": "price_1TG2o8I2HBlCm4kovLFbhsYq",
    "4X": "price_1TG2o8I2HBlCm4kowkcoITfo",
    "5X": "price_1TG2o8I2HBlCm4kov508eGUH",
    "6X": "price_1TG2o8I2HBlCm4kobtDdprKr",
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
        price_id = PRICE_IDS.get(size_key)
        if not price_id:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown size '{item.size}'. Valid sizes: {list(PRICE_IDS.keys())}"
            )
        line_items.append({
            "price": price_id,
            "quantity": item.quantity,
        })
        # Retrieve price amount to calculate subtotal for shipping logic
        try:
            price_obj = stripe.Price.retrieve(price_id)
            subtotal_cents += (price_obj.unit_amount or 0) * item.quantity
        except Exception:
            pass  # If retrieval fails, default to showing paid shipping

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


# ── Serve static files (the landing page) ────────────────────────────────────
app.mount("/", StaticFiles(directory=".", html=True), name="static")
