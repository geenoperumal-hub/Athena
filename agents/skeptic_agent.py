# agents/skeptic_agent.py
from typing import Dict, Any, List
import vertexai
from vertexai.generative_models import GenerativeModel
import json

class SkepticAgent:
    def __init__(self, project_id: str, region: str):
        vertexai.init(project=project_id, location=region)
        self.gemini_model = GenerativeModel("gemini-1.5-pro")
        
        # Define risk categories and their weights
        self.risk_categories = {
            "team_risk": 0.25,
            "market_risk": 0.20,
            "financial_risk": 0.20,
            "execution_risk": 0.15,
            "competitive_risk": 0.10,
            "technical_risk": 0.10
        }
    
    async def analyze_risks(self, enriched_profile: Dict[str, Any], 
                          quant_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive risk analysis"""
        
        risk_analyses = await asyncio.gather(
            self._analyze_team_risks(enriched_profile),
            self._analyze_market_risks(enriched_profile),
            self._analyze_financial_risks(enriched_profile, quant_analysis),
            self._analyze_execution_risks(enriched_profile),
            self._analyze_competitive_risks(enriched_profile),
            self._analyze_technical_risks(enriched_profile)
        )
        
        risk_assessment = {
            "team_risks": risk_analyses[0],
            "market_risks": risk_analyses[1],
            "financial_risks": risk_analyses[2],
            "execution_risks": risk_analyses[3],
            "competitive_risks": risk_analyses[4],
            "technical_risks": risk_analyses[5]
        }
        
        # Calculate overall risk score
        overall_risk = await self._calculate_overall_risk(risk_assessment)
        
        # Generate red flags summary
        red_flags = await self._identify_red_flags(enriched_profile, risk_assessment)
        
        return {
            "risk_assessment": risk_assessment,
            "overall_risk_score": overall_risk,
            "red_flags": red_flags,
            "due_diligence_questions": await self._generate_dd_questions(risk_assessment),
            "risk_mitigation_suggestions": await self._suggest_risk_mitigation(risk_assessment)
        }
    
    async def _analyze_team_risks(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team-related risks"""
        founders = profile.get("founders", [])
        founder_verification = profile.get("founder_verification", {})
        
        prompt = f"""
        Analyze the team risks for this startup based on the following data:
        
        Founders:
        {json.dumps(founders, indent=2)}
        
        Founder Verification:
        {json.dumps(founder_verification, indent=2)}
        
        Identify risks related to:
        - Experience gaps in key areas
        - Co-founder dynamics and complementarity
        - Previous startup experience
        - Domain expertise
        - Team completeness
        - Key person dependency
        
        Return JSON with:
        - "risk_score": 0-1 (1 being highest risk)
        - "risk_factors": list of identified risks
        - "strengths": list of team strengths
        - "recommendations": suggested improvements
        """
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "risk_score": 0.5,
                "risk_factors": ["Unable to analyze team risks"],
                "strengths": [],
                "recommendations": []
            }
    
    async def _analyze_market_risks(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market-related risks"""
        market_data = profile.get("market_data", {})
        competitive_analysis = profile.get("competitor_analysis", {})
        
        prompt = f"""
        Analyze market risks for this startup:
        
        Market Data:
        {json.dumps(market_data, indent=2)}
        
        Competitive Analysis:
        {json.dumps(competitive_analysis, indent=2)}
        
        Problem/Solution:
        Problem: {profile.get("problem_statement", "")}
        Solution: {profile.get("solution_description", "")}
        
        Assess risks related to:
        - Market size and growth potential
        - Market timing
        - Customer acquisition challenges
        - Market saturation
        - Regulatory risks
        - Economic sensitivity
        
        Return JSON with risk analysis.
        """
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"risk_score": 0.5, "risk_factors": [], "strengths": []}
    
    async def _analyze_financial_risks(self, profile: Dict[str, Any], 
                                     quant_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial risks"""
        financials = profile.get("financials", {})
        traction_metrics = profile.get("traction_metrics", {})
        percentile_rankings = quant_analysis.get("percentile_rankings", {})
        
        # Calculate key risk indicators
        risks = []
        risk_score = 0.0
        
        # Burn rate analysis
        burn_rate = financials.get("burn_rate", 0)
        revenue = financials.get("revenue", 0)
        runway_months = financials.get("runway_months", 0)
        
        if runway_months and runway_months < 12:
            risks.append("Short runway - less than 12 months")
            risk_score += 0.3
        
        # Unit economics analysis
        cac = traction_metrics.get("cac")
        ltv = traction_metrics.get("ltv")
        
        if cac and ltv and ltv/cac < 3:
            risks.append("Poor unit economics - LTV/CAC ratio below 3")
            risk_score += 0.2
        
        # Churn analysis
        churn_rate = traction_metrics.get("churn_rate")
        if churn_rate and churn_rate > 15:
            risks.append("High churn rate")
            risk_score += 0.2
        
        # Revenue growth
        if revenue == 0:
            risks.append("No revenue generated yet")
            risk_score += 0.1
        
        return {
            "risk_score": min(risk_score, 1.0),
            "risk_factors": risks,
            "key_metrics": {
                "runway_months": runway_months,
                "ltv_cac_ratio": ltv/cac if cac and ltv else None,
                "monthly_burn": burn_rate,
                "churn_rate": churn_rate
            },
            "recommendations": self._generate_financial_recommendations(risks)
        }
    
    async def _analyze_execution_risks(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze execution-related risks"""
        # This would analyze the startup's ability to execute on their plan
        return {
            "risk_score": 0.4,
            "risk_factors": ["Execution analysis not implemented"],
            "strengths": []
        }
    
    async def _analyze_competitive_risks(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive risks"""
        competitive_analysis = profile.get("competitor_analysis", {})
        
        return {
            "risk_score": 0.3,
            "risk_factors": ["Competitive analysis needs enhancement"],
            "strengths": []
        }
    
    async def _analyze_technical_risks(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical risks"""
        tech_stack = profile.get("technology_stack", [])
        tech_analysis = profile.get("technology_analysis", {})
        
        return {
            "risk_score": tech_analysis.get("technical_risk_score", 0.5),
            "risk_factors": ["Technical risk analysis needs enhancement"],
            "strengths": []
        }
    
    async def _calculate_overall_risk(self, risk_assessment: Dict[str, Any]) -> float:
        """Calculate weighted overall risk score"""
        total_risk = 0.0
        
        for category, weight in self.risk_categories.items():
            category_risk = risk_assessment.get(category, {}).get("risk_score", 0.5)
            total_risk += category_risk * weight
        
        return total_risk
    
    async def _identify_red_flags(self, profile: Dict[str, Any], 
                                 risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical red flags"""
        red_flags = []
        
        # Check for high-priority red flags
        for category, analysis in risk_assessment.items():
            risk_score = analysis.get("risk_score", 0)
            if risk_score > 0.7:  # High risk threshold
                red_flags.append({
                    "category": category,
                    "severity": "high",
                    "description": f"High risk identified in {category.replace('_', ' ')}",
                    "risk_factors": analysis.get("risk_factors", [])
                })
        
        return red_flags
    
    async def _generate_dd_questions(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate due diligence questions based on risks"""
        questions = []
        
        for category, analysis in risk_assessment.items():
            risk_factors = analysis.get("risk_factors", [])
            for risk in risk_factors:
                questions.append(f"How do you plan to address: {risk}?")
        
        return questions[:10]  # Limit to top 10 questions
    
    async def _suggest_risk_mitigation(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Suggest risk mitigation strategies"""
        suggestions = []
        
        # Add specific suggestions based on risk categories
        for category, analysis in risk_assessment.items():
            if analysis.get("risk_score", 0) > 0.6:
                suggestions.extend(analysis.get("recommendations", []))
        
        return suggestions
    
    def _generate_financial_recommendations(self, risks: List[str]) -> List[str]:
        """Generate financial risk mitigation recommendations"""
        recommendations = []
        
        for risk in risks:
            if "runway" in risk.lower():
                recommendations.append("Consider raising bridge funding or reducing burn rate")
            elif "unit economics" in risk.lower():
                recommendations.append("Focus on improving customer acquisition efficiency")
            elif "churn" in risk.lower():
                recommendations.append("Implement customer success initiatives to reduce churn")
            elif "revenue" in risk.lower():
                recommendations.append("Prioritize revenue generation and customer validation")
        
        return recommendations
