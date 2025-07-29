# Event producer for order events
import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any, Optional
from common.logger import get_logger
from common.exception_handler import exception_handler

logger = get_logger("event-producer")

class OrderEventProducer:
    """
    Event producer for publishing order-related events to EventBridge
    """
    
    def __init__(self):
        self.eventbridge_client = boto3.client('events')
        self.event_bus_name = os.environ.get('EVENT_BUS_NAME')
        self.source = "order.service"
        
    def publish_order_placed_event(self, order_data: Dict[str, Any]) -> bool:
        """
        Publish OrderPlaced event when a new order is created
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        try:
            event_detail = {
                "orderId": order_data.get("orderId"),
                "customerId": order_data.get("customerId"),
                "items": order_data.get("items", []),
                "totalAmount": order_data.get("totalAmount"),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "placed"
            }
            
            return self._publish_event(
                detail_type="OrderPlaced",
                detail=event_detail
            )
            
        except Exception as e:
            logger.error(f"Failed to publish OrderPlaced event: {str(e)}", 
                        extra={"orderId": order_data.get("orderId")})
            return False
    
    def publish_order_updated_event(self, order_id: str, status: str, details: Optional[Dict] = None) -> bool:
        """
        Publish OrderUpdated event when order status changes
        
        Args:
            order_id: The order identifier
            status: New status of the order
            details: Additional details about the update
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        try:
            event_detail = {
                "orderId": order_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
            
            return self._publish_event(
                detail_type="OrderUpdated",
                detail=event_detail
            )
            
        except Exception as e:
            logger.error(f"Failed to publish OrderUpdated event: {str(e)}", 
                        extra={"orderId": order_id})
            return False
    
    def publish_payment_processed_event(self, payment_data: Dict[str, Any]) -> bool:
        """
        Publish PaymentProcessed event when payment is completed
        
        Args:
            payment_data: Dictionary containing payment information
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        try:
            event_detail = {
                "paymentId": payment_data.get("paymentId"),
                "orderId": payment_data.get("orderId"),
                "amount": payment_data.get("amount"),
                "status": payment_data.get("status"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self._publish_event(
                detail_type="PaymentProcessed",
                detail=event_detail
            )
            
        except Exception as e:
            logger.error(f"Failed to publish PaymentProcessed event: {str(e)}", 
                        extra={"paymentId": payment_data.get("paymentId")})
            return False
    
    def publish_inventory_updated_event(self, inventory_data: Dict[str, Any]) -> bool:
        """
        Publish InventoryUpdated event when inventory is modified
        
        Args:
            inventory_data: Dictionary containing inventory information
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        try:
            event_detail = {
                "vendorId": inventory_data.get("vendorId"),
                "productId": inventory_data.get("productId"),
                "quantityChange": inventory_data.get("quantityChange"),
                "newQuantity": inventory_data.get("newQuantity"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self._publish_event(
                detail_type="InventoryUpdated",
                detail=event_detail
            )
            
        except Exception as e:
            logger.error(f"Failed to publish InventoryUpdated event: {str(e)}", 
                        extra={"productId": inventory_data.get("productId")})
            return False
    
    def _publish_event(self, detail_type: str, detail: Dict[str, Any]) -> bool:
        """
        Internal method to publish events to EventBridge
        
        Args:
            detail_type: The type of event being published
            detail: The event payload
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        try:
            if not self.event_bus_name:
                logger.error("EVENT_BUS_NAME environment variable not set")
                return False
                
            response = self.eventbridge_client.put_events(
                Entries=[
                    {
                        'Source': self.source,
                        'DetailType': detail_type,
                        'Detail': json.dumps(detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            # Check if the event was published successfully
            if response['FailedEntryCount'] == 0:
                logger.info(f"Successfully published {detail_type} event", 
                           extra={"detail": detail})
                return True
            else:
                logger.error(f"Failed to publish {detail_type} event", 
                           extra={"response": response})
                return False
                
        except Exception as e:
            logger.error(f"Error publishing event to EventBridge: {str(e)}", 
                        extra={"detail_type": detail_type, "detail": detail})
            return False

# Global instance for easy import and use
event_producer = OrderEventProducer()

# Convenience functions for direct use
def publish_order_placed(order_data: Dict[str, Any]) -> bool:
    """Convenience function to publish OrderPlaced event"""
    return event_producer.publish_order_placed_event(order_data)

def publish_order_updated(order_id: str, status: str, details: Optional[Dict] = None) -> bool:
    """Convenience function to publish OrderUpdated event"""
    return event_producer.publish_order_updated_event(order_id, status, details)

def publish_payment_processed(payment_data: Dict[str, Any]) -> bool:
    """Convenience function to publish PaymentProcessed event"""
    return event_producer.publish_payment_processed_event(payment_data)

def publish_inventory_updated(inventory_data: Dict[str, Any]) -> bool:
    """Convenience function to publish InventoryUpdated event"""
    return event_producer.publish_inventory_updated_event(inventory_data)

@exception_handler
def lambda_handler(event, context):
    """
    Lambda handler for manual event publishing (if needed)
    
    Expected event format:
    {
        "eventType": "OrderPlaced|OrderUpdated|PaymentProcessed|InventoryUpdated",
        "data": {...}
    }
    """
    logger.info("Processing event publishing request", extra={"event": event})
    
    event_type = event.get("eventType")
    data = event.get("data", {})
    
    if not event_type:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "eventType is required"})
        }
    
    success = False
    
    if event_type == "OrderPlaced":
        success = publish_order_placed(data)
    elif event_type == "OrderUpdated":
        order_id = data.get("orderId")
        status = data.get("status")
        details = data.get("details")
        success = publish_order_updated(order_id, status, details)
    elif event_type == "PaymentProcessed":
        success = publish_payment_processed(data)
    elif event_type == "InventoryUpdated":
        success = publish_inventory_updated(data)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unknown eventType: {event_type}"})
        }
    
    if success:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"{event_type} event published successfully"})
        }
    else:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to publish {event_type} event"})
        }
