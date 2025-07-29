# Centralized exception handling and ErrorDetail object

import datetime
"""Custom exceptions for the order processing system."""
from typing import Dict, Any
from dataclasses import dataclass
from .constants import ERROR_CODES


class ErrorDetail(Exception):
    def __init__(self, error_code, error_message, recommended_data=None):
        self.errorCode = error_code
        self.errorMessage = error_message
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.recommendedData = recommended_data
        super().__init__(self.errorMessage)

    def to_dict(self):
        error = {
            "errorCode": self.errorCode,
            "errorMessage": self.errorMessage,
            "timestamp": self.timestamp,
        }
        if self.recommendedData is not None:
            error["recommendedData"] = self.recommendedData
        return error


class UnauthorizedException(ErrorDetail):
    def __init__(self, message=None, recommended_data=None):
        super().__init__(
            "UNAUTHORIZED",
            message or ERROR_CODES["UNAUTHORIZED"],
            recommended_data,
        )


class NotFoundException(ErrorDetail):
    def __init__(self, message=None, recommended_data=None):
        super().__init__(
            "NOT_FOUND",
            message or ERROR_CODES["NOT_FOUND"],
            recommended_data,
        )


class BadRequestException(ErrorDetail):
    def __init__(self, message=None, recommended_data=None):
        super().__init__(
            "BAD_REQUEST",
            message or ERROR_CODES["BAD_REQUEST"],
            recommended_data,
        )


class InternalServerError(ErrorDetail):
    def __init__(self, message=None, recommended_data=None):
        super().__init__(
            "INTERNAL_SERVER_ERROR",
            message or ERROR_CODES["INTERNAL_SERVER_ERROR"],
            recommended_data,
        )
