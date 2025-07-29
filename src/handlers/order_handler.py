# Handler for order-related Lambda events
import json

from src.common.logger import get_logger
from src.common.exceptions import BadRequestException
from src.services.order_service import place_order
from src.common.exception_handler import exception_handler
from src.common.validation import validate_request


@exception_handler
def lambda_handler(event, context):
    logger = get_logger("order-handler")
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    # Centralized validation for required fields
    validate_request(body, required_fields=["customerId", "items"])
    # Place order
    order_result = place_order(body)
    logger.info(
        "Order placed successfully", extra={"orderId": order_result.get("orderId")}
    )
    return {
        "statusCode": 201,
        "body": json.dumps({"success": True, "orderId": order_result.get("orderId")}),
    }
