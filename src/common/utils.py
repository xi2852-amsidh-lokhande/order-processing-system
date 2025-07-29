# Shared utility functions

import uuid
from datetime import datetime, timezone


def get_utc_timestamp():
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_idempotency_key():
    """Generate a unique idempotency key."""
    return str(uuid.uuid4())


# Trace ID utilities for end-to-end traceability
TRACE_ID_HEADER = "X-Trace-Id"


def generate_trace_id():
    """Generate a new trace ID."""
    return str(uuid.uuid4())


def extract_trace_id(event):
    """Extract trace ID from Lambda event headers or context."""
    headers = event.get("headers", {})
    trace_id = headers.get(TRACE_ID_HEADER) or event.get("trace_id")
    return trace_id or generate_trace_id()


def propagate_trace_id(payload, trace_id):
    """Attach trace ID to outgoing event or payload."""
    payload = dict(payload)  # shallow copy
    payload["trace_id"] = trace_id
    return payload
