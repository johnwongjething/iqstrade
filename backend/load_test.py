#!/usr/bin/env python3
"""
Simple Load Testing Script for 100 Concurrent Users
Tests your system's performance under load
"""

import requests
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from datetime import datetime

class LoadTester:
    """Simple load tester for concurrent user simulation"""
    
    def __init__(self, base_url, max_workers=100):
        self.base_url = base_url.rstrip('/')
        self.max_workers = max_workers
        self.results = []
        self.lock = threading.Lock()
        
    def make_request(self, endpoint, method='GET', data=None, headers=None):
        """Make a single request and record timing"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            duration = time.time() - start_time
            
            result = {
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'duration': duration,
                'success': response.status_code < 400,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                'url': url,
                'method': method,
                'status_code': None,
                'duration': duration,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        with self.lock:
            self.results.append(result)
        
        return result
    
    def test_endpoint(self, endpoint, method='GET', data=None, headers=None, num_requests=100):
        """Test an endpoint with multiple concurrent requests"""
        print(f"Testing {endpoint} with {num_requests} concurrent requests...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(self.make_request, endpoint, method, data, headers)
                futures.append(future)
            
            # Wait for all requests to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Request failed: {e}")
        
        return self.analyze_results()
    
    def analyze_results(self):
        """Analyze the test results"""
        if not self.results:
            return {}
        
        durations = [r['duration'] for r in self.results]
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        status_codes = {}
        for result in self.results:
            status = result.get('status_code', 'error')
            status_codes[status] = status_codes.get(status, 0) + 1
        
        analysis = {
            'total_requests': len(self.results),
            'successful_requests': len(successful),
            'failed_requests': len(failed),
            'success_rate': (len(successful) / len(self.results)) * 100,
            'avg_response_time': statistics.mean(durations),
            'min_response_time': min(durations),
            'max_response_time': max(durations),
            'median_response_time': statistics.median(durations),
            'status_codes': status_codes,
            'slow_requests': len([d for d in durations if d > 5.0]),  # > 5 seconds
            'very_slow_requests': len([d for d in durations if d > 10.0]),  # > 10 seconds
        }
        
        return analysis
    
    def print_summary(self, analysis):
        """Print a summary of the test results"""
        print("\n" + "="*60)
        print("LOAD TEST SUMMARY")
        print("="*60)
        print(f"Total Requests: {analysis['total_requests']}")
        print(f"Successful: {analysis['successful_requests']}")
        print(f"Failed: {analysis['failed_requests']}")
        print(f"Success Rate: {analysis['success_rate']:.1f}%")
        print(f"Average Response Time: {analysis['avg_response_time']:.3f}s")
        print(f"Median Response Time: {analysis['median_response_time']:.3f}s")
        print(f"Min Response Time: {analysis['min_response_time']:.3f}s")
        print(f"Max Response Time: {analysis['max_response_time']:.3f}s")
        print(f"Slow Requests (>5s): {analysis['slow_requests']}")
        print(f"Very Slow Requests (>10s): {analysis['very_slow_requests']}")
        print(f"Status Codes: {analysis['status_codes']}")
        print("="*60)
        
        # Performance assessment
        if analysis['success_rate'] >= 95 and analysis['avg_response_time'] < 2.0:
            print("✅ EXCELLENT: System handles load well!")
        elif analysis['success_rate'] >= 90 and analysis['avg_response_time'] < 5.0:
            print("⚠️ GOOD: System performs adequately but could be optimized")
        else:
            print("❌ NEEDS IMPROVEMENT: System struggles under load")
    
    def save_results(self, filename=None):
        """Save test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'summary': self.analyze_results(),
                'detailed_results': self.results
            }, f, indent=2)
        
        print(f"Results saved to: {filename}")

def main():
    """Main load testing function"""
    print("🚀 LOAD TESTING FOR 100 CONCURRENT USERS")
    print("="*60)
    
    # Configuration
    base_url = input("Enter your app URL (e.g., https://iqstrade.onrender.com): ").strip()
    if not base_url:
        base_url = "https://iqstrade.onrender.com"
    
    print(f"\nTesting URL: {base_url}")
    
    # Create load tester
    tester = LoadTester(base_url, max_workers=100)
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Homepage Load',
            'endpoint': '/',
            'method': 'GET',
            'requests': 50
        },
        {
            'name': 'API Health Check',
            'endpoint': '/api/ping',
            'method': 'GET',
            'requests': 100
        },
        {
            'name': 'Performance Stats',
            'endpoint': '/api/performance/stats',
            'method': 'GET',
            'requests': 50
        },
        {
            'name': 'Bills List (if authenticated)',
            'endpoint': '/api/bills',
            'method': 'GET',
            'requests': 30
        }
    ]
    
    print("\nRunning test scenarios...")
    
    for scenario in test_scenarios:
        print(f"\n📊 {scenario['name']}")
        print("-" * 40)
        
        analysis = tester.test_endpoint(
            endpoint=scenario['endpoint'],
            method=scenario['method'],
            num_requests=scenario['requests']
        )
        
        tester.print_summary(analysis)
        
        # Wait between tests
        time.sleep(2)
    
    # Overall summary
    print("\n🎯 OVERALL PERFORMANCE ASSESSMENT")
    print("="*60)
    
    overall_analysis = tester.analyze_results()
    tester.print_summary(overall_analysis)
    
    # Save results
    tester.save_results()
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if overall_analysis['success_rate'] < 95:
        print("- Investigate failed requests")
        print("- Check database connection pooling")
        print("- Review server logs for errors")
    
    if overall_analysis['avg_response_time'] > 2.0:
        print("- Optimize database queries")
        print("- Add missing indexes")
        print("- Consider caching strategies")
    
    if overall_analysis['slow_requests'] > 0:
        print("- Monitor slow queries")
        print("- Optimize heavy operations")
        print("- Consider async processing")

if __name__ == "__main__":
    main() 