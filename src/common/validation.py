from .exceptions import BadRequestException


def validate_request(data, required_fields=None):
    """
    Validates that required fields are present in the data dict.
    Raises BadRequestException if any required field is missing.
    """
    if not data:
        raise BadRequestException(
            recommended_data={"details": "Request body is missing or empty."}
        )
    if required_fields:
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise BadRequestException(
                recommended_data={
                    "details": f"Missing required fields: {', '.join(missing)}"
                }
            )
    return True
