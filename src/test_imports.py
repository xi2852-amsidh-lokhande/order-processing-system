#!/usr/bin/env python3
"""
Quick test to verify all imports work correctly
"""

print("Testing imports...")

try:
    # Test common module imports
    from common.logger import get_logger
    print("✅ common.logger import successful")
    
    from common.exceptions import BadRequestException
    print("✅ common.exceptions import successful")
    
    from common.validation import validate_request
    print("✅ common.validation import successful")
    
    from common.exception_handler import exception_handler
    print("✅ common.exception_handler import successful")
    
    # Test service imports
    from services.order_service import place_order
    print("✅ services.order_service import successful")
    
    # Test handler imports
    from handlers.order_handler import lambda_handler
    print("✅ handlers.order_handler import successful")
    
    print("\n🎉 All imports successful! The fix worked.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
