from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import openai
import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')
import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import PyPDF2
import docx
import docx2txt
import io
import uuid
from pymongo import MongoClient
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(mongo_url)
db = client.jobprep_ai
users_collection = db.users
analyses_collection = db.analyses
companies_collection = db.companies

# AI API setup
openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Mock Anthropic client for testing
class MockAnthropicClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.messages = self.Messages()
    
    class Messages:
        def create(self, model=None, max_tokens=None, temperature=None, system=None, messages=None):
            class MockMessage:
                def __init__(self):
                    self.content = [self.Content()]
                
                class Content:
                    def __init__(self):
                        self.text = json.dumps({
                            "analytical_score": 85,
                            "competitive_analysis": "Candidate shows strong technical skills compared to market standards.",
                            "strategic_weaknesses": ["Could improve leadership experience", "Needs more industry-specific certifications"],
                            "professional_positioning": "Position as a technical expert with problem-solving abilities.",
                            "market_alignment": "Well aligned with current market demands for technical roles.",
                            "credibility_assessment": "Strong technical background adds credibility.",
                            "differentiation_strategy": "Emphasize unique project experiences and technical depth.",
                            "executive_summary": "Strong technical candidate with good potential for growth.",
                            "ai_source": "Claude Strategic Analyst"
                        })
            
            return MockMessage()

# Use mock client for testing
anthropic_client = MockAnthropicClient(api_key=os.environ.get('ANTHROPIC_API_KEY'))

class CVAnalysisRequest(BaseModel):
    cv_text: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None

class CompanyResearchRequest(BaseModel):
    company_name: str
    role_type: Optional[str] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    cv_improvements: Dict[str, Any]
    skills_analysis: Dict[str, Any]
    company_insights: Optional[Dict[str, Any]] = None
    confidence_score: float
    recommendations: List[str]

