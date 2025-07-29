# Idempotency utility for event processing
import os
import boto3
from botocore.exceptions import ClientError

IDEMPOTENCY_TABLE = os.getenv("IDEMPOTENCY_TABLE", "IdempotencyKeys")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(IDEMPOTENCY_TABLE)


def is_idempotent(key):
    try:
        response = table.get_item(Key={"idempotencyKey": key})
        return "Item" in response
    except ClientError:
        return False


def mark_idempotent(key):
    try:
        table.put_item(Item={"idempotencyKey": key})
    except ClientError:
        pass
