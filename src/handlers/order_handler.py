# Handler for order-related Lambda events
import json

from common.logger import get_logger
from common.exceptions import BadRequestException
from services.order_service import place_order
from common.exception_handler import exception_handler
from common.validation import validate_request
from events.producer.producer import publish_order_placed


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
    # After saving order to DynamoDB
    publish_order_placed(
        {
            "orderId": order_result.get("orderId"),
            "customerId": body.get("customerId"),
            "items": body.get("items"),
            "totalAmount": order_result.get("totalAmount"),
        }
    )
    return {
        "statusCode": 201,
        "body": json.dumps({"success": True, "orderId": order_result.get("orderId")}),
    }
