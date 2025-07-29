# Data access for order records
import os
import boto3
import json
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError
from common.exceptions import InternalServerError

# Use the correct environment variable names from template.yaml
ORDERS_TABLE = os.getenv("ORDERS_TABLE", "Orders")
IDEMPOTENCY_TABLE = os.getenv("IDEMPOTENCY_TABLE", "IdempotencyKeys")

# Lazy initialization to ensure X-Ray patching happens first
_dynamodb = None
_table = None

def get_dynamodb_table():
    """Get DynamoDB table with lazy initialization to ensure X-Ray patching"""
    global _dynamodb, _table
    if _table is None:
        _dynamodb = boto3.resource("dynamodb")
        _table = _dynamodb.Table(ORDERS_TABLE)
    return _table


def save_order(order_record):
    """Save order using high-level DynamoDB resource for simplicity"""
    try:
        # Get DynamoDB table with lazy initialization
        table = get_dynamodb_table()
        
        # Use high-level put_item instead of low-level transact_write
        table.put_item(Item=order_record)
        
        # Handle idempotency separately if needed
        order_id = order_record.get("orderId")
        if order_id:
            idempotency_table = _dynamodb.Table(IDEMPOTENCY_TABLE)
            try:
                # Use the correct key name 'id' as defined in template.yaml
                idempotency_table.put_item(
                    Item={"id": order_id},
                    ConditionExpression="attribute_not_exists(id)"
                )
            except ClientError as e:
                # If idempotency check fails, it's likely a duplicate - that's okay
                if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                    raise
                    
    except ClientError as e:
        raise InternalServerError(recommended_data={"details": str(e)})
