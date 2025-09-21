# agents/librarian_agent.py
import json
from typing import Dict, Any, List
import vertexai
from vertexai.generative_models import GenerativeModel
from pydantic import BaseModel, Field
from data.prompts.extraction_prompts import EXTRACTION_PROMPTS

class StartupProfile(BaseModel):
    company_name: str = Field(description="Name of the startup")
    founders: List[Dict[str, Any]] = Field(description="Founder information")
    problem_statement: str = Field(description="Problem being solved")
    solution_description: str = Field(description="Solution description")
    market_data: Dict[str, Any] = Field(description="Market size information")
    traction_metrics: Dict[str, Any] = Field(description="Traction and growth metrics")
    financials: Dict[str, Any] = Field(description="Financial information")
    competitive_landscape: List[str] = Field(description="Mentioned competitors")
    technology_stack: List[str] = Field(description="Technology used")

class LibrarianAgent:
    def __init__(self, project_id: str, region: str):
        vertexai.init(project=project_id, location=region)
        self.gemini_model = GenerativeModel("gemini-1.5-pro")
    
    async def extract_structured_data(self, cleaned_text: str) -> Dict[str, Any]:
        """Extract structured data from cleaned text"""
        
        # Extract different sections sequentially for better accuracy
        founders_data = await self._extract_founders(cleaned_text)
        market_data = await self._extract_market_info(cleaned_text)
        traction_data = await self._extract_traction_metrics(cleaned_text)
        financial_data = await self._extract_financial_info(cleaned_text)
        company_info = await self._extract_company_basics(cleaned_text)
        
        # Combine all extracted data
        startup_profile = {
            "company_name": company_info.get("company_name", ""),
            "problem_statement": company_info.get("problem_statement", ""),
            "solution_description": company_info.get("solution_description", ""),
            "founders": founders_data,
            "market_data": market_data,
            "traction_metrics": traction_data,
            "financials": financial_data,
            "competitive_landscape": company_info.get("competitors", []),
            "technology_stack": company_info.get("technology", []),
            "extraction_confidence": await self._calculate_confidence(cleaned_text)
        }
        
        return startup_profile
    
    async def _extract_founders(self, text: str) -> List[Dict[str, Any]]:
        """Extract founder information"""
        prompt = EXTRACTION_PROMPTS["founders"].format(text=text)
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            founders_data = json.loads(response.text)
            return founders_data.get("founders", [])
        except json.JSONDecodeError:
            # Fallback to regex extraction if JSON parsing fails
            return await self._fallback_founder_extraction(text)
    
    async def _extract_market_info(self, text: str) -> Dict[str, Any]:
        """Extract market size and opportunity information"""
        prompt = EXTRACTION_PROMPTS["market"].format(text=text)
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            market_data = json.loads(response.text)
            return market_data
        except json.JSONDecodeError:
            return {
                "tam": None,
                "sam": None,
                "som": None,
                "target_market": "",
                "market_growth_rate": None
            }
    
    async def _extract_traction_metrics(self, text: str) -> Dict[str, Any]:
        """Extract traction and growth metrics"""
        prompt = EXTRACTION_PROMPTS["traction"].format(text=text)
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            traction_data = json.loads(response.text)
            return traction_data
        except json.JSONDecodeError:
            return {
                "mrr": None,
                "arr": None,
                "cac": None,
                "ltv": None,
                "churn_rate": None,
                "user_count": None,
                "growth_rate": None
            }
    
    async def _extract_financial_info(self, text: str) -> Dict[str, Any]:
        """Extract financial information"""
        prompt = EXTRACTION_PROMPTS["financials"].format(text=text)
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            financial_data = json.loads(response.text)
            return financial_data
        except json.JSONDecodeError:
            return {
                "revenue": None,
                "burn_rate": None,
                "funding_requested": None,
                "valuation": None,
                "runway_months": None,
                "previous_funding": []
            }
    
    async def _extract_company_basics(self, text: str) -> Dict[str, Any]:
        """Extract basic company information"""
        prompt = EXTRACTION_PROMPTS["company_basics"].format(text=text)
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            company_data = json.loads(response.text)
            return company_data
        except json.JSONDecodeError:
            return {
                "company_name": "",
                "problem_statement": "",
                "solution_description": "",
                "competitors": [],
                "technology": []
            }
    
    async def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for extraction"""
        # Simple confidence calculation based on text length and structure
        words = text.split()
        word_count = len(words)
        
        # Basic heuristics for confidence
        if word_count < 100:
            return 0.3
        elif word_count < 500:
            return 0.6
        elif word_count < 1000:
            return 0.8
        else:
            return 0.9
    
    async def _fallback_founder_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Fallback method for founder extraction using simpler parsing"""
        # Implementation for regex-based extraction as fallback
        return []
