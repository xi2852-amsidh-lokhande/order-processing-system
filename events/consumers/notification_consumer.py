from src.common.idempotency import is_idempotent, mark_idempotent
from src.common.dlq_replay import replay_dlq_events


# DLQ replay Lambda entrypoint
def replay_handler(event, context):
    return replay_dlq_events(event, context, process_func=_process_notification_event)


# Internal processing function for both normal and replay
def _process_notification_event(detail):
    logger = get_logger("notification-consumer")
    order_id = detail.get("orderId")
    if not order_id:
        logger.error("Missing orderId in event detail", extra={"event": detail})
        return
    if is_idempotent(order_id):
        logger.info("Duplicate event ignored (idempotent)", extra={"orderId": order_id})
        return
    logger.info(
        "Sending notification for order",
        extra={
            "orderId": order_id,
            "customerId": detail.get("customerId"),
        },
    )
    # Integrate with notification service here
    mark_idempotent(order_id)


import json
from src.common.logger import get_logger
from src.common.exception_handler import exception_handler


@exception_handler
def lambda_handler(event, context):
    logger = get_logger("notification-consumer")
    for record in event.get("Records", []):
        detail = (
            json.loads(record["body"]) if "body" in record else record.get("detail", {})
        )
        logger.info(
            "Sending notification for order",
            extra={
                "orderId": detail.get("orderId"),
                "customerId": detail.get("customerId"),
            },
        )
        # Here you would integrate with email/SMS/notification service
    return {"statusCode": 200}
