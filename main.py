import os
import time
import uuid
import secrets
from typing import List, Optional
from datetime import datetime, timezone
import jwt
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from supabase_client import get_supabase_client

load_dotenv()

app = FastAPI(title="PacketCrunch API", version="1.0.0")

# Security / Environment Config
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "2209")
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
if FRONTEND_URL:
    for url in FRONTEND_URL.split(","):
        clean_url = url.strip()
        if clean_url and clean_url not in origins:
            origins.append(clean_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default Products Seed
DEFAULT_PRODUCTS = [
    {
        "id": "pc-1",
        "name": "Lays Magic Masala (Large Pack)",
        "category": "Chips & Crisps",
        "price": 30.0,
        "stock_count": 15,
        "available": True,
        "rating": 4.9,
        "description": "Classic Indian spice flavor crisps for midnight study sessions.",
        "image": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=600&q=80",
        "tag": "Hostel Favorite"
    },
    {
        "id": "pc-2",
        "name": "Doritos Cheese Nachos",
        "category": "Chips & Crisps",
        "price": 50.0,
        "stock_count": 8,
        "available": True,
        "rating": 4.8,
        "description": "Crispy corn tortilla chips bursting with intense cheesy goodness.",
        "image": "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?auto=format&fit=crop&w=600&q=80",
        "tag": "Bestseller"
    },
    {
        "id": "pc-3",
        "name": "Maggi 2-Minute Special Masala",
        "category": "Instant Food",
        "price": 25.0,
        "stock_count": 24,
        "available": True,
        "rating": 5.0,
        "description": "The ultimate hostel survival food. Quick, piping hot & comforting.",
        "image": "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=600&q=80",
        "tag": "Late Night Must"
    },
    {
        "id": "pc-4",
        "name": "Nutella & Go Snack Stick",
        "category": "Sweet & Chocolates",
        "price": 90.0,
        "stock_count": 6,
        "available": True,
        "rating": 4.7,
        "description": "Rich hazelnut cocoa spread paired with crispy breadsticks.",
        "image": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=600&q=80",
        "tag": "Sweet Tooth"
    },
    {
        "id": "pc-5",
        "name": "Red Bull Energy Drink (250ml)",
        "category": "Beverages",
        "price": 125.0,
        "stock_count": 10,
        "available": True,
        "rating": 4.9,
        "description": "Vitalizes body and mind for exam all-nighters.",
        "image": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=600&q=80",
        "tag": "Exam Saver"
    },
    {
        "id": "pc-6",
        "name": "Oreo Original Biscuit Pack",
        "category": "Sweet & Chocolates",
        "price": 35.0,
        "stock_count": 0,
        "available": False,
        "rating": 4.6,
        "description": "Rich rich cream sandwiched between signature chocolate cookies.",
        "image": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=600&q=80",
        "tag": "Out of Stock"
    }
]

# In-memory fallback if Supabase is not configured yet
in_memory_products = [dict(p) for p in DEFAULT_PRODUCTS]
in_memory_orders = []

# Models
class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: str

class ProductModel(BaseModel):
    id: Optional[str] = None
    name: str
    category: str
    price: float
    stockQuantity: Optional[int] = Field(default=10, alias="stock_count")
    stock_count: Optional[int] = 10
    available: Optional[bool] = True
    rating: Optional[float] = 4.8
    description: Optional[str] = ""
    image: Optional[str] = ""
    tag: Optional[str] = "Snack"

    class Config:
        populate_by_name = True

class OrderItemModel(BaseModel):
    id: Optional[str] = None
    name: str
    price: float
    quantity: int
    image: Optional[str] = ""

class CreateOrderModel(BaseModel):
    studentName: str
    roomNumber: str
    phone: str
    paymentMethod: Optional[str] = "UPI / QR Code"
    subtotal: Optional[float] = 0.0
    deliveryFee: Optional[float] = 0.0
    totalAmount: float
    items: List[OrderItemModel]

class StatusUpdateModel(BaseModel):
    status: str

# Helpers
def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": datetime.now(timezone.utc),
        "admin": True
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_admin_token(authorization: Optional[str] = Header(None)) -> bool:
    if not authorization:
        # Fallback to dev header or check token
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
    token = authorization.replace("Bearer ", "").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("admin"):
            return True
    except Exception:
        pass
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired admin token")

def format_product(p: dict) -> dict:
    stock = p.get("stock_count", p.get("stockQuantity", 10))
    if stock is None:
        stock = 10
    else:
        stock = int(stock)
    avail = bool(p.get("available", True)) and (stock > 0)
    return {
        "id": str(p.get("id")),
        "name": p.get("name", ""),
        "category": p.get("category", "Chips & Crisps"),
        "price": float(p.get("price", 0)),
        "stockQuantity": stock,
        "stock_count": stock,
        "available": avail,
        "rating": float(p.get("rating", 4.8)),
        "description": p.get("description", ""),
        "image": p.get("image", ""),
        "tag": p.get("tag", "Snack")
    }

def format_order(o: dict, items: List[dict] = None) -> dict:
    order_items = []
    if items:
        for it in items:
            order_items.append({
                "id": str(it.get("product_id") or it.get("id", "")),
                "name": it.get("product_name") or it.get("name", ""),
                "price": float(it.get("price", 0)),
                "quantity": int(it.get("quantity", 1)),
                "subtotal": float(it.get("subtotal", 0)),
                "image": it.get("image", "")
            })
    elif "items" in o:
        order_items = o["items"]
    
    return {
        "id": str(o.get("id")),
        "studentName": o.get("customer_name") or o.get("studentName", ""),
        "customer_name": o.get("customer_name") or o.get("studentName", ""),
        "roomNumber": o.get("customer_address") or o.get("roomNumber", ""),
        "customer_address": o.get("customer_address") or o.get("roomNumber", ""),
        "phone": o.get("customer_phone") or o.get("phone", ""),
        "customer_phone": o.get("customer_phone") or o.get("phone", ""),
        "paymentMethod": o.get("payment_method") or o.get("paymentMethod", "UPI / QR Code"),
        "subtotal": float(o.get("subtotal", 0.0)),
        "deliveryFee": float(o.get("delivery_fee") or o.get("deliveryFee", 0.0)),
        "totalAmount": float(o.get("total_amount") or o.get("totalAmount", 0.0)),
        "total_amount": float(o.get("total_amount") or o.get("totalAmount", 0.0)),
        "status": o.get("status", "Preparing"),
        "timestamp": o.get("created_at") or o.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "items": order_items
    }

# Routes
@app.get("/")
def read_root():
    client = get_supabase_client()
    return {
        "app": "PacketCrunch Backend API",
        "status": "online",
        "database": "Supabase PostgreSQL" if client else "In-Memory (Configure SUPABASE_URL in .env)"
    }

@app.post("/api/admin/login")
def admin_login(req: LoginRequest):
    # Allow authentication if password matches ADMIN_PASSWORD
    if req.password == ADMIN_PASSWORD:
        token = create_token(req.username or ADMIN_USERNAME)
        return {
            "success": True,
            "token": token,
            "message": "Admin authentication successful"
        }
    raise HTTPException(status_code=401, detail="Invalid admin password")

@app.get("/api/products")
def get_products():
    client = get_supabase_client()
    if client:
        try:
            res = client.table("products").select("*").execute()
            if not res.data:
                # Seed default products into Supabase
                seed_data = []
                for p in DEFAULT_PRODUCTS:
                    seed_data.append({
                        "id": p["id"],
                        "name": p["name"],
                        "category": p["category"],
                        "price": p["price"],
                        "stock_count": p["stock_count"],
                        "available": p["available"],
                        "rating": p["rating"],
                        "description": p["description"],
                        "image": p["image"],
                        "tag": p["tag"]
                    })
                client.table("products").insert(seed_data).execute()
                res = client.table("products").select("*").execute()
            
            return [format_product(p) for p in res.data]
        except Exception as e:
            print(f"Supabase products error: {e}")
            return [format_product(p) for p in in_memory_products]
    else:
        return [format_product(p) for p in in_memory_products]

@app.post("/api/products")
def create_product(product: ProductModel, authenticated: bool = Depends(verify_admin_token)):
    stock = product.stock_count if product.stock_count is not None else (product.stockQuantity or 10)
    item_id = product.id or f"pc-{int(time.time() * 1000)}"
    product_dict = {
        "id": item_id,
        "name": product.name,
        "category": product.category,
        "price": float(product.price),
        "stock_count": int(stock),
        "available": bool(stock > 0 and product.available),
        "rating": float(product.rating or 4.8),
        "description": product.description or "",
        "image": product.image or "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=600&q=80",
        "tag": product.tag or "Snack"
    }

    client = get_supabase_client()
    if client:
        try:
            res = client.table("products").upsert(product_dict).execute()
            return format_product(res.data[0] if res.data else product_dict)
        except Exception as e:
            print(f"Supabase create product error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # In-memory update
        existing_idx = next((i for i, p in enumerate(in_memory_products) if p["id"] == item_id), -1)
        if existing_idx >= 0:
            in_memory_products[existing_idx] = product_dict
        else:
            in_memory_products.append(product_dict)
        return format_product(product_dict)

@app.put("/api/products/{product_id}")
def update_product(product_id: str, product: ProductModel, authenticated: bool = Depends(verify_admin_token)):
    product.id = product_id
    return create_product(product, authenticated)

@app.delete("/api/products/{product_id}")
def delete_product(product_id: str, authenticated: bool = Depends(verify_admin_token)):
    client = get_supabase_client()
    if client:
        try:
            client.table("products").delete().eq("id", product_id).execute()
            return {"success": True, "message": "Product deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        global in_memory_products
        in_memory_products = [p for p in in_memory_products if p["id"] != product_id]
        return {"success": True, "message": "Product deleted successfully"}

@app.patch("/api/products/{product_id}/toggle")
def toggle_product_availability(product_id: str, authenticated: bool = Depends(verify_admin_token)):
    client = get_supabase_client()
    if client:
        try:
            res = client.table("products").select("*").eq("id", product_id).execute()
            if not res.data:
                raise HTTPException(status_code=404, detail="Product not found")
            item = res.data[0]
            new_avail = not bool(item.get("available", True))
            new_stock = item.get("stock_count", 0)
            if new_avail and new_stock <= 0:
                new_stock = 5 # Default restock if toggled on
            
            updated = {
                "available": new_avail and new_stock > 0,
                "stock_count": new_stock
            }
            res_up = client.table("products").update(updated).eq("id", product_id).execute()
            return format_product(res_up.data[0])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        item = next((p for p in in_memory_products if p["id"] == product_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        item["available"] = not item.get("available", True)
        if item["available"] and item.get("stock_count", 0) <= 0:
            item["stock_count"] = 5
        return format_product(item)

@app.post("/api/orders")
def create_order(order: CreateOrderModel):
    order_id = f"ORD-{secrets.randbelow(900000) + 100000}"
    now_iso = datetime.now(timezone.utc).isoformat()

    order_record = {
        "id": order_id,
        "customer_name": order.studentName,
        "customer_phone": order.phone,
        "customer_address": order.roomNumber,
        "total_amount": float(order.totalAmount),
        "subtotal": float(order.subtotal or 0.0),
        "delivery_fee": float(order.deliveryFee or 0.0),
        "payment_method": order.paymentMethod or "UPI / QR Code",
        "status": "Preparing",
        "created_at": now_iso
    }

    order_items_records = []
    for item in order.items:
        order_items_records.append({
            "order_id": order_id,
            "product_id": item.id,
            "product_name": item.name,
            "quantity": item.quantity,
            "price": float(item.price),
            "subtotal": float(item.quantity * item.price)
        })

    client = get_supabase_client()
    if client:
        try:
            # 1. Insert order
            client.table("orders").insert(order_record).execute()

            # 2. Insert order items
            if order_items_records:
                client.table("order_items").insert(order_items_records).execute()

            # 3. Deduct product stock in database
            for item in order.items:
                if item.id:
                    try:
                        p_res = client.table("products").select("stock_count, available").eq("id", item.id).execute()
                        if p_res.data:
                            curr_stock = p_res.data[0].get("stock_count", 10)
                            new_stock = max(0, curr_stock - item.quantity)
                            new_avail = new_stock > 0 and p_res.data[0].get("available", True)
                            client.table("products").update({
                                "stock_count": new_stock,
                                "available": new_avail
                            }).eq("id", item.id).execute()
                    except Exception as p_err:
                        print(f"Error updating stock for {item.id}: {p_err}")

            formatted = format_order(order_record, order_items_records)
            return {"success": True, "order": formatted}
        except Exception as e:
            print(f"Supabase order creation error: {e}")
            raise HTTPException(status_code=500, detail="Order could not be placed. Please try again.")
    else:
        # In-memory save
        formatted = format_order(order_record, order_items_records)
        in_memory_orders.insert(0, formatted)
        # Deduct in memory
        for item in order.items:
            p = next((x for x in in_memory_products if x["id"] == item.id), None)
            if p:
                p["stock_count"] = max(0, p.get("stock_count", 10) - item.quantity)
                if p["stock_count"] == 0:
                    p["available"] = False
        return {"success": True, "order": formatted}

@app.get("/api/orders")
def get_orders(authenticated: bool = Depends(verify_admin_token)):
    client = get_supabase_client()
    if client:
        try:
            orders_res = client.table("orders").select("*").order("created_at", desc=True).execute()
            if not orders_res.data:
                return []
            
            orders_list = []
            for o in orders_res.data:
                items_res = client.table("order_items").select("*").eq("order_id", o["id"]).execute()
                orders_list.append(format_order(o, items_res.data or []))
            
            return orders_list
        except Exception as e:
            print(f"Supabase get orders error: {e}")
            return in_memory_orders
    else:
        return in_memory_orders

@app.patch("/api/orders/{order_id}/status")
def update_order_status(order_id: str, payload: StatusUpdateModel, authenticated: bool = Depends(verify_admin_token)):
    client = get_supabase_client()
    if client:
        try:
            res = client.table("orders").update({"status": payload.status, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", order_id).execute()
            if res.data:
                items_res = client.table("order_items").select("*").eq("order_id", order_id).execute()
                return {"success": True, "order": format_order(res.data[0], items_res.data or [])}
            return {"success": True, "order_id": order_id, "status": payload.status}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        for o in in_memory_orders:
            if o["id"] == order_id:
                o["status"] = payload.status
                return {"success": True, "order": o}
        raise HTTPException(status_code=404, detail="Order not found")
