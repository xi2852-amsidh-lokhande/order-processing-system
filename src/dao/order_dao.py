# Data access for order records
import os
import boto3
import json
from botocore.exceptions import ClientError
from src.common.exceptions import InternalServerError

ORDERS_TABLE = os.getenv("ORDERS_TABLE", "Orders")
IDEMPOTENCY_TABLE = os.getenv("IDEMPOTENCY_TABLE", "IdempotencyKeys")
dynamodb = boto3.resource("dynamodb")
client = boto3.client("dynamodb")
table = dynamodb.Table(ORDERS_TABLE)


def save_order(order_record):
    order_id = order_record.get("orderId")
    transact_items = [
        {
            "Put": {
                "TableName": ORDERS_TABLE,
                "Item": {
                    k: (
                        {"S": json.dumps(v)} if isinstance(v, (dict, list))
                        else {"S": str(v)} if isinstance(v, str)
                        else {"N": str(v)}
                    )
                    for k, v in order_record.items()
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
                    "Item": {"idempotencyKey": {"S": order_id}},
                    "ConditionExpression": "attribute_not_exists(idempotencyKey)",
                }
            }
        )
    try:
        client.transact_write_items(TransactItems=transact_items)
    except ClientError as e:
        raise InternalServerError(recommended_data={"details": str(e)})
