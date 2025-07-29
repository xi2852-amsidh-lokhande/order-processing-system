# Business logic for payment processing
import uuid
from common.logger import get_logger
from dao.payment_dao import save_payment
from datetime import datetime, timezone
from events.producer.producer import publish_payment_processed


def process_payment(data):
    logger = get_logger("payment-service")
    payment_id = str(uuid.uuid4())  # Generate a unique payment ID
    order_id = data["orderId"]
    amount = data["amount"]

    payment_record = {
        "paymentId": payment_id,
        "orderId": order_id,
        "amount": amount,
        "paymentMethod": data.get("paymentMethod", "card"),
        "status": "PROCESSED",
        "processedAt": datetime.now(timezone.utc).isoformat(),
    }
    
    # Save payment to DynamoDB
    save_payment(payment_record)
    logger.info("Payment record saved", extra={"orderId": order_id, "paymentId": payment_id})

    # Publish PaymentProcessed event using the producer
    event_published = publish_payment_processed({
        "paymentId": payment_id,
        "orderId": order_id,
        "amount": amount,
        "status": "completed",
    })
    
    if event_published:
        logger.info("PaymentProcessed event published successfully", 
                   extra={"orderId": order_id, "paymentId": payment_id})
    else:
        logger.error("Failed to publish PaymentProcessed event", 
                    extra={"orderId": order_id, "paymentId": payment_id})
    
    return {
        "paymentId": payment_id,
        "orderId": order_id,
        "amount": amount,
        "status": "PROCESSED",
        "eventPublished": event_published
    }


def refund_payment(payment_id: str, refund_amount: float, reason: str = None):
    """
    Process a payment refund and publish events
    
    Args:
        payment_id: The payment identifier to refund
        refund_amount: Amount to refund
        reason: Reason for the refund
        
    Returns:
        dict: Refund result
    """
    logger = get_logger("payment-service")
    
    try:
        refund_id = str(uuid.uuid4())
        
        refund_record = {
            "refundId": refund_id,
            "paymentId": payment_id,
            "amount": refund_amount,
            "reason": reason or "Customer requested refund",
            "status": "PROCESSED",
            "processedAt": datetime.now(timezone.utc).isoformat(),
        }
        
        # In real implementation, save refund to DynamoDB
        # save_refund(refund_record)
        
        logger.info("Refund processed", 
                   extra={"paymentId": payment_id, "refundId": refund_id, "amount": refund_amount})
        
        # Publish refund event (could extend producer for this)
        # For now, we can use payment_processed with refund status
        event_published = publish_payment_processed({
            "paymentId": refund_id,
            "orderId": payment_id,  # Using payment_id as reference
            "amount": -refund_amount,  # Negative amount indicates refund
            "status": "refunded",
        })
        
        return {
            "refundId": refund_id,
            "paymentId": payment_id,
            "amount": refund_amount,
            "status": "PROCESSED",
            "eventPublished": event_published
        }
        
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}", 
                    extra={"paymentId": payment_id})
        return {
            "success": False,
            "paymentId": payment_id,
            "error": str(e)
        }
