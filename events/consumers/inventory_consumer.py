from src.common.idempotency import is_idempotent, mark_idempotent
from src.common.dlq_replay import replay_dlq_events


# DLQ replay Lambda entrypoint
def replay_handler(event, context):
    return replay_dlq_events(event, context, process_func=_process_inventory_event)


# Internal processing function for both normal and replay
def _process_inventory_event(detail):
    logger = get_logger("inventory-consumer")
    order_id = detail.get("orderId")
    if not order_id:
        logger.error("Missing orderId in event detail", extra={"event": detail})
        return
    if is_idempotent(order_id):
        logger.info("Duplicate event ignored (idempotent)", extra={"orderId": order_id})
        return
    logger.info(
        "Processing OrderPlaced event for inventory",
        extra={"orderId": order_id},
    )
    for item in detail.get("items", []):
        update_inventory(
            {
                "vendorId": item.get("vendorId"),
                "productId": item.get("productId"),
                "quantity": -item.get("quantity", 1),
            }
        )
    mark_idempotent(order_id)


import json
from src.common.logger import get_logger
from src.common.exception_handler import exception_handler
from src.services.inventory_service import update_inventory


@exception_handler
def lambda_handler(event, context):
    logger = get_logger("inventory-consumer")
    for record in event.get("Records", []):
        detail = (
            json.loads(record["body"]) if "body" in record else record.get("detail", {})
        )
        logger.info(
            "Processing OrderPlaced event for inventory",
            extra={"orderId": detail.get("orderId")},
        )
        # Example: update inventory for each item
        for item in detail.get("items", []):
            update_inventory(
                {
                    "vendorId": item.get("vendorId"),
                    "productId": item.get("productId"),
                    "quantity": -item.get("quantity", 1),  # Decrement inventory
                }
            )
    return {"statusCode": 200}
