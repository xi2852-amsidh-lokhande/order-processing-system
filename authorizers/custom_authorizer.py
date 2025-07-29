import base64
import json
import os
import logging
import boto3
import hashlib


def generate_policy(principal_id, effect, resource, context=None):
    auth_response = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
    }
    if context:
        auth_response["context"] = context
    return auth_response


def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    token = event.get("authorizationToken")
    method_arn = event.get("methodArn")
    if not token:
        logger.warning("No authorization token provided")
        raise PermissionError("Unauthorized")

    # Helper: fetch user secrets from AWS Secrets Manager
    def get_user_secret(username):
        secret_name = f"user/{username}"
        # AWS Lambda automatically provides the region in the execution environment
        region = boto3.Session().region_name or "us-east-1"
        client = boto3.client("secretsmanager", region_name=region)
        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(get_secret_value_response["SecretString"])
            return secret  # expects {"password_hash": ..., "role": ...}
        except client.exceptions.ResourceNotFoundException:
            return None
        except Exception as e:
            logger.error(f"Secrets Manager error: {e}")
            return None

    # Example: Basic Auth (username:password base64)
    if token.startswith("Basic "):
        try:
            b64_creds = token.split(" ")[1]
            creds = base64.b64decode(b64_creds).decode("utf-8")
            username, password = creds.split(":", 1)
            user_secret = get_user_secret(username)
            if not user_secret:
                logger.warning("User not found in Secrets Manager")
                raise PermissionError("Unauthorized")
            # Passwords should be stored as salted hashes (e.g., SHA256)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == user_secret.get("password_hash"):
                user_context = {
                    "role": user_secret.get("role", "user"),
                    "username": username,
                }
                return generate_policy(username, "Allow", method_arn, user_context)
            else:
                logger.warning("Invalid username or password")
                raise PermissionError("Unauthorized")
        except Exception as e:
            logger.error(f"Basic auth error: {e}")
            raise PermissionError("Unauthorized")

    # Example: Bearer token (role-based)
    if token.startswith("Bearer "):
        jwt_token = token.split(" ")[1]
        # Replace with real JWT validation and role extraction
        # For demo, accept a static token
        if jwt_token == os.getenv("AUTH_TOKEN", "demo-token"):
            user_context = {"role": "user", "username": "demo"}
            return generate_policy("demo", "Allow", method_arn, user_context)
        else:
            logger.warning("Invalid bearer token")
            raise PermissionError("Unauthorized")

    logger.warning("Unsupported authorization method")
    raise PermissionError("Unauthorized")
