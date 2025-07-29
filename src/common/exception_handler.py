import json
from src.common.logger import get_logger
from src.common.exceptions import ErrorDetail, InternalServerError


def exception_handler(func):
    def wrapper(event, context):
        logger = get_logger("order-handler")
        try:
            return func(event, context)
        except ErrorDetail as e:
            logger.error("Handled error", extra={"error": e.to_dict()})
            return {"statusCode": 400, "body": json.dumps(e.to_dict())}
        except Exception as e:
            logger.error("Unhandled error", extra={"error": str(e)})
            err = InternalServerError(recommended_data={"details": str(e)})
            return {"statusCode": 500, "body": json.dumps(err.to_dict())}

    return wrapper
