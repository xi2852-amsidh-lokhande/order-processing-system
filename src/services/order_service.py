# Business logic for order processing
from common.logger import get_logger
from dao.order_dao import save_order
from events.producer.producer import publish_order_placed, publish_order_updated
import uuid
from datetime import datetime, timezone
from decimal import Decimal


def place_order(order_data):
    logger = get_logger("order-service")
    # Validation is handled at the handler layer
    order_id = str(uuid.uuid4())
    
    # Calculate total amount - use default price if not provided
    total_amount = Decimal('0')
    processed_items = []
    
    for item in order_data.get("items", []):
        # Use default price of 10.00 if not provided in request
        price = Decimal(str(item.get("price", "10.00")))
        quantity = Decimal(str(item.get("quantity", 1)))
        total_amount += price * quantity
        
        # Create processed item with Decimal types for DynamoDB
        processed_item = {
            "vendorId": item.get("vendorId"),
            "productId": item.get("productId"),
            "quantity": quantity,
            "price": price
        }
        processed_items.append(processed_item)
    
    order_record = {
        "orderId": order_id,
        "customerId": order_data["customerId"],
        "items": processed_items,  # Use processed items with Decimal types
        "totalAmount": total_amount,  # Keep as Decimal for DynamoDB
        "status": "PLACED",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    
    # Save order to DynamoDB
    save_order(order_record)
    logger.info("Order saved", extra={"orderId": order_id})

    # Publish OrderPlaced event using the producer
    event_published = publish_order_placed({
        "orderId": order_id,
        "customerId": order_data["customerId"],
        "items": order_data["items"],  # Use original items for event (JSON serializable)
        "totalAmount": float(total_amount)  # Convert to float for JSON serialization in events
    })
    
    if event_published:
        logger.info("OrderPlaced event published successfully", extra={"orderId": order_id})
    else:
        logger.error("Failed to publish OrderPlaced event", extra={"orderId": order_id})
    
    return {
        "orderId": order_id,
        "totalAmount": float(total_amount),  # Convert to float for JSON response
    }


def update_order_status(order_id: str, new_status: str, details: dict = None):
    """
    Update order status and publish OrderUpdated event
    
    Args:
        order_id: The order identifier
        new_status: New status for the order
        details: Additional details about the status update
    """
    logger = get_logger("order-service")
    
    try:
        # Here you would typically update the order in DynamoDB
        # For now, we'll just publish the event
        
        event_published = publish_order_updated(order_id, new_status, details)
        
        if event_published:
            logger.info(f"Order status updated to {new_status}", 
                       extra={"orderId": order_id, "status": new_status})
        else:
            logger.error("Failed to publish OrderUpdated event", 
                        extra={"orderId": order_id})
        
        return {"success": event_published, "orderId": order_id, "status": new_status}
        
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}", 
                    extra={"orderId": order_id})
        return {"success": False, "error": str(e)}
