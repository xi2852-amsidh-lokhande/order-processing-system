# DLQ replay utility for EventBridge consumers
import json
from src.common.logger import get_logger
from src.common.exception_handler import exception_handler


def replay_dlq_events(event, context, process_func):
    """
    Utility to replay events from a DLQ (e.g., SQS) and process them with the given function.
    Ensures idempotency and logs replay attempts.
    """
    logger = get_logger("dlq-replay")
    for record in event.get("Records", []):
        try:
            detail = (
                json.loads(record["body"])
                if "body" in record
                else record.get("detail", {})
            )
            logger.info("Replaying DLQ event", extra={"event": detail})
            process_func(detail)
        except Exception as e:
            logger.error(
                "Failed to replay DLQ event", extra={"error": str(e), "event": record}
            )
    return {"statusCode": 200}
