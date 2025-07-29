# Root src package
# Cross-cutting concern: Auto-enable X-Ray tracing for all modules
# This ensures DynamoDB and other AWS services are traced without code changes

try:
    # Import X-Ray auto-patching as a cross-cutting concern
    from common import xray_auto_patch
except ImportError:
    # If X-Ray patching fails, continue without it
    pass
