import json
from common.logger import get_logger
from common.exception_handler import exception_handler
from common.validation import validate_request
from services.inventory_service import update_inventory


@exception_handler
def lambda_handler(event, context):
    logger = get_logger("inventory-handler")
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    validate_request(body, required_fields=["vendorId", "productId", "quantity"])
    update_inventory(body)
    logger.info(
        "Inventory updated",
        extra={"vendorId": body["vendorId"], "productId": body["productId"]},
    )
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "success": True,
                "vendorId": body["vendorId"],
                "productId": body["productId"],
            }
        ),
    }
