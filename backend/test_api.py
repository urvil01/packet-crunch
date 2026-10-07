from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_full_flow():
    print("=== TEST 1: Health Check ===")
    res = client.get("/")
    assert res.status_code == 200
    print("Health response:", res.json())

    print("\n=== TEST 2: Fetch Products ===")
    res = client.get("/api/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 6
    print(f"Loaded {len(products)} products successfully. Sample product:", products[0]["name"])

    print("\n=== TEST 3: Admin Login ===")
    res = client.post("/api/admin/login", json={"password": "2209"})
    assert res.status_code == 200
    login_data = res.json()
    assert login_data["success"] == True
    token = login_data["token"]
    print("Admin login successful. Token generated.")

    auth_headers = {"Authorization": f"Bearer {token}"}

    print("\n=== TEST 4: Customer Places Order ===")
    order_payload = {
        "studentName": "Rahul Sharma",
        "roomNumber": "Block B - Room 304",
        "phone": "9876543210",
        "paymentMethod": "UPI / QR Code",
        "subtotal": 60.0,
        "deliveryFee": 10.0,
        "totalAmount": 70.0,
        "items": [
            {
                "id": "pc-1",
                "name": "Lays Magic Masala (Large Pack)",
                "price": 30.0,
                "quantity": 2
            }
        ]
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 200
    order_data = res.json()
    assert order_data["success"] == True
    order_id = order_data["order"]["id"]
    print(f"Order created successfully with ID: {order_id}")

    print("\n=== TEST 5: Admin Fetches Orders ===")
    res = client.get("/api/orders", headers=auth_headers)
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) >= 1
    found_order = next((o for o in orders if o["id"] == order_id), None)
    assert found_order is not None
    assert found_order["studentName"] == "Rahul Sharma"
    print(f"Admin verified order {order_id} exists in central database!")

    print("\n=== TEST 6: Admin Updates Order Status ===")
    res = client.patch(f"/api/orders/{order_id}/status", json={"status": "Out for Delivery"}, headers=auth_headers)
    assert res.status_code == 200
    print(f"Order status updated to: {res.json()['order']['status']}")

    print("\n=== TEST 7: Product Management (Add, Edit, Toggle, Delete) ===")
    new_product = {
        "name": "Test Energy Bar",
        "category": "Chips & Crisps",
        "price": 40.0,
        "stockQuantity": 12,
        "description": "Crunchy protein snack bar.",
        "tag": "New"
    }
    res = client.post("/api/products", json=new_product, headers=auth_headers)
    assert res.status_code == 200
    created_p = res.json()
    p_id = created_p["id"]
    print(f"Created new product ID: {p_id}")

    res = client.patch(f"/api/products/{p_id}/toggle", headers=auth_headers)
    assert res.status_code == 200
    print(f"Toggled availability for product {p_id}")

    res = client.delete(f"/api/products/{p_id}", headers=auth_headers)
    assert res.status_code == 200
    print("\n[SUCCESS] ALL API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_flow()
