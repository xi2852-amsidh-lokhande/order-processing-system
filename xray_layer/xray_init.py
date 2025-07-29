# X-Ray Auto-Instrumentation Layer
# This module automatically instruments AWS SDK calls, HTTP requests, and database queries
# without requiring code changes in the application

import os
import logging
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Configure X-Ray recorder
xray_recorder.configure(
    context_missing='LOG_ERROR',
    plugins=('EC2Plugin', 'ECSPlugin', 'ElasticBeanstalkPlugin'),
    daemon_address=os.environ.get('_X_AMZN_TRACE_ID', '127.0.0.1:2000'),
    service=os.environ.get('AWS_XRAY_TRACING_NAME', 'order-processing-system')
)

# Patch all AWS SDK calls for automatic tracing
patch_all()

# Configure logging for X-Ray
logging.getLogger('aws_xray_sdk').setLevel(logging.WARNING)

def lambda_handler_wrapper(original_handler):
    """
    Wrapper function that adds X-Ray tracing to any Lambda handler
    without requiring code changes
    """
    def wrapped_handler(event, context):
        # Add trace metadata
        xray_recorder.put_metadata('lambda', {
            'function_name': context.function_name,
            'function_version': context.function_version,
            'request_id': context.aws_request_id,
            'memory_limit': context.memory_limit_in_mb
        })
        
        # Add annotations for filtering traces
        xray_recorder.put_annotation('service_name', os.environ.get('AWS_XRAY_TRACING_NAME', 'order-processing-system'))
        xray_recorder.put_annotation('function_name', context.function_name)
        xray_recorder.put_annotation('environment', os.environ.get('Environment', 'dev'))
        
        # Extract trace information if available
        if hasattr(event, 'get') and 'Records' in event:
            # For EventBridge/SQS events
            for record in event.get('Records', []):
                if 'eventSource' in record:
                    xray_recorder.put_annotation('event_source', record['eventSource'])
                if 'eventName' in record:
                    xray_recorder.put_annotation('event_name', record['eventName'])
        
        # Execute the original handler
        return original_handler(event, context)
    
    return wrapped_handler

# Auto-patch existing handlers by setting environment variable
if os.environ.get('ENABLE_XRAY_AUTOPATCH', 'true').lower() == 'true':
    # This ensures all imports after this will be automatically traced
    print("X-Ray auto-instrumentation enabled")
