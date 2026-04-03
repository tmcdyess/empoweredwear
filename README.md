# EmpoweredWear by Dr. Tina — Website & Stripe Backend

This project contains the complete EmpoweredWear landing page and a lightweight Python backend that integrates with Stripe Checkout.

## Why a backend is required
Because each shirt size has a different Stripe Price ID (e.g., Small is `$17`, 1X is `$20`), a backend server is required to securely create a Stripe Checkout Session with the exact Price ID that matches the customer's selected size.

## Project Structure
- `index.html` — The main landing page (frontend)
- `assets/` — All product images, logos, and photos
- `server.py` — The Python/FastAPI backend that handles Stripe Checkout
- `requirements.txt` — Python dependencies

## How to Run Locally

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8080
   ```

3. **View the site:**
   Open `http://localhost:8080` in your browser.

## How to Deploy to Production

To make this website permanent and live on the internet, you need to deploy both the frontend and the backend together.

**Recommended hosting: Render or Railway (Free/Low Cost)**
Both platforms allow you to deploy Python web services easily.

1. Upload this entire folder to a GitHub repository.
2. Connect your GitHub repository to Render (render.com) or Railway (railway.app).
3. Choose **Python Web Service**.
4. Set the Start Command to: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. The platform will automatically install the requirements and start your server.

## Stripe Configuration
Your live Stripe Secret Key is currently configured in `server.py`. 
*Note: For best security practices in production, you should move this key to an Environment Variable (`STRIPE_SECRET_KEY`) in your hosting provider's dashboard.*
