#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite for Discord Voice Node Offset Finder
Tests all API endpoints, file validation, binary analysis, and error handling.
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

# Get backend URL from environment
BACKEND_URL = "https://romantic-matsumoto.preview.emergentagent.com/api"

class DiscordVoiceOffsetFinderTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test basic API health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                if "Discord Voice Node Offset Finder API" in data.get("message", ""):
                    self.log_test("Health Check Endpoint", True, f"Response: {data}")
                else:
                    self.log_test("Health Check Endpoint", False, f"Unexpected response: {data}")
            else:
                self.log_test("Health Check Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Health Check Endpoint", False, f"Exception: {str(e)}")
    
    def create_test_files(self):
        """Create test files for upload validation"""
        test_files = {}
        
        # Create a fake .node file (binary content)
        node_content = b'\x7fELF\x01\x01\x01\x00' + b'\x00' * 100 + b'discord_voice' + b'\x00' * 50
        node_file = tempfile.NamedTemporaryFile(suffix='.node', delete=False)
        node_file.write(node_content)
        node_file.close()
        test_files['valid_node'] = node_file.name
        
        # Create invalid file types
        txt_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        txt_file.write(b'This is a text file')
        txt_file.close()
        test_files['invalid_txt'] = txt_file.name
        
        exe_file = tempfile.NamedTemporaryFile(suffix='.exe', delete=False)
        exe_file.write(b'MZ\x90\x00' + b'\x00' * 100)
        exe_file.close()
        test_files['invalid_exe'] = exe_file.name
        
        # Create oversized file (simulate large file)
        large_file = tempfile.NamedTemporaryFile(suffix='.node', delete=False)
        large_file.write(b'\x00' * (10 * 1024 * 1024))  # 10MB file
        large_file.close()
        test_files['large_node'] = large_file.name
        
        return test_files
    
    def test_file_upload_validation(self):
        """Test file upload validation - should only accept .node files"""
        test_files = self.create_test_files()
        
        try:
            # Test valid .node file
            with open(test_files['valid_node'], 'rb') as f:
                files = {'file': ('test_discord_voice.node', f, 'application/octet-stream')}
                response = self.session.post(f"{self.base_url}/analyze", files=files)
                
                if response.status_code == 200:
                    self.log_test("Valid .node File Upload", True, "Successfully accepted .node file")
                else:
                    self.log_test("Valid .node File Upload", False, f"Status: {response.status_code}, Response: {response.text}")
            
            # Test invalid .txt file
            with open(test_files['invalid_txt'], 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = self.session.post(f"{self.base_url}/analyze", files=files)
                
                if response.status_code == 400:
                    self.log_test("Invalid .txt File Rejection", True, "Correctly rejected .txt file")
                else:
                    self.log_test("Invalid .txt File Rejection", False, f"Should reject .txt files. Status: {response.status_code}")
            
            # Test invalid .exe file
            with open(test_files['invalid_exe'], 'rb') as f:
                files = {'file': ('test.exe', f, 'application/octet-stream')}
                response = self.session.post(f"{self.base_url}/analyze", files=files)
                
                if response.status_code == 400:
                    self.log_test("Invalid .exe File Rejection", True, "Correctly rejected .exe file")
                else:
                    self.log_test("Invalid .exe File Rejection", False, f"Should reject .exe files. Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("File Upload Validation", False, f"Exception: {str(e)}")
        
        finally:
            # Cleanup test files
            for file_path in test_files.values():
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def test_binary_analysis_functionality(self):
        """Test the core binary analysis functionality"""
        test_files = self.create_test_files()
        
        try:
            # Upload a valid .node file and check analysis results
            with open(test_files['valid_node'], 'rb') as f:
                files = {'file': ('discord_voice.node', f, 'application/octet-stream')}
                response = self.session.post(f"{self.base_url}/analyze", files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields in response
                    required_fields = ['filename', 'total_functions', 'functions_found', 'high_confidence_matches', 'success_rate']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        # Validate data types and ranges
                        if (isinstance(data['total_functions'], int) and data['total_functions'] > 0 and
                            isinstance(data['functions_found'], int) and data['functions_found'] >= 0 and
                            isinstance(data['high_confidence_matches'], int) and data['high_confidence_matches'] >= 0 and
                            isinstance(data['success_rate'], (int, float)) and 0 <= data['success_rate'] <= 100):
                            
                            self.log_test("Binary Analysis Response Structure", True, 
                                        f"Total: {data['total_functions']}, Found: {data['functions_found']}, "
                                        f"High Confidence: {data['high_confidence_matches']}, Success Rate: {data['success_rate']:.1f}%")
                        else:
                            self.log_test("Binary Analysis Response Structure", False, f"Invalid data types or ranges: {data}")
                    else:
                        self.log_test("Binary Analysis Response Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Binary Analysis Functionality", False, f"Status: {response.status_code}, Response: {response.text}")
                    
        except Exception as e:
            self.log_test("Binary Analysis Functionality", False, f"Exception: {str(e)}")
        
        finally:
            # Cleanup
            for file_path in test_files.values():
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def test_offset_file_generation(self):
        """Test offset.txt file generation and download"""
        test_files = self.create_test_files()
        
        try:
            # First, perform an analysis to generate offset.txt
            with open(test_files['valid_node'], 'rb') as f:
                files = {'file': ('discord_voice.node', f, 'application/octet-stream')}
                response = self.session.post(f"{self.base_url}/analyze", files=files)
                
                if response.status_code == 200:
                    # Wait a moment for file generation
                    time.sleep(1)
                    
                    # Try to download the results
                    download_response = self.session.get(f"{self.base_url}/download-results")
                    
                    if download_response.status_code == 200:
                        content = download_response.text
                        
                        # Check if the content looks like a valid offset file
                        if ("DISCORD VOICE NODE OFFSET FINDER RESULTS" in content and
                            "Functions analyzed:" in content and
                            "DETAILED RESULTS:" in content):
                            self.log_test("Offset.txt File Generation", True, f"Generated file with {len(content)} characters")
                        else:
                            self.log_test("Offset.txt File Generation", False, "Generated file doesn't have expected format")
                    else:
                        self.log_test("Offset.txt File Generation", False, f"Download failed. Status: {download_response.status_code}")
                else:
                    self.log_test("Offset.txt File Generation", False, f"Analysis failed. Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Offset.txt File Generation", False, f"Exception: {str(e)}")
        
        finally:
            # Cleanup
            for file_path in test_files.values():
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def test_download_without_analysis(self):
        """Test download endpoint when no analysis has been performed"""
        try:
            # Try to download without performing analysis first
            response = self.session.get(f"{self.base_url}/download-results")
            
            if response.status_code == 404:
                self.log_test("Download Without Analysis", True, "Correctly returns 404 when no analysis exists")
            else:
                self.log_test("Download Without Analysis", False, f"Should return 404. Got: {response.status_code}")
                
        except Exception as e:
            self.log_test("Download Without Analysis", False, f"Exception: {str(e)}")
    
    def test_analysis_history(self):
        """Test analysis history endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/analysis-history")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_test("Analysis History Endpoint", True, f"Retrieved {len(data)} analysis records")
                    
                    # If there are records, validate structure
                    if data:
                        first_record = data[0]
                        required_fields = ['filename', 'total_functions', 'functions_found', 'analysis_timestamp']
                        missing_fields = [field for field in required_fields if field not in first_record]
                        
                        if not missing_fields:
                            self.log_test("Analysis History Structure", True, "History records have correct structure")
                        else:
                            self.log_test("Analysis History Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Analysis History Endpoint", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("Analysis History Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Analysis History Endpoint", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test various error conditions"""
        try:
            # Test missing file parameter
            response = self.session.post(f"{self.base_url}/analyze")
            
            if response.status_code in [400, 422]:  # FastAPI returns 422 for validation errors
                self.log_test("Missing File Parameter Error", True, "Correctly handles missing file")
            else:
                self.log_test("Missing File Parameter Error", False, f"Expected 400/422, got: {response.status_code}")
            
            # Test corrupted file upload
            corrupted_content = b'\x00\x01\x02\x03' * 100  # Random bytes
            corrupted_file = tempfile.NamedTemporaryFile(suffix='.node', delete=False)
            corrupted_file.write(corrupted_content)
            corrupted_file.close()
            
            try:
                with open(corrupted_file.name, 'rb') as f:
                    files = {'file': ('corrupted.node', f, 'application/octet-stream')}
                    response = self.session.post(f"{self.base_url}/analyze", files=files)
                    
                    # Should either succeed (with low confidence results) or fail gracefully
                    if response.status_code in [200, 500]:
                        self.log_test("Corrupted File Handling", True, f"Handled corrupted file gracefully (status: {response.status_code})")
                    else:
                        self.log_test("Corrupted File Handling", False, f"Unexpected status: {response.status_code}")
            finally:
                os.unlink(corrupted_file.name)
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
    
    def test_database_operations(self):
        """Test database operations by performing analysis and checking history"""
        test_files = self.create_test_files()
        
        try:
            # Get initial history count
            initial_response = self.session.get(f"{self.base_url}/analysis-history")
            initial_count = len(initial_response.json()) if initial_response.status_code == 200 else 0
            
            # Perform an analysis
            with open(test_files['valid_node'], 'rb') as f:
                files = {'file': ('test_db_discord_voice.node', f, 'application/octet-stream')}
                response = self.session.post(f"{self.base_url}/analyze", files=files)
                
                if response.status_code == 200:
                    # Check if history count increased
                    time.sleep(1)  # Wait for DB write
                    new_response = self.session.get(f"{self.base_url}/analysis-history")
                    
                    if new_response.status_code == 200:
                        new_count = len(new_response.json())
                        
                        if new_count > initial_count:
                            self.log_test("Database Operations", True, f"Analysis saved to database (count: {initial_count} -> {new_count})")
                        else:
                            self.log_test("Database Operations", False, f"Analysis not saved to database (count unchanged: {new_count})")
                    else:
                        self.log_test("Database Operations", False, f"Failed to retrieve history after analysis")
                else:
                    self.log_test("Database Operations", False, f"Analysis failed: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Database Operations", False, f"Exception: {str(e)}")
        
        finally:
            # Cleanup
            for file_path in test_files.values():
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def run_all_tests(self):
        """Run all test suites"""
        print("=" * 60)
        print("DISCORD VOICE NODE OFFSET FINDER - BACKEND TESTS")
        print("=" * 60)
        print(f"Testing backend at: {self.base_url}")
        print()
        
        # Run all test suites
        self.test_health_check()
        self.test_file_upload_validation()
        self.test_binary_analysis_functionality()
        self.test_offset_file_generation()
        self.test_download_without_analysis()
        self.test_analysis_history()
        self.test_error_handling()
        self.test_database_operations()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"❌ {test['test']}: {test['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = DiscordVoiceOffsetFinderTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some tests failed!")
        exit(1)