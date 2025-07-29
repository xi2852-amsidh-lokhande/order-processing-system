# Business logic for inventory management
from src.common.logger import get_logger
from src.dao.inventory_dao import update_inventory_record
from datetime import datetime, timezone


def update_inventory(data):
    logger = get_logger("inventory-service")
    inventory_record = {
        "vendorId": data["vendorId"],
        "productId": data["productId"],
        "quantity": data["quantity"],
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    update_inventory_record(inventory_record)
    logger.info(
        "Inventory record updated",
        extra={"vendorId": data["vendorId"], "productId": data["productId"]},
    )
    return {"vendorId": data["vendorId"], "productId": data["productId"]}
