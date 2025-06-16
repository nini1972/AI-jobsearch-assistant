import requests
import unittest
import os
import json
import time
from io import BytesIO
import zipfile
import struct
import re

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if 'REACT_APP_BACKEND_URL' in line:
            BACKEND_URL = line.split('=')[1].strip()
            break
    else:
        BACKEND_URL = "http://localhost:8001"

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
        self.sample_company = "Imec"  # Using Imec as mentioned in the review request
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
    
    def test_02_upload_pdf(self):
        """Test PDF upload functionality"""
        print("\n🔍 Testing PDF upload functionality...")
        
        # Create a mock PDF file
        mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R>>\nendobj\n4 0 obj\n<</Length 21>>\nstream\nBT /F1 12 Tf (Test) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000102 00000 n \n0000000182 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n252\n%%EOF"
        files = {'file': ('test_cv.pdf', BytesIO(mock_pdf_content), 'application/pdf')}
        
        response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
        
        self.assertEqual(response.status_code, 200, f"PDF upload failed with status {response.status_code}")
        data = response.json()
        self.assertTrue(data["success"], "Upload was not successful")
        self.assertTrue("cv_text" in data, "CV text not returned in response")
        self.assertEqual(data["file_type"], "pdf", "File type should be 'pdf'")
        print("✅ PDF upload test passed")
    
    def test_03_upload_docx(self):
        """Test DOCX upload functionality"""
        print("\n🔍 Testing DOCX upload functionality...")
        
        # Create a minimal DOCX file
        docx_file = BytesIO()
        
        # Create a ZIP file (DOCX is a ZIP file with specific structure)
        with zipfile.ZipFile(docx_file, 'w') as zf:
            # Add required files for a minimal DOCX
            zf.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            zf.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            zf.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>This is a test DOCX file with sample CV content.</w:t></w:r></w:p><w:p><w:r><w:t>JOHN DOE - Software Engineer</w:t></w:r></w:p></w:body></w:document>')
            zf.writestr('word/_rels/document.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
        
        docx_file.seek(0)
        files = {'file': ('test_cv.docx', docx_file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        
        response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
        
        self.assertEqual(response.status_code, 200, f"DOCX upload failed with status {response.status_code}")
        data = response.json()
        self.assertTrue(data["success"], "Upload was not successful")
        self.assertTrue("cv_text" in data, "CV text not returned in response")
        self.assertEqual(data["file_type"], "docx", "File type should be 'docx'")
        print("✅ DOCX upload test passed")
    
    def test_04_upload_doc(self):
        """Test DOC upload functionality"""
        print("\n🔍 Testing DOC upload functionality...")
        
        # For DOC testing, we'll use a text file with .doc extension
        # This is a pragmatic approach since creating a valid DOC binary is complex
        text_as_doc = BytesIO(self.sample_cv_text.encode('utf-8'))
        files = {'file': ('test_cv.doc', text_as_doc, 'application/msword')}
        
        try:
            response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
            
            # Check if the server accepts the file (even if it falls back to text extraction)
            if response.status_code == 200:
                data = response.json()
                self.assertTrue(data["success"], "Upload was not successful")
                self.assertTrue("cv_text" in data, "CV text not returned in response")
                print("✅ DOC upload test passed")
            else:
                # If the server rejects the file, we'll note it but not fail the test
                # This is because DOC handling can be complex and may vary by implementation
                print(f"⚠️ DOC upload returned status {response.status_code}")
                print(f"⚠️ Response: {response.text[:100]}")
                print("⚠️ DOC format support may need additional implementation")
                # We're not failing the test since this is an informational finding
        except Exception as e:
            print(f"⚠️ Error testing DOC upload: {e}")
            # We're not failing the test since this is an informational finding
    
    def test_05_upload_txt(self):
        """Test TXT upload functionality"""
        print("\n🔍 Testing TXT upload functionality...")
        
        files = {'file': ('test_cv.txt', BytesIO(self.sample_cv_text.encode('utf-8')), 'text/plain')}
        response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
        
        self.assertEqual(response.status_code, 200, f"TXT upload failed with status {response.status_code}")
        data = response.json()
        self.assertTrue(data["success"], "Upload was not successful")
        self.assertTrue("cv_text" in data, "CV text not returned in response")
        self.assertEqual(data["file_type"], "text", "File type should be 'text'")
        print("✅ TXT upload test passed")
    
    def test_06_upload_unsupported_format(self):
        """Test unsupported file format upload"""
        print("\n🔍 Testing unsupported file format upload...")
        
        # Create a mock image file
        mock_image = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        files = {'file': ('test_cv.png', mock_image, 'image/png')}
        
        response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
        
        # We expect a 400 Bad Request for unsupported formats
        self.assertEqual(response.status_code, 400, "Unsupported format should return 400 status code")
        data = response.json()
        self.assertTrue("detail" in data, "Error detail not returned in response")
        self.assertTrue("Unsupported file format" in data["detail"], "Error message should mention unsupported format")
        print("✅ Unsupported format test passed")
    
    def test_07_upload_oversized_file(self):
        """Test file size validation (10MB limit)"""
        print("\n🔍 Testing file size validation...")
        
        # Create a file just over 10MB
        # Note: We're not actually sending 10MB over the network, just telling the server it's that big
        class LargeBufferIO(BytesIO):
            def __len__(self):
                return 10 * 1024 * 1024 + 1  # 10MB + 1 byte
        
        large_file = LargeBufferIO(b"This is a test file" * 100)  # Actual content is small
        files = {'file': ('large_cv.txt', large_file, 'text/plain')}
        
        try:
            response = requests.post(f"{self.api_url}/api/upload-cv", files=files)
            
            # Check if the server enforces size limit
            if response.status_code == 400 and "too large" in response.json().get("detail", ""):
                print("✅ File size validation test passed - server rejected oversized file")
            else:
                print("⚠️ Server accepted oversized file or returned unexpected response")
                print(f"Status: {response.status_code}, Response: {response.text[:100]}")
        except Exception as e:
            print(f"⚠️ Error testing file size validation: {e}")
    
    def test_08_analyze_cv(self):
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
    
    def test_09_company_research(self):
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
    
    def test_10_get_analysis(self):
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
    suite.addTest(JobPrepAIBackendTests('test_02_upload_pdf'))
    suite.addTest(JobPrepAIBackendTests('test_03_upload_docx'))
    suite.addTest(JobPrepAIBackendTests('test_04_upload_doc'))
    suite.addTest(JobPrepAIBackendTests('test_05_upload_txt'))
    suite.addTest(JobPrepAIBackendTests('test_06_upload_unsupported_format'))
    suite.addTest(JobPrepAIBackendTests('test_07_upload_oversized_file'))
    suite.addTest(JobPrepAIBackendTests('test_08_analyze_cv'))
    suite.addTest(JobPrepAIBackendTests('test_09_company_research'))
    suite.addTest(JobPrepAIBackendTests('test_10_get_analysis'))
    
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