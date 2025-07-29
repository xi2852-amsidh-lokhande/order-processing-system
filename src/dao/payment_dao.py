# Data access for payment records
import os
import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError
from common.exceptions import InternalServerError

PAYMENTS_TABLE = os.getenv("PAYMENTS_TABLE", "Payments")
IDEMPOTENCY_TABLE = os.getenv("IDEMPOTENCY_TABLE", "IdempotencyKeys")
dynamodb = boto3.resource("dynamodb")
client = boto3.client("dynamodb")
table = dynamodb.Table(PAYMENTS_TABLE)


def save_payment(payment_record):
    order_id = payment_record.get("orderId")
    transact_items = [
        {
            "Put": {
                "TableName": PAYMENTS_TABLE,
                "Item": {
                    k: {"S": str(v)} if isinstance(v, str) else {"N": str(v)}
                    for k, v in payment_record.items()
                },
            }
        }
    ]
    # Add idempotency record if order_id is present
    if order_id:
        transact_items.append(
            {
                "Put": {
                    "TableName": IDEMPOTENCY_TABLE,
                    "Item": {"id": {"S": order_id}},
                    "ConditionExpression": "attribute_not_exists(id)",
                }
            }
        )
    try:
        client.transact_write_items(TransactItems=transact_items)
    except ClientError as e:
        raise InternalServerError(recommended_data={"details": str(e)})