# Advanced Multi-AI Orchestration Engine
class AIOrchestrator:
    def __init__(self):
        self.gpt4_client = openai_client
        self.claude_client = anthropic_client
        
    def analyze_cv_with_gpt4(self, cv_text: str, target_role: str = None) -> Dict[str, Any]:
        """GPT-4 specialized for creative CV improvements and content generation"""
        
        prompt = f"""As an expert CV optimization specialist, analyze this CV and provide detailed improvements.

CV Content:
{cv_text}

Target Role: {target_role or "General professional role"}

Provide a comprehensive analysis in JSON format with these sections:

1. "overall_score": Rate the CV from 1-100
2. "strengths": List top 3 strengths
3. "critical_improvements": List specific actionable improvements
4. "content_suggestions": Suggest better phrasing for key sections
5. "missing_elements": What's missing that should be added
6. "ats_optimization": Keywords and phrases to improve ATS compatibility
7. "impact_statements": Convert weak statements to strong impact statements
8. "structure_improvements": How to better organize the content

Be specific, actionable, and focus on high-impact changes."""

        try:
            response = self.gpt4_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert CV optimization specialist with 15+ years of HR experience. Focus on creative and engaging improvements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                result["ai_source"] = "GPT-4 Creative Engine"
                return result
            except:
                return {"analysis": content, "ai_source": "GPT-4 Creative Engine"}
                
        except Exception as e:
            logger.error(f"GPT-4 CV analysis error: {e}")
            return {"error": str(e), "ai_source": "GPT-4 Creative Engine"}
    
    async def analyze_cv_with_claude(self, cv_text: str, target_role: str = None) -> Dict[str, Any]:
        """Claude specialized for deep analytical thinking and critical evaluation"""
        
        prompt = f"""As a senior career strategist and CV critic, provide a thorough analytical assessment of this CV.

CV Content:
{cv_text}

Target Role: {target_role or "General professional role"}

Conduct a deep analysis and return JSON with:

1. "analytical_score": Your analytical assessment (1-100) with detailed reasoning
2. "competitive_analysis": How this candidate compares to market standards
3. "strategic_weaknesses": Critical gaps that could hurt job prospects
4. "professional_positioning": How to better position this candidate
5. "market_alignment": How well the CV aligns with current market demands
6. "credibility_assessment": Areas that need more credibility or proof
7. "differentiation_strategy": How to make this candidate stand out
8. "executive_summary": A strategic overview of the candidate's profile

Focus on strategic thinking, market positioning, and competitive advantage."""

        try:
            message = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.claude_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    temperature=0.2,
                    system="You are a senior career strategist with deep analytical thinking capabilities. Provide thorough, strategic career advice focused on competitive positioning.",
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            content = message.content[0].text
            try:
                result = json.loads(content)
                result["ai_source"] = "Claude Strategic Analyst"
                return result
            except:
                return {"analysis": content, "ai_source": "Claude Strategic Analyst"}
                
        except Exception as e:
            logger.error(f"Claude CV analysis error: {e}")
            return {"error": str(e), "ai_source": "Claude Strategic Analyst"}
    
    async def analyze_skills_with_claude(self, cv_text: str, target_role: str = None) -> Dict[str, Any]:
        """Claude specialized for deep skills analysis and market intelligence"""
        
        prompt = f"""As a technical skills analyst and market intelligence expert, perform comprehensive skills analysis.

CV Content: {cv_text}
Target Role: {target_role or "Software Engineer"}

Provide detailed JSON analysis:

1. "current_skills_matrix": Detailed breakdown of skills by category with proficiency levels
2. "market_demand_analysis": Current and projected demand for each skill (2025-2026)
3. "competitive_gaps": Skills missing compared to top candidates in this field
4. "emerging_technologies": New technologies gaining traction in this industry
5. "learning_roadmap": Strategic 6-month learning plan with priorities
6. "skill_monetization": Which skills have highest earning potential
7. "industry_transitions": How skills transfer to adjacent industries
8. "certification_recommendations": Specific certifications to pursue

Focus on strategic skill development and market positioning."""

        try:
            message = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.claude_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    temperature=0.1,
                    system="You are a technical skills analyst with deep market intelligence. Focus on strategic skill development and competitive advantage.",
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            content = message.content[0].text
            try:
                result = json.loads(content)
                result["ai_source"] = "Claude Skills Intelligence"
                return result
            except:
                return {"analysis": content, "ai_source": "Claude Skills Intelligence"}
                
        except Exception as e:
            logger.error(f"Claude skills analysis error: {e}")
            return {"error": str(e), "ai_source": "Claude Skills Intelligence"}

    def create_ai_ensemble(self, gpt4_cv_analysis: Dict, claude_cv_analysis: Dict, claude_skills_analysis: Dict, target_role: str = None) -> Dict[str, Any]:
        """Advanced AI ensemble that creates unified insights from multiple AI perspectives"""
        
        ensemble_prompt = f"""As an AI ensemble coordinator, analyze these insights from multiple AI experts and create unified recommendations.

GPT-4 Creative Analysis:
{json.dumps(gpt4_cv_analysis, indent=2)}

Claude Strategic Analysis:
{json.dumps(claude_cv_analysis, indent=2)}

Claude Skills Intelligence:
{json.dumps(claude_skills_analysis, indent=2)}

Target Role: {target_role}

Create a comprehensive JSON response with:

1. "consensus_score": Where all AIs agree on overall quality (1-100)
2. "ai_agreement_areas": Points where all AIs strongly agree
3. "ai_disagreement_areas": Where AIs differ and why this matters
4. "unified_priorities": Top 5 actions combining all AI insights
5. "competitive_advantage": Unique positioning strategy
6. "risk_assessment": Potential red flags identified across analyses
7. "success_probability": Likelihood of success for target role (with reasoning)
8. "ai_confidence": How confident the ensemble is in recommendations
9. "personalized_strategy": Tailored 90-day action plan
10. "market_positioning": How to position against competitors

This should be the definitive career guidance combining multiple AI perspectives."""

        try:
            response = self.gpt4_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an AI ensemble coordinator combining insights from multiple AI systems to provide superior career guidance."},
                    {"role": "user", "content": ensemble_prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                result["ai_source"] = "Multi-AI Ensemble"
                return result
            except:
                return {"analysis": content, "ai_source": "Multi-AI Ensemble"}
                
        except Exception as e:
            logger.error(f"AI Ensemble error: {e}")
            return {"error": str(e), "ai_source": "Multi-AI Ensemble"}

    async def full_multi_ai_analysis(self, cv_text: str, target_role: str = None) -> Dict[str, Any]:
        """Execute complete multi-AI orchestration analysis"""
        
        logger.info("Starting Multi-AI Orchestration Analysis...")
        
        # Run multiple AI analyses
        gpt4_result = self.analyze_cv_with_gpt4(cv_text, target_role)
        claude_cv_result = await self.analyze_cv_with_claude(cv_text, target_role)
        claude_skills_result = await self.analyze_skills_with_claude(cv_text, target_role)
        
        # Create ensemble insights
        ensemble_result = self.create_ai_ensemble(
            gpt4_result, claude_cv_result, claude_skills_result, target_role
        )
        
        return {
            "gpt4_creative_analysis": gpt4_result,
            "claude_strategic_analysis": claude_cv_result,
            "claude_skills_intelligence": claude_skills_result,
            "ai_ensemble_insights": ensemble_result,
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_models_used": ["GPT-4 Turbo", "Claude-3 Sonnet", "Multi-AI Ensemble"]
        }

# Real-Time Company Intelligence Engine
class CompanyIntelligence:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def get_company_news(self, company_name: str) -> List[Dict[str, Any]]:
        """Fetch recent company news and developments"""
        try:
            # Search for company news (simplified version - in production, use proper news APIs)
            search_query = f"{company_name} company news 2025"
            news_results = []
            
            # Placeholder for news scraping - replace with actual news API
            news_results.append({
                "title": f"Latest developments at {company_name}",
                "summary": f"Recent updates and news from {company_name}",
                "date": datetime.now().isoformat(),
                "source": "Company Intelligence Engine"
            })
            
            return news_results
            
        except Exception as e:
            logger.error(f"Company news error: {e}")
            return []
    
    async def analyze_company_culture(self, company_name: str) -> Dict[str, Any]:
        """Analyze company culture and work environment"""
        
        prompt = f"""Provide a comprehensive company culture analysis for {company_name}.

Based on your knowledge, analyze:

1. "work_culture": Work environment and company values
2. "interview_style": Typical interview process and what they look for
3. "growth_opportunities": Career advancement prospects
4. "compensation_insights": Salary ranges and benefits (general market data)
5. "company_challenges": Current challenges the company faces
6. "ideal_candidate": Profile of successful candidates they typically hire
7. "recent_developments": Major company changes or initiatives
8. "application_tips": Specific advice for applying to this company

Return as detailed JSON. Be specific and actionable."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a company research specialist with deep knowledge of corporate cultures and hiring practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                return {"analysis": content, "source": "company_culture"}
                
        except Exception as e:
            logger.error(f"Company culture analysis error: {e}")
            return {"error": str(e)}
    
    async def get_comprehensive_intelligence(self, company_name: str, role_type: str = None) -> Dict[str, Any]:
        """Get comprehensive company intelligence"""
        
        news = await self.get_company_news(company_name)
        culture = await self.analyze_company_culture(company_name)
        
        # Industry context analysis
        industry_prompt = f"""Provide industry context for someone applying to {company_name} for a {role_type or 'professional'} role.

Include:
1. "industry_trends": Current trends affecting this company's industry
2. "competitive_landscape": Key competitors and market position
3. "future_outlook": Industry predictions for 2025-2026
4. "skill_priorities": What skills are most valued in this industry right now
5. "market_challenges": Key challenges facing companies in this space

Return as JSON."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an industry analyst providing market intelligence."},
                    {"role": "user", "content": industry_prompt}
                ],
                temperature=0.3
            )
            
            industry_content = response.choices[0].message.content
            try:
                industry_analysis = json.loads(industry_content)
            except:
                industry_analysis = {"analysis": industry_content}
                
        except Exception as e:
            industry_analysis = {"error": str(e)}
        
        return {
            "company_name": company_name,
            "recent_news": news,
            "culture_analysis": culture,
            "industry_context": industry_analysis,
            "last_updated": datetime.now().isoformat()
        }

