from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import openai
import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import PyPDF2
import io
import uuid
from pymongo import MongoClient
import logging

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

# OpenAI setup
openai.api_key = os.environ.get('OPENAI_API_KEY')

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

# AI Orchestration Engine
class AIOrchestrator:
    def __init__(self):
        self.gpt4_client = openai
        
    async def analyze_cv_with_gpt4(self, cv_text: str, target_role: str = None) -> Dict[str, Any]:
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
            response = await self.gpt4_client.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert CV optimization specialist with 15+ years of HR experience."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            # Try to parse JSON, fallback to structured text if needed
            try:
                return json.loads(content)
            except:
                return {"analysis": content, "source": "gpt4_creative"}
                
        except Exception as e:
            logger.error(f"GPT-4 CV analysis error: {e}")
            return {"error": str(e), "source": "gpt4_creative"}
    
    async def analyze_skills_gap(self, cv_text: str, target_role: str = None) -> Dict[str, Any]:
        """Specialized skills gap analysis using GPT-4"""
        
        prompt = f"""As a technical skills analyst, perform a comprehensive skills gap analysis.

CV Content: {cv_text}
Target Role: {target_role or "Software Engineer"}

Analyze and return JSON with:

1. "current_skills": Categorized list of skills found in CV
2. "missing_critical_skills": Skills essential for the target role that are missing
3. "emerging_skills": Trending skills in this field for 2025
4. "skill_strength_scores": Rate each current skill (1-10)
5. "learning_priorities": Top 5 skills to learn first with reasons
6. "market_demand": How in-demand each skill is (High/Medium/Low)
7. "learning_resources": Specific recommendations for acquiring missing skills
8. "timeline_estimate": Realistic timeline to bridge the gap

Focus on 2025 market trends and emerging technologies."""

        try:
            response = await self.gpt4_client.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a technical skills analyst tracking 2025 market trends."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                return {"analysis": content, "source": "gpt4_skills"}
                
        except Exception as e:
            logger.error(f"Skills analysis error: {e}")
            return {"error": str(e), "source": "gpt4_skills"}

    async def ensemble_analysis(self, cv_text: str, target_role: str = None) -> Dict[str, Any]:
        """Combine multiple AI analyses for superior insights"""
        
        # Get analyses from different specialized prompts
        cv_analysis = await self.analyze_cv_with_gpt4(cv_text, target_role)
        skills_analysis = await self.analyze_skills_gap(cv_text, target_role)
        
        # Create ensemble insights
        ensemble_prompt = f"""Based on these two AI analyses, provide a unified recommendation:

CV Analysis Results: {json.dumps(cv_analysis, indent=2)}

Skills Analysis Results: {json.dumps(skills_analysis, indent=2)}

Create a final JSON recommendation with:
1. "confidence_score": Overall confidence in analysis (0-100)
2. "priority_actions": Top 3 immediate actions to take
3. "long_term_strategy": 6-month improvement plan
4. "competitive_advantage": How to stand out from other candidates
5. "ai_consensus": Where both analyses agree
6. "ai_differences": Where analyses differ and why

Provide actionable, specific guidance."""

        try:
            response = await self.gpt4_client.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an AI ensemble coordinator providing unified career guidance."},
                    {"role": "user", "content": ensemble_prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            try:
                ensemble_result = json.loads(content)
            except:
                ensemble_result = {"analysis": content, "source": "ensemble"}
            
            return {
                "cv_analysis": cv_analysis,
                "skills_analysis": skills_analysis,
                "ensemble_insights": ensemble_result
            }
            
        except Exception as e:
            logger.error(f"Ensemble analysis error: {e}")
            return {
                "cv_analysis": cv_analysis,
                "skills_analysis": skills_analysis,
                "ensemble_insights": {"error": str(e)}
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
            response = await openai.ChatCompletion.acreate(
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
            response = await openai.ChatCompletion.acreate(
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "JobPrep AI - Multi-AI Orchestration"}

@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """Upload and extract text from CV"""
    try:
        content = await file.read()
        
        if file.filename.lower().endswith('.pdf'):
            pdf_file = io.BytesIO(content)
            cv_text = extract_text_from_pdf(pdf_file)
        else:
            # Assume text file
            cv_text = content.decode('utf-8')
        
        if not cv_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from CV")
        
        return {
            "success": True,
            "cv_text": cv_text,
            "filename": file.filename,
            "length": len(cv_text)
        }
        
    except Exception as e:
        logger.error(f"CV upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")

@app.post("/api/analyze-cv")
async def analyze_cv(request: CVAnalysisRequest):
    """Comprehensive CV analysis using Multi-AI Orchestration"""
    try:
        analysis_id = str(uuid.uuid4())
        
        # Multi-AI Analysis
        ai_results = await ai_orchestrator.ensemble_analysis(
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
        
        # Calculate confidence score
        confidence_score = 85.0  # Base confidence, adjust based on AI responses
        
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
            "confidence_score": confidence_score,
            "recommendations": recommendations
        }
        
        analyses_collection.insert_one(analysis_result)
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            cv_improvements=ai_results.get("cv_analysis", {}),
            skills_analysis=ai_results.get("skills_analysis", {}),
            company_insights=company_insights,
            confidence_score=confidence_score,
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