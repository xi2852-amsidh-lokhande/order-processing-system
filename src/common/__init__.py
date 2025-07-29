# Cross-Cutting X-Ray Bootstrap for Order Processing System
# This module ensures X-Ray DynamoDB tracing is applied automatically
# whenever any common module is imported - TRUE CROSS-CUTTING CONCERN

# CRITICAL: Import X-Ray auto-patching FIRST before any other imports
# This ensures boto3 is patched before any DAO operations
from . import xray_auto_patch

# Now import other common modules safely
from .logger import get_logger
from .constants import ERROR_CODES
from .exceptions import ErrorDetail, BadRequestException, InternalServerError
from .validation import validate_request
from .idempotency import is_idempotent, mark_idempotent
from .utils import get_utc_timestamp, generate_idempotency_key
from .exception_handler import exception_handler

# Export commonly used items for easy importing
__all__ = [
    'get_logger', 
    'ERROR_CODES',
    'ErrorDetail',
    'BadRequestException',
    'InternalServerError',
    'validate_request',
    'is_idempotent',
    'mark_idempotent',
    'get_utc_timestamp',
    'generate_idempotency_key',
    'exception_handler',
    'xray_auto_patch'
]
