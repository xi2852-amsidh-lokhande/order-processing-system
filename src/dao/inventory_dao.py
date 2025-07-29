# Data access for inventory records
import os
import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError
from common.exceptions import InternalServerError

INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "Inventory")
IDEMPOTENCY_TABLE = os.getenv("IDEMPOTENCY_TABLE", "IdempotencyKeys")
dynamodb = boto3.resource("dynamodb")
client = boto3.client("dynamodb")
table = dynamodb.Table(INVENTORY_TABLE)


def update_inventory_record(inventory_record):
    order_id = inventory_record.get("orderId")
    transact_items = [
        {
            "Put": {
                "TableName": INVENTORY_TABLE,
                "Item": {
                    k: {"S": str(v)} if isinstance(v, str) else {"N": str(v)}
                    for k, v in inventory_record.items()
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
