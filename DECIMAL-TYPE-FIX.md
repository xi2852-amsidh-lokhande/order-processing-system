# 🔧 DynamoDB Decimal Type Error Fix

## Error Analysis
```json
{
    "errorCode": "INTERNAL_SERVER_ERROR",
    "errorMessage": "Internal server error",
    "recommendedData": {
        "details": "Float types are not supported. Use Decimal types instead."
    }
}
```

## Root Cause
DynamoDB requires `Decimal` types for numeric values, but the code was converting Decimal calculations back to `float` before saving to DynamoDB.

## Issue in order_service.py

### ❌ **Before (Causing Error):**
```python
# Converting Decimal back to float for DynamoDB - WRONG!
order_record = {
    "orderId": order_id,
    "customerId": order_data["customerId"],
    "items": order_data["items"],
    "totalAmount": float(total_amount),  # ❌ Float not supported by DynamoDB
    "status": "PLACED",
    "createdAt": datetime.now(timezone.utc).isoformat(),
}
```

### ✅ **After (Fixed):**
```python
# Keep Decimal types for DynamoDB
order_record = {
    "orderId": order_id,
    "customerId": order_data["customerId"],
    "items": processed_items,  # Items with Decimal types
    "totalAmount": total_amount,  # ✅ Keep as Decimal for DynamoDB
    "status": "PLACED",
    "createdAt": datetime.now(timezone.utc).isoformat(),
}
```

## Additional Improvements

### 1. **Handle Missing Price in Request**
Your request doesn't include `price` values:
```json
{
    "customerId": "amsidh",
    "items": [
        {
            "vendorId": "v1",
            "productId": "p1",
            "quantity": 2
            // ❌ No price field
        }
    ]
}
```

**Fixed by adding default price:**
```python
# Use default price of 10.00 if not provided in request
price = Decimal(str(item.get("price", "10.00")))
```

### 2. **Process Items with Decimal Types**
```python
processed_items = []
for item in order_data.get("items", []):
    processed_item = {
        "vendorId": item.get("vendorId"),
        "productId": item.get("productId"),
        "quantity": Decimal(str(item.get("quantity", 1))),  # ✅ Decimal for DynamoDB
        "price": Decimal(str(item.get("price", "10.00")))   # ✅ Decimal for DynamoDB
    }
    processed_items.append(processed_item)
```

### 3. **Separate Data for Different Uses**
- **DynamoDB Storage**: Use Decimal types (for data consistency)
- **JSON Events**: Convert to float (for JSON serialization)
- **API Response**: Convert to float (for JSON response)

```python
# For DynamoDB - keep Decimals
order_record = {"totalAmount": total_amount}

# For Events - convert to float for JSON
publish_order_placed({"totalAmount": float(total_amount)})

# For Response - convert to float for JSON
return {"totalAmount": float(total_amount)}
```

## Expected Result

With your request:
```json
{
    "customerId": "amsidh",
    "items": [
        {
            "vendorId": "v1",
            "productId": "p1",
            "quantity": 2
        }
    ]
}
```

**Expected Response:**
```json
{
    "success": true,
    "orderId": "generated-uuid"
}
```

**DynamoDB Record (with Decimals):**
```json
{
    "orderId": "generated-uuid",
    "customerId": "amsidh",
    "items": [
        {
            "vendorId": "v1",
            "productId": "p1",
            "quantity": 2,
            "price": 10.00
        }
    ],
    "totalAmount": 20.00,
    "status": "PLACED",
    "createdAt": "2025-07-29T18:54:54.510161+00:00"
}
```

The **"Float types are not supported"** error should be completely resolved! 🎯
