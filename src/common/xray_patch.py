# X-Ray auto-patching for AWS services
# This module automatically patches AWS services for X-Ray tracing

try:
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    
    # Auto-patch all AWS services for X-Ray tracing
    patch_all()
    
    # Configure X-Ray recorder
    xray_recorder.configure(
        context_missing='LOG_ERROR',
        plugins=('EC2Plugin', 'ECSPlugin'),
        daemon_address='127.0.0.1:2000'
    )
    
except ImportError:
    # X-Ray SDK not available - silently skip patching
    # This allows the code to work in environments without X-Ray
    pass
except Exception:
    # Any other X-Ray configuration error - silently skip
    # This ensures the application continues to work even if X-Ray fails
    pass
