# Business logic for inventory management
import uuid
from common.logger import get_logger
from dao.inventory_dao import update_inventory_record
from events.producer.producer import publish_inventory_updated
from datetime import datetime, timezone


def update_inventory(data):
    logger = get_logger("inventory-service")
    
    # Get current quantity before update (in real implementation, you'd fetch from DB)
    current_quantity = data.get("currentQuantity", 0)  # This should come from DB lookup
    quantity_change = data["quantity"]
    new_quantity = current_quantity + quantity_change
    
    inventory_record = {
        "vendorId": data["vendorId"],
        "productId": data["productId"],
        "quantity": quantity_change,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    
    # Update inventory in DynamoDB
    update_inventory_record(inventory_record)
    logger.info(
        "Inventory record updated",
        extra={
            "vendorId": data["vendorId"], 
            "productId": data["productId"],
            "quantityChange": quantity_change,
            "newQuantity": new_quantity
        },
    )
    
    # Publish InventoryUpdated event
    event_published = publish_inventory_updated({
        "vendorId": data["vendorId"],
        "productId": data["productId"],
        "quantityChange": quantity_change,
        "newQuantity": new_quantity
    })
    
    if event_published:
        logger.info("InventoryUpdated event published successfully", 
                   extra={"vendorId": data["vendorId"], "productId": data["productId"]})
    else:
        logger.error("Failed to publish InventoryUpdated event", 
                    extra={"vendorId": data["vendorId"], "productId": data["productId"]})
    
    return {
        "vendorId": data["vendorId"], 
        "productId": data["productId"],
        "quantityChange": quantity_change,
        "newQuantity": new_quantity,
        "eventPublished": event_published
    }


def check_inventory_availability(vendor_id: str, product_id: str, required_quantity: int):
    """
    Check if sufficient inventory is available for an order
    
    Args:
        vendor_id: The vendor identifier
        product_id: The product identifier  
        required_quantity: Quantity needed
        
    Returns:
        dict: Availability status and current quantity
    """
    logger = get_logger("inventory-service")
    
    try:
        # In real implementation, fetch current quantity from DynamoDB
        # current_quantity = get_inventory_quantity(vendor_id, product_id)
        current_quantity = 100  # Mock value for now
        
        is_available = current_quantity >= required_quantity
        
        logger.info(f"Inventory check: {required_quantity} needed, {current_quantity} available",
                   extra={
                       "vendorId": vendor_id,
                       "productId": product_id,
                       "required": required_quantity,
                       "available": current_quantity,
                       "isAvailable": is_available
                   })
        
        return {
            "vendorId": vendor_id,
            "productId": product_id,
            "currentQuantity": current_quantity,
            "requiredQuantity": required_quantity,
            "isAvailable": is_available
        }
        
    except Exception as e:
        logger.error(f"Error checking inventory availability: {str(e)}", 
                    extra={"vendorId": vendor_id, "productId": product_id})
        return {
            "vendorId": vendor_id,
            "productId": product_id,
            "isAvailable": False,
            "error": str(e)
        }
