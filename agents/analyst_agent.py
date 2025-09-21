# agents/analyst_agent.py
from typing import Dict, Any, List
import vertexai
from vertexai.generative_models import GenerativeModel
from datetime import datetime
import json

class AnalystAgent:
    def __init__(self, project_id: str, region: str):
        vertexai.init(project=project_id, location=region)
        self.gemini_model = GenerativeModel("gemini-1.5-pro")
        
        # Investment thesis weights (configurable)
        self.thesis_weights = {
            "team": 0.40,
            "market": 0.30,
            "traction": 0.20,
            "moat": 0.10
        }
    
    async def synthesize_analysis(self, enriched_profile: Dict[str, Any],
                                quant_analysis: Dict[str, Any],
                                risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final investment memo and recommendation"""
        
        # Calculate investment score
        investment_score = await self._calculate_investment_score(
            enriched_profile, quant_analysis, risk_analysis
        )
        
        # Generate SWOT analysis
        swot_analysis = await self._generate_swot_analysis(
            enriched_profile, quant_analysis, risk_analysis
        )
        
        # Create investment memo
        investment_memo = await self._generate_investment_memo(
            enriched_profile, quant_analysis, risk_analysis, 
            investment_score, swot_analysis
        )
        
        # Generate final recommendation
        recommendation = await self._generate_recommendation(
            investment_score, risk_analysis
        )
        
        return {
            "investment_score": investment_score,
            "recommendation": recommendation,
            "investment_memo": investment_memo,
            "swot_analysis": swot_analysis,
            "executive_summary": await self._generate_executive_summary(
                enriched_profile, investment_score, recommendation
            ),
            "analysis_metadata": {
                "analysis_date": datetime.utcnow().isoformat(),
                "confidence_level": await self._calculate_confidence_level(enriched_profile),
                "data_completeness": await self._assess_data_completeness(enriched_profile)
            }
        }
    
    async def _calculate_investment_score(self, profile: Dict[str, Any],
                                        quant: Dict[str, Any],
                                        risk: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weighted investment score"""
        
        # Team score (0-1)
        team_score = await self._score_team(profile)
        
        # Market score (0-1)
        market_score = await self._score_market(profile)
        
        # Traction score (0-1)
        traction_score = quant.get("overall_score", 0.5)
        
        # Moat score (0-1)
        moat_score = await self._score_moat(profile)
        
        # Calculate weighted score
        weighted_score = (
            team_score * self.thesis_weights["team"] +
            market_score * self.thesis_weights["market"] +
            traction_score * self.thesis_weights["traction"] +
            moat_score * self.thesis_weights["moat"]
        )
        
        # Adjust for risk
        risk_adjustment = 1 - risk.get("overall_risk_score", 0.5)
        final_score = weighted_score * risk_adjustment
        
        return {
            "overall_score": final_score,
            "component_scores": {
                "team": team_score,
                "market": market_score,
                "traction": traction_score,
                "moat": moat_score
            },
            "risk_adjustment": risk_adjustment,
            "weighted_score": weighted_score
        }
    
    async def _score_team(self, profile: Dict[str, Any]) -> float:
        """Score team quality (0-1)"""
        founders = profile.get("founders", [])
        verification = profile.get("founder_verification", {})
        
        if not founders:
            return 0.3
        
        # Simple scoring logic - in production, this would be more sophisticated
        score = 0.5  # Base score
        
        # Bonus for relevant experience
        for founder in founders:
            experience = founder.get("experience_years", 0)
            if experience > 5:
                score += 0.1
            if "ex-" in founder.get("background", "").lower():
                score += 0.1
        
        # Verification bonus/penalty
        for name, ver in verification.items():
            verification_score = ver.get("verification_score", 0.5)
            score += (verification_score - 0.5) * 0.2
        
        return min(score, 1.0)
    
    async def _score_market(self, profile: Dict[str, Any]) -> float:
        """Score market opportunity (0-1)"""
        market_data = profile.get("market_data", {})
        market_validation = profile.get("market_validation", {})
        
        score = 0.5  # Base score
        
        # TAM size bonus
        tam = market_data.get("tam", 0)
        if tam > 1000000000:  # $1B+ TAM
            score += 0.2
        elif tam > 100000000:  # $100M+ TAM
            score += 0.1
        
        # Market validation
        validation_score = market_validation.get("addressable_market_score", 0.5)
        score += (validation_score - 0.5) * 0.3
        
        return min(score, 1.0)
    
    async def _score_moat(self, profile: Dict[str, Any]) -> float:
        """Score competitive moat (0-1)"""
        # This would analyze the startup's defensibility
        # For now, return a default score
        return 0.5
    
    async def _generate_swot_analysis(self, profile: Dict[str, Any],
                                    quant: Dict[str, Any],
                                    risk: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SWOT analysis"""
        prompt = f"""
        Generate a comprehensive SWOT analysis for this startup based on the following data:
        
        Company: {profile.get("company_name", "Unknown")}
        
        Team Data:
        {json.dumps(profile.get("founders", []), indent=2)}
        
        Market & Traction:
        Problem: {profile.get("problem_statement", "")}
        Solution: {profile.get("solution_description", "")}
        Market Data: {json.dumps(profile.get("market_data", {}), indent=2)}
        Traction: {json.dumps(profile.get("traction_metrics", {}), indent=2)}
        
        Quantitative Analysis:
        {json.dumps(quant.get("percentile_rankings", {}), indent=2)}
        
        Risk Assessment:
        {json.dumps(risk.get("red_flags", []), indent=2)}
        
        Create a SWOT analysis with:
        - Strengths: 3-5 key strengths
        - Weaknesses: 3-5 key weaknesses  
        - Opportunities: 3-5 market opportunities
        - Threats: 3-5 potential threats
        
        Return as JSON with clear, actionable insights.
        """
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "strengths": ["Analysis pending"],
                "weaknesses": ["Analysis pending"],
                "opportunities": ["Analysis pending"],
                "threats": ["Analysis pending"]
            }
    
    async def _generate_investment_memo(self, profile: Dict[str, Any],
                                      quant: Dict[str, Any],
                                      risk: Dict[str, Any],
                                      investment_score: Dict[str, Any],
                                      swot: Dict[str, Any]) -> str:
        """Generate comprehensive investment memo"""
        prompt = f"""
        Write a professional investment memo (2-3 pages) for this startup opportunity:
        
        COMPANY OVERVIEW:
        Company: {profile.get("company_name", "TBD")}
        Problem: {profile.get("problem_statement", "")}
        Solution: {profile.get("solution_description", "")}
        
        TEAM:
        {json.dumps(profile.get("founders", []), indent=2)}
        
        MARKET & TRACTION:
        Market Size: ${profile.get("market_data", {}).get("tam", "TBD")}
        Current Metrics: {json.dumps(profile.get("traction_metrics", {}), indent=2)}
        
        FINANCIAL DATA:
        {json.dumps(profile.get("financials", {}), indent=2)}
        
        INVESTMENT SCORING:
        Overall Score: {investment_score.get("overall_score", 0):.2f}/1.0
        Component Scores: {json.dumps(investment_score.get("component_scores", {}), indent=2)}
        
        SWOT ANALYSIS:
        {json.dumps(swot, indent=2)}
        
        RISK ASSESSMENT:
        Overall Risk: {risk.get("overall_risk_score", 0.5):.2f}
        Key Risks: {json.dumps(risk.get("red_flags", []), indent=2)}
        
        Structure the memo with these sections:
        1. Executive Summary
        2. Company Overview  
        3. Market Opportunity
        4. Team Assessment
        5. Business Model & Traction
        6. Financial Analysis
        7. Risk Assessment
        8. Investment Thesis
        9. Recommendation
        
        Write in a professional, analytical tone suitable for an investment committee.
        Be specific with numbers and provide clear reasoning for the recommendation.
        """
        
        response = await self.gemini_model.generate_content_async(prompt)
        return response.text
    
    async def _generate_recommendation(self, investment_score: Dict[str, Any],
                                     risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final investment recommendation"""
        overall_score = investment_score.get("overall_score", 0)
        risk_score = risk_analysis.get("overall_risk_score", 0.5)
        
        # Decision logic
        if overall_score >= 0.7 and risk_score <= 0.4:
            decision = "PRIORITIZE"
            rationale = "Strong opportunity with manageable risk"
        elif overall_score >= 0.5 and risk_score <= 0.6:
            decision = "REVIEW"
            rationale = "Potential opportunity requiring deeper analysis"
        else:
            decision = "PASS"
            rationale = "Insufficient opportunity or excessive risk"
        
        return {
            "decision": decision,
            "rationale": rationale,
            "confidence": self._calculate_recommendation_confidence(overall_score, risk_score),
            "next_steps": self._generate_next_steps(decision),
            "key_questions": risk_analysis.get("due_diligence_questions", [])[:5]
        }
    
    def _calculate_recommendation_confidence(self, score: float, risk: float) -> str:
        """Calculate confidence in recommendation"""
        if abs(score - 0.5) > 0.3:  # Clear signal
            return "HIGH"
        elif abs(score - 0.5) > 0.15:  # Moderate signal
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_next_steps(self, decision: str) -> List[str]:
        """Generate next steps based on decision"""
        if decision == "PRIORITIZE":
            return [
                "Schedule founder meeting",
                "Begin formal due diligence",
                "Prepare term sheet",
                "Conduct reference checks"
            ]
        elif decision == "REVIEW":
            return [
                "Deeper market analysis",
                "Customer interviews",
                "Technical assessment",
                "Follow-up with founders"
            ]
        else:  # PASS
            return [
                "Send polite decline",
                "Monitor for future progress",
                "Maintain relationship",
                "Archive analysis"
            ]
    
    async def _generate_executive_summary(self, profile: Dict[str, Any],
                                        investment_score: Dict[str, Any],
                                        recommendation: Dict[str, Any]) -> str:
        """Generate executive summary"""
        company_name = profile.get("company_name", "TBD")
        decision = recommendation.get("decision", "REVIEW")
        score = investment_score.get("overall_score", 0)
        
        return f"""
        EXECUTIVE SUMMARY - {company_name}
        
        RECOMMENDATION: {decision}
        INVESTMENT SCORE: {score:.2f}/1.0
        
        {company_name} is addressing {profile.get("problem_statement", "a market problem")} 
        with {profile.get("solution_description", "their solution")}.
        
        Key Strengths: Strong team background, {profile.get("market_data", {}).get("tam", "sizable")} market opportunity
        Key Concerns: {recommendation.get("rationale", "Standard early-stage risks")}
        
        Next Steps: {", ".join(recommendation.get("next_steps", [])[:3])}
        """
    
    async def _calculate_confidence_level(self, profile: Dict[str, Any]) -> str:
        """Calculate overall confidence in analysis"""
        # Based on data completeness and verification scores
        extraction_confidence = profile.get("extraction_confidence", 0.5)
        
        if extraction_confidence > 0.8:
            return "HIGH"
        elif extraction_confidence > 0.6:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _assess_data_completeness(self, profile: Dict[str, Any]) -> float:
        """Assess completeness of data for analysis"""
        required_fields = [
            "company_name", "founders", "problem_statement", 
            "solution_description", "market_data", "traction_metrics", "financials"
        ]
        
        complete_fields = 0
        for field in required_fields:
            if profile.get(field) and profile[field] != "":
                complete_fields += 1
        
        return complete_fields / len(required_fields)
