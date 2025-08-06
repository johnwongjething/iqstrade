#!/usr/bin/env python3
"""
Geetest Cloudflare Blocking Report Generator
Generate a detailed report for Geetest support about Cloudflare blocking
"""
import requests
import json
import socket
from datetime import datetime

def get_server_info():
    """Get server information"""
    print("🔍 Collecting Server Information...")
    
    try:
        # Get public IP
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        public_ip = response.json()['ip']
    except:
        public_ip = "Could not determine"
    
    try:
        # Get hostname
        hostname = socket.gethostname()
    except:
        hostname = "Unknown"
    
    return {
        'public_ip': public_ip,
        'hostname': hostname,
        'timestamp': datetime.now().isoformat()
    }

def test_geetest_endpoints():
    """Test all Geetest endpoints"""
    print("\n🔍 Testing Geetest Endpoints...")
    
    geetest_id = "892f5d0ac8e4a9746a87e8e35866b6be"  # Your ID
    
    endpoints = [
        "https://gcaptcha4.geetest.com/register",
        "https://api.geetest.com/register", 
        "https://gcaptcha4.geetest.com/api/register",
        "https://gcaptcha4.geetest.com/validate"
    ]
    
    results = {}
    
    for url in endpoints:
        print(f"\n📡 Testing: {url}")
        
        try:
            if "validate" in url:
                # Test validation endpoint
                payload = {
                    "lot_number": "test",
                    "captcha_output": "test",
                    "pass_token": "test", 
                    "captcha_id": geetest_id
                }
                response = requests.post(url, json=payload, timeout=10)
            else:
                # Test registration endpoint
                params = {
                    "captcha_id": geetest_id,
                    "client_type": "web",
                    "lang": "en"
                }
                response = requests.get(url, params=params, timeout=10)
            
            results[url] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_length': len(response.content),
                'is_html': response.headers.get('content-type', '').startswith('text/html'),
                'is_json': response.headers.get('content-type', '').startswith('application/json')
            }
            
            if response.status_code == 200:
                if results[url]['is_json']:
                    try:
                        data = response.json()
                        results[url]['response_data'] = data
                        print(f"✅ 200 OK - JSON Response")
                    except:
                        results[url]['response_data'] = "Invalid JSON"
                        print(f"⚠️ 200 OK - Invalid JSON")
                else:
                    results[url]['response_data'] = "HTML Response"
                    print(f"⚠️ 200 OK - HTML Response")
            elif response.status_code == 403:
                results[url]['response_data'] = "Cloudflare Blocking"
                print(f"❌ 403 Forbidden - Cloudflare Blocking")
            else:
                results[url]['response_data'] = response.text[:200] + "..." if len(response.text) > 200 else response.text
                print(f"❌ {response.status_code} - Error")
                
        except Exception as e:
            results[url] = {
                'error': str(e),
                'status_code': None
            }
            print(f"❌ Exception: {e}")
    
    return results

def generate_report():
    """Generate the complete report"""
    print("=" * 80)
    print("Geetest Cloudflare Blocking Report")
    print("=" * 80)
    
    # Collect information
    server_info = get_server_info()
    endpoint_results = test_geetest_endpoints()
    
    # Generate report
    report = {
        'report_generated': datetime.now().isoformat(),
        'server_info': server_info,
        'endpoint_tests': endpoint_results,
        'summary': {
            'cloudflare_blocked': False,
            'working_endpoints': [],
            'blocked_endpoints': []
        }
    }
    
    # Analyze results
    for url, result in endpoint_results.items():
        if result.get('status_code') == 403:
            report['summary']['cloudflare_blocked'] = True
            report['summary']['blocked_endpoints'].append(url)
        elif result.get('status_code') == 200 and result.get('is_json'):
            report['summary']['working_endpoints'].append(url)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Server IP: {server_info['public_ip']}")
    print(f"Hostname: {server_info['hostname']}")
    print(f"Cloudflare Blocking Detected: {'Yes' if report['summary']['cloudflare_blocked'] else 'No'}")
    print(f"Working Endpoints: {len(report['summary']['working_endpoints'])}")
    print(f"Blocked Endpoints: {len(report['summary']['blocked_endpoints'])}")
    
    if report['summary']['cloudflare_blocked']:
        print("\n🚨 CLOUDFLARE BLOCKING DETECTED")
        print("=" * 50)
        print("Your server IP appears to be blocked by Cloudflare.")
        print("Please contact Geetest support with this information:")
        print(f"   - Server IP: {server_info['public_ip']}")
        print(f"   - Timestamp: {server_info['timestamp']}")
        print(f"   - Blocked endpoints: {', '.join(report['summary']['blocked_endpoints'])}")
        print("\n💡 Include this report in your support ticket.")
    
    # Save report
    filename = f"geetest_cloudflare_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {filename}")
    print("📧 Send this file to Geetest support along with your ticket.")
    
    return report

if __name__ == "__main__":
    generate_report() 