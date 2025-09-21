# agents/quant_agent.py
import pandas as pd
from typing import Dict, Any, List
from google.cloud import bigquery
import numpy as np
import vertexai
from vertexai.generative_models import GenerativeModel

class QuantAgent:
    def __init__(self, project_id: str, region: str, bq_client: bigquery.Client):
        self.project_id = project_id
        self.bq_client = bq_client
        vertexai.init(project=project_id, location=region)
        self.gemini_model = GenerativeModel("gemini-1.5-pro")
    
    async def benchmark_startup(self, enriched_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Benchmark startup against historical data"""
        
        # Determine startup stage and sector
        stage = self._determine_stage(enriched_profile)
        sector = self._determine_sector(enriched_profile)
        
        # Get benchmark data from BigQuery
        benchmark_data = await self._get_benchmark_data(sector, stage)
        
        # Calculate percentile rankings
        metrics_benchmarks = await self._calculate_percentile_rankings(
            enriched_profile, benchmark_data
        )
        
        # Generate quantitative analysis
        quant_analysis = await self._generate_quantitative_analysis(
            enriched_profile, metrics_benchmarks
        )
        
        return {
            "stage": stage,
            "sector": sector,
            "benchmark_data": benchmark_data,
            "percentile_rankings": metrics_benchmarks,
            "quantitative_analysis": quant_analysis,
            "overall_score": await self._calculate_overall_score(metrics_benchmarks)
        }
    
    def _determine_stage(self, profile: Dict[str, Any]) -> str:
        """Determine startup stage based on metrics"""
        financials = profile.get("financials", {})
        traction = profile.get("traction_metrics", {})
        
        revenue = financials.get("revenue", 0) or 0
        funding_requested = financials.get("funding_requested", 0) or 0
        
        if revenue == 0 and funding_requested < 1000000:
            return "pre_seed"
        elif revenue < 100000 and funding_requested < 3000000:
            return "seed"
        elif revenue < 1000000:
            return "series_a"
        elif revenue < 10000000:
            return "series_b"
        else:
            return "growth"
    
    def _determine_sector(self, profile: Dict[str, Any]) -> str:
        """Determine sector using Gemini"""
        # Use AI to classify the sector based on problem/solution
        problem = profile.get("problem_statement", "")
        solution = profile.get("solution_description", "")
        
        # For now, return a default - in production, use Gemini classification
        return "b2b_saas"
    
    async def _get_benchmark_data(self, sector: str, stage: str) -> Dict[str, Any]:
        """Get benchmark data from BigQuery"""
        query = f"""
        SELECT 
            metric_name,
            p25, p50, p75, p90
        FROM `{self.project_id}.athena_data.benchmark_data`
        WHERE sector = @sector AND stage = @stage
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("sector", "STRING", sector),
                bigquery.ScalarQueryParameter("stage", "STRING", stage),
            ]
        )
        
        query_job = self.bq_client.query(query, job_config=job_config)
        results = query_job.result()
        
        benchmark_data = {}
        for row in results:
            benchmark_data[row.metric_name] = {
                "p25": row.p25,
                "p50": row.p50,
                "p75": row.p75,
                "p90": row.p90
            }
        
        # If no data found, use default benchmarks
        if not benchmark_data:
            benchmark_data = self._get_default_benchmarks(sector, stage)
        
        return benchmark_data
    
    def _get_default_benchmarks(self, sector: str, stage: str) -> Dict[str, Any]:
        """Default benchmarks for when no data is available"""
        if stage == "seed" and sector == "b2b_saas":
            return {
                "mrr_growth_rate": {"p25": 10, "p50": 20, "p75": 35, "p90": 50},
                "cac_ltv_ratio": {"p25": 2, "p50": 3, "p75": 5, "p90": 8},
                "churn_rate": {"p25": 15, "p50": 10, "p75": 7, "p90": 5},
                "burn_multiple": {"p25": 3, "p50": 2, "p75": 1.5, "p90": 1}
            }
        return {}
    
    async def _calculate_percentile_rankings(self, profile: Dict[str, Any], 
                                           benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate percentile rankings for each metric"""
        rankings = {}
        
        traction = profile.get("traction_metrics", {})
        financials = profile.get("financials", {})
        
        # Calculate key metrics
        metrics = {
            "mrr_growth_rate": self._calculate_mrr_growth(traction),
            "cac_ltv_ratio": self._calculate_cac_ltv_ratio(traction),
            "churn_rate": traction.get("churn_rate"),
            "burn_multiple": self._calculate_burn_multiple(financials, traction)
        }
        
        # Calculate percentile for each metric
        for metric_name, value in metrics.items():
            if value is not None and metric_name in benchmarks:
                percentile = self._calculate_percentile(value, benchmarks[metric_name])
                rankings[metric_name] = {
                    "value": value,
                    "percentile": percentile,
                    "benchmark": benchmarks[metric_name]
                }
        
        return rankings
    
    def _calculate_mrr_growth(self, traction: Dict) -> float:
        """Calculate MRR growth rate (mock calculation)"""
        mrr = traction.get("mrr", 0)
        if mrr > 0:
            # Mock calculation - in production, you'd need historical data
            return 20.0  # 20% monthly growth
        return None
    
    def _calculate_cac_ltv_ratio(self, traction: Dict) -> float:
        """Calculate CAC to LTV ratio"""
        cac = traction.get("cac")
        ltv = traction.get("ltv")
        
        if cac and ltv and cac > 0:
            return ltv / cac
        return None
    
    def _calculate_burn_multiple(self, financials: Dict, traction: Dict) -> float:
        """Calculate burn multiple"""
        burn_rate = financials.get("burn_rate")
        arr_growth = traction.get("arr", 0) * 0.1  # Mock ARR growth
        
        if burn_rate and arr_growth and arr_growth > 0:
            return burn_rate / arr_growth
        return None
    
    def _calculate_percentile(self, value: float, benchmark: Dict[str, float]) -> float:
        """Calculate percentile ranking against benchmark"""
        if value <= benchmark["p25"]:
            return 25
        elif value <= benchmark["p50"]:
            return 50
        elif value <= benchmark["p75"]:
            return 75
        elif value <= benchmark["p90"]:
            return 90
        else:
            return 95
    
    async def _generate_quantitative_analysis(self, profile: Dict[str, Any], 
                                            rankings: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quantitative analysis using Gemini"""
        prompt = f"""
        Analyze the following startup metrics and benchmarking data:
        
        Startup Profile:
        {json.dumps(profile.get("traction_metrics", {}), indent=2)}
        {json.dumps(profile.get("financials", {}), indent=2)}
        
        Percentile Rankings:
        {json.dumps(rankings, indent=2)}
        
        Provide analysis on:
        - Overall financial health
        - Growth trajectory assessment
        - Unit economics analysis
        - Risk factors from metrics
        - Recommendations for improvement
        
        Return as JSON with clear recommendations.
        """
        
        response = await self.gemini_model.generate_content_async(prompt)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "financial_health": "needs_analysis",
                "growth_trajectory": "unknown",
                "recommendations": []
            }
    
    async def _calculate_overall_score(self, rankings: Dict[str, Any]) -> float:
        """Calculate overall quantitative score"""
        if not rankings:
            return 0.5
        
        # Weight different metrics
        weights = {
            "mrr_growth_rate": 0.3,
            "cac_ltv_ratio": 0.3,
            "churn_rate": 0.2,
            "burn_multiple": 0.2
        }
        
        weighted_score = 0
        total_weight = 0
        
        for metric, data in rankings.items():
            if metric in weights:
                # Convert percentile to 0-1 score
                score = data["percentile"] / 100
                weighted_score += score * weights[metric]
                total_weight += weights[metric]
        
        if total_weight > 0:
            return weighted_score / total_weight
        return 0.5
