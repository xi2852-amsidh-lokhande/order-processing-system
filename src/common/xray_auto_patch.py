# X-Ray auto-patching for AWS services
# This module automatically patches AWS services for X-Ray tracing
# Import this module FIRST to ensure all boto3 calls are traced

import os

# Check if X-Ray auto-patching is enabled via environment variable
if os.environ.get('XRAY_AUTO_PATCH', '').lower() == 'true':
    try:
        from aws_xray_sdk.core import xray_recorder
        from aws_xray_sdk.core import patch_all
        
        # Auto-patch all AWS services for X-Ray tracing (including DynamoDB)
        patch_all()
        
        # Configure X-Ray recorder for Lambda environment
        xray_recorder.configure(
            context_missing='LOG_ERROR',
            plugins=('EC2Plugin', 'ECSPlugin'),
        )
        
        print("X-Ray auto-patching enabled for all AWS services including DynamoDB")
        
    except ImportError:
        # X-Ray SDK not available - silently skip patching
        print("X-Ray SDK not available - skipping patching")
        pass
    except Exception as e:
        # Any other X-Ray configuration error - silently skip
        print(f"X-Ray configuration error: {e} - skipping patching")
        pass
else:
    print("X-Ray auto-patching disabled - set XRAY_AUTO_PATCH=true to enable")
