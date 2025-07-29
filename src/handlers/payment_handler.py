import json
from src.common.logger import get_logger
from src.common.exception_handler import exception_handler
from src.common.validation import validate_request
from src.services.payment_service import process_payment


@exception_handler
def lambda_handler(event, context):
    logger = get_logger("payment-handler")
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    validate_request(body, required_fields=["orderId", "amount", "paymentMethod"])
    process_payment(body)
    logger.info("Payment processed", extra={"orderId": body["orderId"]})
    return {
        "statusCode": 200,
        "body": json.dumps({"success": True, "orderId": body["orderId"]}),
    }
