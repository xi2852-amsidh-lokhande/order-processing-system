# Auto-import module that patches boto3 for X-Ray without requiring code changes
# This module is automatically imported by Lambda when the layer is attached

import os
import sys

# Only run if X-Ray auto-patching is enabled
if os.environ.get('ENABLE_XRAY_AUTOPATCH', '').lower() == 'true':
    try:
        from aws_xray_sdk.core import xray_recorder, patch
        
        # Configure X-Ray recorder
        xray_recorder.configure(
            context_missing='LOG_ERROR',
            service=os.environ.get('AWS_XRAY_TRACING_NAME', 'order-processing-system')
        )
        
        # Patch boto3 for automatic tracing
        patch(['boto3'])
        
        print("X-Ray auto-patching enabled for boto3 (DynamoDB tracing active)")
        
    except ImportError:
        # aws-xray-sdk not available
        print("X-Ray SDK not available - no patching applied")
    except Exception as e:
        # Log error but don't fail
        print(f"X-Ray patching error: {e}")
