#!/usr/bin/env python3
"""
Simple test script to demonstrate AutoAgentHire API functionality
"""

import asyncio
import requests
import time
import json
from typing import Dict, Any

API_BASE = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ Health check: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✅ Root endpoint: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_job_search():
    """Test job search functionality"""
    try:
        search_data = {
            "keywords": "Python Developer",
            "location": "San Francisco, CA",
            "experience_level": "mid",
            "limit": 5
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/jobs/search",
            json=search_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Job search successful: Found {result.get('total_count', 0)} jobs")
            
            # Print first job details
            if result.get('jobs'):
                first_job = result['jobs'][0]
                print(f"   First job: {first_job['title']} at {first_job['company']}")
            
            return True
        else:
            print(f"❌ Job search failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Job search failed: {e}")
        return False

def test_job_matching():
    """Test job matching functionality"""
    try:
        search_data = {
            "keywords": "Software Engineer",
            "location": "Remote",
            "limit": 3
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/jobs/match",
            json=search_data
        )
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Job matching successful: Found {len(jobs)} matched jobs")
            
            # Print match scores
            for i, job in enumerate(jobs[:2]):
                score = job.get('match_score', 'N/A')
                print(f"   Job {i+1}: {job['title']} (Score: {score})")
            
            return True
        else:
            print(f"❌ Job matching failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Job matching failed: {e}")
        return False

def test_application_status():
    """Test application status endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/jobs/applications/status")
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Application status: {status}")
            return True
        else:
            print(f"❌ Application status failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Application status failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing AutoAgentHire API...")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("Job Search", test_job_search),
        ("Job Matching", test_job_matching),
        ("Application Status", test_application_status)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AutoAgentHire API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
    
    return passed == total

if __name__ == "__main__":
    main()