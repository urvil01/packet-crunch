# PacketCrunch FastAPI Backend

FastAPI backend service for PacketCrunch connected to Supabase PostgreSQL database.

## Local Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env`:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=2209
   FRONTEND_URL=http://localhost:5173
   ```

3. Run locally:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Render Deployment Settings

- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Environment Variables to set in Render Dashboard:

- `SUPABASE_URL`: Your Supabase Project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase Service Role Secret Key
- `ADMIN_USERNAME`: Admin login username
- `ADMIN_PASSWORD`: Admin login password/PIN
- `FRONTEND_URL`: Your Vercel frontend URL (e.g., `https://packet-crunch.vercel.app`)

## Database Setup (Supabase SQL)

Run the following SQL in the Supabase SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock_count INT NOT NULL DEFAULT 10,
    available BOOLEAN NOT NULL DEFAULT true,
    rating NUMERIC(3, 1) DEFAULT 4.8,
    description TEXT,
    image TEXT,
    tag TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_address TEXT NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) DEFAULT 0,
    delivery_fee NUMERIC(10, 2) DEFAULT 0,
    payment_method TEXT DEFAULT 'UPI / QR Code',
    status TEXT NOT NULL DEFAULT 'Preparing',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id TEXT REFERENCES products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    quantity INT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
