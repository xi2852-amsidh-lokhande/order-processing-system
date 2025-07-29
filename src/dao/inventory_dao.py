# Data access for inventory records
import os
import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError
from common.exceptions import InternalServerError

INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "Inventory")
IDEMPOTENCY_TABLE = os.getenv("IDEMPOTENCY_TABLE", "IdempotencyKeys")

# Lazy initialization to ensure X-Ray patching happens first
_dynamodb = None
_client = None
_table = None

def get_dynamodb_resources():
    """Get DynamoDB resources with lazy initialization to ensure X-Ray patching"""
    global _dynamodb, _client, _table
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
        _client = boto3.client("dynamodb")
        _table = _dynamodb.Table(INVENTORY_TABLE)
    return _dynamodb, _client, _table


def update_inventory_record(inventory_record):
    # Get DynamoDB resources with lazy initialization
    dynamodb, client, table = get_dynamodb_resources()
    
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
