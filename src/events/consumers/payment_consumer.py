from common.idempotency import is_idempotent, mark_idempotent
from common.dlq_replay import replay_dlq_events


# DLQ replay Lambda entrypoint
def replay_handler(event, context):
    return replay_dlq_events(event, context, process_func=_process_payment_event)


# Internal processing function for both normal and replay
def _process_payment_event(detail):
    logger = get_logger("payment-consumer")
    order_id = detail.get("orderId")
    if not order_id:
        logger.error("Missing orderId in event detail", extra={"event": detail})
        return
    if is_idempotent(order_id):
        logger.info("Duplicate event ignored (idempotent)", extra={"orderId": order_id})
        return
    logger.info(
        "Processing OrderPlaced event for payment",
        extra={"orderId": order_id},
    )
    process_payment(
        {
            "orderId": order_id,
            "amount": detail.get("amount", 0),
            "paymentMethod": detail.get("paymentMethod", "default"),
        }
    )
    mark_idempotent(order_id)


import json
from common.logger import get_logger
from common.exception_handler import exception_handler
from services.payment_service import process_payment


@exception_handler
def lambda_handler(event, context):
    logger = get_logger("payment-consumer")
    for record in event.get("Records", []):
        detail = (
            json.loads(record["body"]) if "body" in record else record.get("detail", {})
        )
        logger.info(
            "Processing OrderPlaced event for payment",
            extra={"orderId": detail.get("orderId")},
        )
        # Example: process payment for the order
        process_payment(
            {
                "orderId": detail.get("orderId"),
                "amount": detail.get("amount", 0),
                "paymentMethod": detail.get("paymentMethod", "default"),
            }
        )
    return {"statusCode": 200}
