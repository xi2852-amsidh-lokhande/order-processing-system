# Business logic for payment processing
from src.common.logger import get_logger
from src.dao.payment_dao import save_payment
from datetime import datetime, timezone


def process_payment(data):
    logger = get_logger("payment-service")
    payment_record = {
        "orderId": data["orderId"],
        "amount": data["amount"],
        "paymentMethod": data["paymentMethod"],
        "status": "PROCESSED",
        "processedAt": datetime.now(timezone.utc).isoformat(),
    }
    save_payment(payment_record)
    logger.info("Payment record saved", extra={"orderId": data["orderId"]})
    return {"orderId": data["orderId"]}
