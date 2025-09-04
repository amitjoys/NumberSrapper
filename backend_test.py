#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Realtime Webscraper
Tests all API endpoints and WebSocket functionality
"""

import requests
import sys
import json
import time
import asyncio
import websockets
import threading
from datetime import datetime
from io import StringIO
import pandas as pd

class WebScraperAPITester:
    def __init__(self, base_url="https://contact-fetch-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.ws_url = base_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws'
        self.tests_run = 0
        self.tests_passed = 0
        self.ws_messages = []
        self.ws_connected = False

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def run_api_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if success:
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        details += f", Response keys: {list(response_data.keys())}"
                except:
                    details += ", Response: Non-JSON"
            else:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            return self.log_test(name, success, details), response.json() if success else {}

        except Exception as e:
            return self.log_test(name, False, f"Exception: {str(e)}"), {}

    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        print(f"\n🔍 Testing WebSocket Connection...")
        print(f"   WS URL: {self.ws_url}")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                self.ws_connected = True
                
                # Send a test message
                await websocket.send("test connection")
                
                # Wait for any response (optional)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    self.ws_messages.append(response)
                except asyncio.TimeoutError:
                    pass  # No response expected for test message
                
                return self.log_test("WebSocket Connection", True, "Connected successfully")
                
        except Exception as e:
            return self.log_test("WebSocket Connection", False, f"Exception: {str(e)}")

    def create_test_csv(self):
        """Create a test CSV file for bulk upload"""
        test_data = {
            'url': [
                'https://example.com',
                'https://github.com',
                'https://stackoverflow.com'
            ]
        }
        df = pd.DataFrame(test_data)
        csv_content = df.to_csv(index=False)
        return csv_content

    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("\n" + "="*60)
        print("PHASE 1: BASIC API ENDPOINT TESTING")
        print("="*60)
        
        # Test root endpoint
        self.run_api_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        
        # Test CSV template download
        success, response = self.run_api_test(
            "CSV Template Download",
            "GET", 
            "scrape/template",
            200
        )

    def test_scraping_endpoints(self):
        """Test scraping functionality"""
        print("\n" + "="*60)
        print("PHASE 2: SCRAPING ENDPOINT TESTING")
        print("="*60)
        
        # Test single URL scraping
        single_url_data = {
            "url": "https://example.com",
            "max_threads": 1
        }
        
        success, response = self.run_api_test(
            "Single URL Scraping",
            "POST",
            "scrape/single",
            200,
            data=single_url_data
        )
        
        job_id = None
        if success and 'job_id' in response:
            job_id = response['job_id']
            print(f"   Job ID: {job_id}")
            
            # Wait a moment for job to start
            time.sleep(2)
            
            # Test job status endpoint
            self.run_api_test(
                "Job Status Check",
                "GET",
                f"scrape/job/{job_id}",
                200
            )
            
            # Test job results endpoint
            self.run_api_test(
                "Job Results Check",
                "GET",
                f"scrape/results/{job_id}",
                200
            )
        
        # Test bulk CSV upload
        csv_content = self.create_test_csv()
        files = {'file': ('test_urls.csv', csv_content, 'text/csv')}
        form_data = {'max_threads': '2'}
        
        success, response = self.run_api_test(
            "Bulk CSV Upload",
            "POST",
            "scrape/bulk",
            200,
            data=form_data,
            files=files
        )
        
        bulk_job_id = None
        if success and 'job_id' in response:
            bulk_job_id = response['job_id']
            print(f"   Bulk Job ID: {bulk_job_id}")
        
        return job_id, bulk_job_id

    def test_download_endpoints(self, job_id):
        """Test download functionality"""
        print("\n" + "="*60)
        print("PHASE 3: DOWNLOAD ENDPOINT TESTING")
        print("="*60)
        
        if job_id:
            # Wait for some processing time
            print("   Waiting 10 seconds for scraping to process...")
            time.sleep(10)
            
            # Test results download
            url = f"{self.api_url}/scrape/download/{job_id}"
            print(f"\n🔍 Testing Results Download...")
            print(f"   URL: {url}")
            
            try:
                response = requests.get(url, timeout=30)
                success = response.status_code == 200
                
                if success:
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    details = f"Status: {response.status_code}, Type: {content_type}, Size: {content_length} bytes"
                else:
                    details = f"Status: {response.status_code}, Expected: 200"
                
                self.log_test("Results Download", success, details)
                
            except Exception as e:
                self.log_test("Results Download", False, f"Exception: {str(e)}")

    async def run_websocket_tests(self):
        """Run WebSocket tests"""
        print("\n" + "="*60)
        print("PHASE 4: WEBSOCKET TESTING")
        print("="*60)
        
        await self.test_websocket_connection()

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n" + "="*60)
        print("PHASE 5: ERROR HANDLING TESTING")
        print("="*60)
        
        # Test invalid URL
        invalid_url_data = {
            "url": "not-a-valid-url",
            "max_threads": 1
        }
        
        success, response = self.run_api_test(
            "Invalid URL Handling",
            "POST",
            "scrape/single",
            200,  # API should return 200 but with error status
            data=invalid_url_data
        )
        
        # Test invalid CSV upload
        invalid_files = {'file': ('test.txt', 'not a csv file', 'text/plain')}
        form_data = {'max_threads': '2'}
        
        self.run_api_test(
            "Invalid File Upload",
            "POST",
            "scrape/bulk",
            200,  # API should return 200 but with error status
            data=form_data,
            files=invalid_files
        )
        
        # Test non-existent job ID
        self.run_api_test(
            "Non-existent Job Status",
            "GET",
            "scrape/job/non-existent-job-id",
            200  # API returns 200 with error message
        )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.ws_connected:
            print(f"🔌 WebSocket: Connected")
        else:
            print(f"🔌 WebSocket: Failed to connect")
        
        print(f"🌐 Backend URL: {self.base_url}")
        print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.tests_passed == self.tests_run

async def main():
    """Main test execution"""
    print("🚀 Starting Realtime Webscraper Backend API Tests")
    print("="*60)
    
    tester = WebScraperAPITester()
    
    # Run synchronous tests
    tester.test_basic_endpoints()
    job_id, bulk_job_id = tester.test_scraping_endpoints()
    tester.test_download_endpoints(job_id)
    tester.test_error_handling()
    
    # Run WebSocket tests
    await tester.run_websocket_tests()
    
    # Print summary and return result
    all_passed = tester.print_summary()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)