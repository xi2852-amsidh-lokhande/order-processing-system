#!/usr/bin/env python3
"""
Test script to verify distributed tracing is working across the order processing system
"""

import json
import requests
import time
import boto3
from datetime import datetime

def test_distributed_tracing():
    """Test the complete order flow and verify tracing"""
    
    # Configuration - update these with your actual API Gateway URL
    API_BASE_URL = "https://your-api-gateway-url.execute-api.region.amazonaws.com/dev"
    
    print("🔍 Testing Distributed Tracing for Order Processing System")
    print("=" * 60)
    
    # Test data
    test_order = {
        "customerId": "test-customer-123",
        "items": [
            {
                "productId": "product-1",
                "vendorId": "vendor-1", 
                "quantity": 2,
                "price": 29.99
            },
            {
                "productId": "product-2",
                "vendorId": "vendor-2",
                "quantity": 1,
                "price": 49.99
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer demo-token"
    }
    
    try:
        # 1. Place an order (this will trigger the entire flow)
        print("📦 Placing test order...")
        order_response = requests.post(
            f"{API_BASE_URL}/orders",
            json=test_order,
            headers=headers
        )
        
        if order_response.status_code == 201:
            order_data = order_response.json()
            order_id = order_data.get("orderId")
            print(f"✅ Order placed successfully! Order ID: {order_id}")
            
            # Add trace header to track this request
            trace_id = order_response.headers.get("X-Amzn-Trace-Id", "Not found")
            print(f"🔗 X-Ray Trace ID: {trace_id}")
            
            # 2. Wait for async processing
            print("⏳ Waiting for EventBridge consumers to process...")
            time.sleep(10)
            
            # 3. Check X-Ray traces
            print("🔍 Checking X-Ray traces...")
            check_xray_traces(trace_id)
            
        else:
            print(f"❌ Order placement failed: {order_response.status_code}")
            print(f"Response: {order_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def check_xray_traces(trace_id):
    """Check if traces are being generated in X-Ray"""
    
    try:
        xray_client = boto3.client('xray')
        
        # Get traces from the last 5 minutes
        end_time = datetime.utcnow()
        start_time = datetime.utcnow().replace(minute=datetime.utcnow().minute - 5)
        
        response = xray_client.get_trace_summaries(
            TimeRangeType='TimeRangeByStartTime',
            StartTime=start_time,
            EndTime=end_time,
            FilterExpression='service("order-processing-system")'
        )
        
        traces = response.get('TraceSummaries', [])
        
        if traces:
            print(f"✅ Found {len(traces)} traces in X-Ray!")
            
            for trace in traces[:3]:  # Show first 3 traces
                print(f"   📊 Trace ID: {trace.get('Id', 'Unknown')}")
                print(f"   ⏱️  Duration: {trace.get('Duration', 0):.3f}s")
                print(f"   🎯 Response Time: {trace.get('ResponseTime', 0):.3f}s")
                
                if trace.get('ErrorRootCauses'):
                    print(f"   ❌ Errors: {len(trace.get('ErrorRootCauses'))}")
                else:
                    print(f"   ✅ No errors")
                print()
                
            # Get service statistics
            print("📈 Service Statistics:")
            get_service_statistics()
            
        else:
            print("⚠️  No traces found in X-Ray. This could mean:")
            print("   - Traces are still being processed (wait a few minutes)")
            print("   - X-Ray tracing is not properly configured")
            print("   - The request didn't generate traces")
            
    except Exception as e:
        print(f"❌ Failed to check X-Ray traces: {e}")
        print("   Make sure you have X-Ray permissions and the service is configured")

def get_service_statistics():
    """Get service map and statistics"""
    
    try:
        xray_client = boto3.client('xray')
        
        # Get service statistics
        end_time = datetime.utcnow()
        start_time = datetime.utcnow().replace(minute=datetime.utcnow().minute - 10)
        
        response = xray_client.get_service_graph(
            StartTime=start_time,
            EndTime=end_time
        )
        
        services = response.get('Services', [])
        
        if services:
            print("🗺️  Service Map:")
            for service in services:
                name = service.get('Name', 'Unknown')
                state = service.get('State', 'Unknown')
                
                # Get response time statistics
                response_time_histogram = service.get('ResponseTimeHistogram', {})
                edges = service.get('Edges', [])
                
                print(f"   🔧 Service: {name}")
                print(f"   📊 State: {state}")
                print(f"   🔗 Connections: {len(edges)}")
                
                if response_time_histogram:
                    total_count = response_time_histogram.get('TotalCount', 0)
                    print(f"   📈 Total Requests: {total_count}")
                
                print()
        else:
            print("   No services found in service map")
            
    except Exception as e:
        print(f"❌ Failed to get service statistics: {e}")

def print_next_steps():
    """Print instructions for viewing traces"""
    
    print("🚀 Next Steps:")
    print("=" * 40)
    print("1. 📊 View X-Ray Service Map:")
    print("   - Go to AWS X-Ray Console")
    print("   - Click on 'Service map'")
    print("   - You should see your services connected")
    print()
    print("2. 🔍 Analyze Traces:")
    print("   - Click on 'Traces' in X-Ray console")
    print("   - Filter by service name: order-processing-system")
    print("   - Click on individual traces for detailed timeline")
    print()
    print("3. 📈 Monitor Performance:")
    print("   - Set up CloudWatch alarms for error rates")
    print("   - Monitor latency percentiles")
    print("   - Use ServiceLens for enhanced monitoring")
    print()
    print("4. 🔧 Customize Sampling:")
    print("   - Adjust sampling rules if needed")
    print("   - Configure trace retention")
    print("   - Set up custom annotations")

if __name__ == "__main__":
    test_distributed_tracing()
    print()
    print_next_steps()
