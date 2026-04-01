#!/usr/bin/env python3
"""
Comprehensive Customer Balance System Test Script
Tests all components: Frontend, Backend, Database, and API endpoints
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "https://iqstrade.onrender.com"
API_BASE_URL = f"{BASE_URL}/api"

# Test credentials
TEST_USERNAME = "ray40"
TEST_PASSWORD = "Raysan11!!"

class CustomerBalanceTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "timestamp": timestamp,
            "test": test_name,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{timestamp}] {test_name}: {status}")
        if details:
            print(f"  Details: {details}")
        print()

    def test_1_frontend_accessibility(self):
        """Test 1: Check if frontend pages are accessible"""
        try:
            # Test main page
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                self.log_test("Frontend Main Page", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Frontend Main Page", "FAIL", f"Status: {response.status_code}")
            
            # Test dashboard page
            response = self.session.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                self.log_test("Frontend Dashboard Page", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Frontend Dashboard Page", "FAIL", f"Status: {response.status_code}")
                
            # Test customer balance page
            response = self.session.get(f"{BASE_URL}/simple-new-staff-stats")
            if response.status_code == 200:
                self.log_test("Frontend Customer Balance Page", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Frontend Customer Balance Page", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Frontend Accessibility", "ERROR", str(e))

    def test_2_authentication(self):
        """Test 2: Test user authentication"""
        try:
            # Get CSRF token first
            csrf_response = self.session.get(f"{API_BASE_URL}/csrf-token")
            if csrf_response.status_code != 200:
                self.log_test("CSRF Token", "FAIL", f"Status: {csrf_response.status_code}")
                return False
            
            csrf_data = csrf_response.json()
            csrf_token = csrf_data.get('csrf_token')
            
            # Login
            login_data = {
                'username': TEST_USERNAME,
                'password': TEST_PASSWORD,
                'captcha_id': 'test_captcha',
                'lot_number': 'test_lot',
                'pass_token': 'test_token',
                'gen_time': '1234567890',
                'captcha_output': 'test_output'
            }
            
            headers = {'X-CSRFToken': csrf_token}
            response = self.session.post(f"{API_BASE_URL}/login", json=login_data, headers=headers)
            
            if response.status_code == 200:
                login_result = response.json()
                if login_result.get('status') == 'success':
                    self.log_test("User Authentication", "PASS", f"Logged in as {TEST_USERNAME}")
                    return True
                else:
                    self.log_test("User Authentication", "FAIL", f"Login failed: {login_result}")
                    return False
            else:
                self.log_test("User Authentication", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", "ERROR", str(e))
            return False

    def test_3_api_endpoints_existence(self):
        """Test 3: Check if API endpoints exist"""
        endpoints_to_test = [
            "/api/balance/search",
            "/api/balance/ray40",
            "/api/balance/ray40/history",
            "/api/balance/ray40/adjust",
            "/api/balance/all"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                # We expect 401 (unauthorized) or 400 (bad request), but not 404 (not found)
                if response.status_code == 404:
                    self.log_test(f"API Endpoint {endpoint}", "FAIL", f"Endpoint not found (404)")
                elif response.status_code in [401, 400, 405]:
                    self.log_test(f"API Endpoint {endpoint}", "PASS", f"Endpoint exists (Status: {response.status_code})")
                else:
                    self.log_test(f"API Endpoint {endpoint}", "WARNING", f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"API Endpoint {endpoint}", "ERROR", str(e))

    def test_4_balance_search_with_auth(self):
        """Test 4: Test balance search with authentication"""
        try:
            # Test search with authentication
            response = self.session.get(f"{API_BASE_URL}/balance/search?q=ray40")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    customers = data.get('customers', [])
                    if customers:
                        self.log_test("Balance Search (Authenticated)", "PASS", f"Found {len(customers)} customers")
                    else:
                        self.log_test("Balance Search (Authenticated)", "WARNING", "No customers found")
                else:
                    self.log_test("Balance Search (Authenticated)", "FAIL", f"API error: {data}")
            elif response.status_code == 401:
                self.log_test("Balance Search (Authenticated)", "FAIL", "Authentication required")
            elif response.status_code == 404:
                self.log_test("Balance Search (Authenticated)", "FAIL", "Endpoint not found (404)")
            else:
                self.log_test("Balance Search (Authenticated)", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Balance Search (Authenticated)", "ERROR", str(e))

    def test_5_backend_route_registration(self):
        """Test 5: Check if balance routes are properly registered"""
        try:
            # Test if the app.py imports balance_routes
            # This is a manual check - we'll look for common patterns
            
            # Test if any balance-related endpoints respond
            test_endpoints = [
                "/api/balance/test",
                "/api/balance/",
                "/api/balance"
            ]
            
            for endpoint in test_endpoints:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 404:
                    self.log_test(f"Backend Route {endpoint}", "FAIL", "Route not registered")
                else:
                    self.log_test(f"Backend Route {endpoint}", "PASS", f"Route responds (Status: {response.status_code})")
                    
        except Exception as e:
            self.log_test("Backend Route Registration", "ERROR", str(e))

    def test_6_database_connectivity(self):
        """Test 6: Test database connectivity through API"""
        try:
            # Try to access a simple endpoint that requires database
            response = self.session.get(f"{API_BASE_URL}/me")
            
            if response.status_code == 200:
                data = response.json()
                if 'username' in data:
                    self.log_test("Database Connectivity", "PASS", f"Connected as {data['username']}")
                else:
                    self.log_test("Database Connectivity", "WARNING", "Connected but no user data")
            else:
                self.log_test("Database Connectivity", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Connectivity", "ERROR", str(e))

    def test_7_complete_workflow(self):
        """Test 7: Test complete customer balance workflow"""
        try:
            # 1. Search for customer
            search_response = self.session.get(f"{API_BASE_URL}/balance/search?q=ray40")
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('status') == 'success':
                    customers = search_data.get('customers', [])
                    if customers:
                        customer = customers[0]
                        username = customer.get('username')
                        
                        # 2. Get customer balance
                        balance_response = self.session.get(f"{API_BASE_URL}/balance/{username}")
                        if balance_response.status_code == 200:
                            balance_data = balance_response.json()
                            self.log_test("Complete Workflow", "PASS", f"Search and balance retrieval successful")
                        else:
                            self.log_test("Complete Workflow", "FAIL", f"Balance retrieval failed: {balance_response.status_code}")
                    else:
                        self.log_test("Complete Workflow", "WARNING", "No customers found in search")
                else:
                    self.log_test("Complete Workflow", "FAIL", f"Search failed: {search_data}")
            else:
                self.log_test("Complete Workflow", "FAIL", f"Search failed: {search_response.status_code}")
                
        except Exception as e:
            self.log_test("Complete Workflow", "ERROR", str(e))

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("CUSTOMER BALANCE SYSTEM COMPREHENSIVE TEST")
        print("=" * 60)
        print()
        
        # Run tests
        self.test_1_frontend_accessibility()
        auth_success = self.test_2_authentication()
        self.test_3_api_endpoints_existence()
        
        if auth_success:
            self.test_4_balance_search_with_auth()
            self.test_5_backend_route_registration()
            self.test_6_database_connectivity()
            self.test_7_complete_workflow()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARNING'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Warnings: {warning_tests}")
        print()
        
        # Show failed tests
        failed_results = [r for r in self.test_results if r['status'] in ['FAIL', 'ERROR']]
        if failed_results:
            print("FAILED TESTS:")
            for result in failed_results:
                print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Show warnings
        warning_results = [r for r in self.test_results if r['status'] == 'WARNING']
        if warning_results:
            print("WARNINGS:")
            for result in warning_results:
                print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"customer_balance_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'errors': error_tests,
                    'warnings': warning_tests
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"Detailed results saved to: {filename}")

if __name__ == "__main__":
    tester = CustomerBalanceTester()
    tester.run_all_tests() 