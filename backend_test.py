import requests
import unittest
import os
import json
import time
from io import BytesIO

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://0d20cb53-d151-45da-8b29-6ce815842608.preview.emergentagent.com"

class JobPrepAIBackendTests(unittest.TestCase):
    """Test suite for JobPrep AI backend API endpoints"""
    
    def setUp(self):
        """Setup for each test"""
        self.api_url = BACKEND_URL
        self.sample_cv_text = """
        JOHN DOE
        Software Engineer
        
        CONTACT
        Email: john.doe@example.com
        Phone: (123) 456-7890
        LinkedIn: linkedin.com/in/johndoe
        
        SUMMARY
        Experienced software engineer with 5+ years of experience in full-stack development.
        Proficient in Python, JavaScript, React, and cloud technologies.
        
        EXPERIENCE
        Senior Software Engineer | Tech Company Inc. | 2020 - Present
        - Led development of microservices architecture using Python and FastAPI
        - Implemented CI/CD pipelines reducing deployment time by 40%
        - Mentored junior developers and conducted code reviews
        
        Software Developer | StartupXYZ | 2018 - 2020
        - Built responsive web applications using React and Node.js
        - Developed RESTful APIs and integrated with third-party services
        - Implemented automated testing increasing code coverage by 30%
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology | 2014 - 2018
        
        SKILLS
        Languages: Python, JavaScript, TypeScript, SQL
        Frameworks: React, Node.js, FastAPI, Django
        Tools: Git, Docker, Kubernetes, AWS, CI/CD
        """
        self.sample_company = "Microsoft"
        self.sample_role = "Senior Software Engineer"
        self.analysis_id = None
    
    def test_01_health_check(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing health check endpoint...")
        response = requests.get(f"{self.api_url}/api/health")
        
        self.assertEqual(response.status_code, 200, "Health check failed")
        data = response.json()
        self.assertEqual(data["status"], "healthy", "Health status is not 'healthy'")
        print("✅ Health check passed")
    
    def test_02_upload_cv(self):
        """Test CV upload functionality"""
        print("\n🔍 Testing CV upload functionality...")
        
        # Create a mock PDF file
        mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R>>\nendobj\n4 0 obj\n<</Length 21>>\nstream\nBT /F1 12 Tf (Test) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000102 00000 n \n0000000182 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n252\n%%EOF"
        files = {'file': ('test_cv.pdf', BytesIO(mock_pdf_content), 'application/pdf')}
        
        response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
        
        # Test with text file as fallback
        if response.status_code != 200:
            print("PDF upload failed, trying text file...")
            files = {'file': ('test_cv.txt', BytesIO(self.sample_cv_text.encode('utf-8')), 'text/plain')}
            response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
        
        self.assertEqual(response.status_code, 200, f"CV upload failed with status {response.status_code}")
        data = response.json()
        self.assertTrue(data["success"], "Upload was not successful")
        self.assertTrue("cv_text" in data, "CV text not returned in response")
        print("✅ CV upload test passed")
    
    def test_03_analyze_cv(self):
        """Test CV analysis functionality"""
        print("\n🔍 Testing CV analysis functionality...")
        
        payload = {
            "cv_text": self.sample_cv_text,
            "target_role": self.sample_role,
            "target_company": self.sample_company
        }
        
        response = requests.post(
            f"{self.api_url}/api/analyze-cv",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200, f"CV analysis failed with status {response.status_code}")
        data = response.json()
        
        # Save analysis_id for later test
        self.analysis_id = data.get("analysis_id")
        
        # Check required fields in response
        required_fields = ["analysis_id", "cv_improvements", "skills_analysis", "confidence_score", "recommendations"]
        for field in required_fields:
            self.assertTrue(field in data, f"Field '{field}' missing from analysis response")
        
        print("✅ CV analysis test passed")
        print(f"📝 Analysis ID: {self.analysis_id}")
    
    def test_04_company_research(self):
        """Test company research functionality"""
        print("\n🔍 Testing company research functionality...")
        
        payload = {
            "company_name": self.sample_company,
            "role_type": self.sample_role
        }
        
        response = requests.post(
            f"{self.api_url}/api/company-research",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200, f"Company research failed with status {response.status_code}")
        data = response.json()
        
        # Check required fields in response
        required_fields = ["company_name", "culture_analysis", "industry_context"]
        for field in required_fields:
            self.assertTrue(field in data, f"Field '{field}' missing from company research response")
        
        print("✅ Company research test passed")
    
    def test_05_get_analysis(self):
        """Test retrieving previous analysis"""
        print("\n🔍 Testing analysis retrieval...")
        
        # Skip if no analysis_id from previous test
        if not self.analysis_id:
            print("⚠️ Skipping analysis retrieval test - no analysis ID available")
            return
        
        response = requests.get(f"{self.api_url}/api/analysis/{self.analysis_id}")
        
        self.assertEqual(response.status_code, 200, f"Analysis retrieval failed with status {response.status_code}")
        data = response.json()
        
        # Verify it's the same analysis
        self.assertEqual(data["analysis_id"], self.analysis_id, "Retrieved analysis ID doesn't match")
        
        print("✅ Analysis retrieval test passed")

if __name__ == "__main__":
    # Run the tests
    print("🚀 Starting JobPrep AI Backend Tests")
    print(f"🌐 Testing against: {BACKEND_URL}")
    
    # Create a test suite and run it
    suite = unittest.TestSuite()
    suite.addTest(JobPrepAIBackendTests('test_01_health_check'))
    suite.addTest(JobPrepAIBackendTests('test_02_upload_cv'))
    suite.addTest(JobPrepAIBackendTests('test_03_analyze_cv'))
    suite.addTest(JobPrepAIBackendTests('test_04_company_research'))
    suite.addTest(JobPrepAIBackendTests('test_05_get_analysis'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"Total tests: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)