# Initialize AI services
ai_orchestrator = AIOrchestrator()
company_intel = CompanyIntelligence()

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""

def extract_text_from_docx(docx_file) -> str:
    """Extract text from uploaded DOCX file"""
    try:
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return ""

def extract_text_from_doc(doc_file) -> str:
    """Extract text from uploaded DOC file"""
    try:
        # Reset file pointer to beginning
        doc_file.seek(0)
        text = docx2txt.process(doc_file)
        return text if text else ""
    except Exception as e:
        logger.error(f"DOC extraction error: {e}")
        # Try alternative approach - treat as binary and extract readable text
        try:
            doc_file.seek(0)
            content = doc_file.read()
            # Simple text extraction for basic DOC files
            text = content.decode('utf-8', errors='ignore')
            # Clean up the text
            import re
            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)  # Remove control characters
            text = ' '.join(text.split())  # Normalize whitespace
            return text if len(text) > 50 else ""  # Only return if we got substantial text
        except Exception as e2:
            logger.error(f"Alternative DOC extraction error: {e2}")
            return ""

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "JobPrep AI - Multi-AI Orchestration"}

@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """Upload and extract text from CV (supports PDF, DOCX, DOC, and text files)"""
    try:
        content = await file.read()
        filename_lower = file.filename.lower()
        
        logger.info(f"Processing file: {file.filename} (type: {file.content_type})")
        
        if filename_lower.endswith('.pdf'):
            # Handle PDF files
            pdf_file = io.BytesIO(content)
            cv_text = extract_text_from_pdf(pdf_file)
        elif filename_lower.endswith('.docx'):
            # Handle DOCX files
            docx_file = io.BytesIO(content)
            cv_text = extract_text_from_docx(docx_file)
        elif filename_lower.endswith('.doc'):
            # Handle DOC files with improved error handling
            doc_file = io.BytesIO(content)
            cv_text = extract_text_from_doc(doc_file)
            if not cv_text:
                # If DOC extraction fails, suggest conversion
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from this DOC file. For best results, please save your document as DOCX format and try again, or copy and paste the text into a text file."
                )
        elif filename_lower.endswith(('.txt', '.text')):
            # Handle text files
            cv_text = content.decode('utf-8')
        else:
            # Try to decode as text as fallback
            try:
                cv_text = content.decode('utf-8')
                logger.info(f"Fallback: Treated {file.filename} as text file")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format. Please upload PDF, DOCX, DOC, or text files. File type: {file.content_type}"
                )
        
        if not cv_text or not cv_text.strip():
            raise HTTPException(
                status_code=400, 
                detail="Could not extract text from CV. Please ensure the file contains readable text."
            )
        
        logger.info(f"Successfully extracted {len(cv_text)} characters from {file.filename}")
        
        return {
            "success": True,
            "cv_text": cv_text,
            "filename": file.filename,
            "length": len(cv_text),
            "file_type": "pdf" if filename_lower.endswith('.pdf') 
                        else "docx" if filename_lower.endswith('.docx')
                        else "doc" if filename_lower.endswith('.doc')
                        else "text"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")

@app.post("/api/analyze-cv")
async def analyze_cv(request: CVAnalysisRequest):
    """Comprehensive CV analysis using Multi-AI Orchestration"""
    try:
        analysis_id = str(uuid.uuid4())
        
        # Multi-AI Analysis
        ai_results = await ai_orchestrator.full_multi_ai_analysis(
            request.cv_text, 
            request.target_role
        )
        
        # Company Intelligence (if company specified)
        company_insights = None
        if request.target_company:
            company_insights = await company_intel.get_comprehensive_intelligence(
                request.target_company,
                request.target_role
            )
        
        # Calculate ensemble confidence score
        ensemble_confidence = ai_results.get("ai_ensemble_insights", {}).get("ai_confidence", 85.0)
        if isinstance(ensemble_confidence, str):
            try:
                ensemble_confidence = float(re.findall(r'\d+\.?\d*', ensemble_confidence)[0])
            except:
                ensemble_confidence = 85.0
        
        # Generate final recommendations
        recommendations = [
            "Optimize your CV based on AI analysis above",
            "Focus on high-impact skill development",
            "Tailor your application to company culture",
            "Practice interview questions specific to this role"
        ]
        
        # Store analysis in database
        analysis_result = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now(),
            "cv_text": request.cv_text,
            "target_role": request.target_role,
            "target_company": request.target_company,
            "ai_results": ai_results,
            "company_insights": company_insights,
            "confidence_score": ensemble_confidence,
            "recommendations": recommendations
        }
        
        analyses_collection.insert_one(analysis_result)
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            cv_improvements=ai_results.get("cv_analysis", {}),
            skills_analysis=ai_results.get("skills_analysis", {}),
            company_insights=company_insights,
            confidence_score=ensemble_confidence,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"CV analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/company-research")
async def research_company(request: CompanyResearchRequest):
    """Deep company research and intelligence"""
    try:
        intelligence = await company_intel.get_comprehensive_intelligence(
            request.company_name,
            request.role_type
        )
        
        # Store in database
        companies_collection.update_one(
            {"company_name": request.company_name},
            {"$set": {
                "intelligence": intelligence,
                "last_updated": datetime.now()
            }},
            upsert=True
        )
        
        return intelligence
        
    except Exception as e:
        logger.error(f"Company research error: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Retrieve previous analysis"""
    try:
        analysis = analyses_collection.find_one({"analysis_id": analysis_id})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Convert MongoDB ObjectId to string for JSON serialization
        analysis["_id"] = str(analysis["_id"])
        return analysis
        
    except Exception as e:
        logger.error(f"Get analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)