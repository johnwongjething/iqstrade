#!/usr/bin/env python3
"""
Backend Route Registration Diagnostic Script
Checks if balance routes are properly registered in the Flask app
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://iqstrade.onrender.com"

def test_route_registration():
    """Test if balance routes are registered"""
    print("=" * 50)
    print("BACKEND ROUTE REGISTRATION DIAGNOSTIC")
    print("=" * 50)
    print()
    
    # Test endpoints that should exist
    test_endpoints = [
        "/api/balance/search",
        "/api/balance/ray40", 
        "/api/balance/ray40/history",
        "/api/balance/ray40/adjust",
        "/api/balance/all",
        "/api/balance/",  # Root balance endpoint
        "/api/balance"    # Without trailing slash
    ]
    
    results = []
    
    for endpoint in test_endpoints:
        try:
            print(f"Testing: {endpoint}")
            response = requests.get(f"{BASE_URL}{endpoint}")
            
            status = response.status_code
            if status == 404:
                result = "❌ NOT FOUND - Route not registered"
            elif status == 401:
                result = "✅ EXISTS - Route registered (requires auth)"
            elif status == 400:
                result = "✅ EXISTS - Route registered (bad request)"
            elif status == 405:
                result = "✅ EXISTS - Route registered (method not allowed)"
            elif status == 200:
                result = "✅ EXISTS - Route registered (working)"
            else:
                result = f"⚠️  UNKNOWN - Status {status}"
            
            print(f"  Status: {status}")
            print(f"  Result: {result}")
            
            if response.text:
                print(f"  Response: {response.text[:200]}...")
            
            results.append({
                'endpoint': endpoint,
                'status_code': status,
                'result': result,
                'response': response.text[:500] if response.text else ''
            })
            
        except Exception as e:
            print(f"  Error: {str(e)}")
            results.append({
                'endpoint': endpoint,
                'status_code': 'ERROR',
                'result': f"❌ ERROR - {str(e)}",
                'response': ''
            })
        
        print()
    
    # Summary
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    registered = len([r for r in results if 'EXISTS' in r['result']])
    not_found = len([r for r in results if 'NOT FOUND' in r['result']])
    errors = len([r for r in results if 'ERROR' in r['result']])
    
    print(f"Registered Routes: {registered}")
    print(f"Not Found Routes: {not_found}")
    print(f"Errors: {errors}")
    print()
    
    if not_found > 0:
        print("❌ ISSUE DETECTED: Some balance routes are not registered!")
        print("This suggests the balance_routes blueprint is not properly imported in app.py")
        print()
        print("Missing routes:")
        for result in results:
            if 'NOT FOUND' in result['result']:
                print(f"  - {result['endpoint']}")
    else:
        print("✅ All balance routes appear to be registered")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backend_route_diagnostic_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'registered': registered,
                'not_found': not_found,
                'errors': errors
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {filename}")

if __name__ == "__main__":
    test_route_registration() 