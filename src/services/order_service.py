# Business logic for order processing
from src.common.logger import get_logger
from src.dao.order_dao import save_order
import os
import boto3
import uuid
from datetime import datetime, timezone
import json


def place_order(order_data):
    logger = get_logger("order-service")
    # Validation is handled at the handler layer
    order_id = str(uuid.uuid4())
    order_record = {
        "orderId": order_id,
        "customerId": order_data["customerId"],
        "items": order_data["items"],
        "status": "PLACED",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    # Save order
    save_order(order_record)
    logger.info("Order saved", extra={"orderId": order_id})

    # Publish OrderPlaced event to EventBridge
    eventbridge = boto3.client("events")
    event_bus_name = os.getenv("EVENT_BUS_NAME", "default")
    event_detail = {
        "orderId": order_id,
        "customerId": order_data["customerId"],
        "items": order_data["items"],
        "status": "PLACED",
    }
    eventbridge.put_events(
        Entries=[
            {
                "Source": "order-service",
                "DetailType": "OrderPlaced",
                "Detail": json.dumps(event_detail),
                "EventBusName": event_bus_name,
            }
        ]
    )
    logger.info("OrderPlaced event published", extra={"orderId": order_id})
    return {"orderId": order_id}
