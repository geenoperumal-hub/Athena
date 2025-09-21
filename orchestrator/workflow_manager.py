# orchestrator/workflow_manager.py
import asyncio
from typing import Dict, Any, List
from agents.scribe_agent import ScribeAgent
from agents.librarian_agent import LibrarianAgent
from agents.scout_agent import ScoutAgent
from agents.quant_agent import QuantAgent
from agents.skeptic_agent import SkepticAgent
from agents.analyst_agent import AnalystAgent
from utils.gcp_clients import GCPClients
from google.cloud import firestore
import json
from datetime import datetime

class WorkflowManager:
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        
        # Initialize GCP clients
        self.gcp_clients = GCPClients(project_id, region)
        
        # Initialize agents
        self.scribe = ScribeAgent(project_id, region)
        self.librarian = LibrarianAgent(project_id, region)
        self.scout = ScoutAgent(project_id, region)
        self.quant = QuantAgent(project_id, region, self.gcp_clients.bq_client)
        self.skeptic = SkepticAgent(project_id, region)
        self.analyst = AnalystAgent(project_id, region)
        
        # Firestore for state management
        self.db = firestore.Client(project=project_id)
    
    async def process_startup_submission(self, submission_id: str, 
                                       file_path: str, file_type: str,
                                       metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main orchestration workflow"""
        
        # Initialize analysis state
        analysis_state = {
            "submission_id": submission_id,
            "status": "processing",
            "current_stage": "ingestion",
            "started_at": datetime.utcnow().isoformat(),
            "file_path": file_path,
            "file_type": file_type,
            "metadata": metadata or {}
        }
        
        # Save initial state
        await self._save_analysis_state(submission_id, analysis_state)
        
        try:
            # Stage 1: Ingestion (Scribe Agent)
            print(f"Stage 1: Processing document - {file_path}")
            analysis_state["current_stage"] = "ingestion"
            await self._save_analysis_state(submission_id, analysis_state)
            
            ingestion_result = await self.scribe.process_document(file_path, file_type)
            analysis_state["ingestion_result"] = ingestion_result
            
            # Stage 2: Data Extraction (Librarian Agent)
            print("Stage 2: Extracting structured data")
            analysis_state["current_stage"] = "extraction"
            await self._save_analysis_state(submission_id, analysis_state)
            
            cleaned_text = ingestion_result.get("cleaned_text", "")
            startup_profile = await self.librarian.extract_structured_data(cleaned_text)
            analysis_state["startup_profile"] = startup_profile
            
            # Stage 3: Data Enrichment (Scout Agent)
            print("Stage 3: Enriching with external data")
            analysis_state["current_stage"] = "enrichment"
            await self._save_analysis_state(submission_id, analysis_state)
            
            enriched_profile = await self.scout.enrich_startup_data(startup_profile)
            analysis_state["enriched_profile"] = enriched_profile
            
            # Stage 4: Quantitative Analysis (Quant Agent)
            print("Stage 4: Performing quantitative analysis")
            analysis_state["current_stage"] = "quantitative_analysis"
            await self._save_analysis_state(submission_id, analysis_state)
            
            quant_analysis = await self.quant.benchmark_startup(enriched_profile)
            analysis_state["quant_analysis"] = quant_analysis
            
            # Stage 5: Risk Analysis (Skeptic Agent)
            print("Stage 5: Analyzing risks")
            analysis_state["current_stage"] = "risk_analysis"
            await self._save_analysis_state(submission_id, analysis_state)
            
            risk_analysis = await self.skeptic.analyze_risks(enriched_profile, quant_analysis)
            analysis_state["risk_analysis"] = risk_analysis
            
            # Stage 6: Final Synthesis (Analyst Agent)
            print("Stage 6: Generating final analysis")
            analysis_state["current_stage"] = "synthesis"
            await self._save_analysis_state(submission_id, analysis_state)
            
            final_analysis = await self.analyst.synthesize_analysis(
                enriched_profile, quant_analysis, risk_analysis
            )
            analysis_state["final_analysis"] = final_analysis
            
            # Complete the analysis
            analysis_state["status"] = "completed"
            analysis_state["current_stage"] = "completed"
            analysis_state["completed_at"] = datetime.utcnow().isoformat()
            
            # Save to BigQuery for historical analysis
            await self._save_to_bigquery(submission_id, analysis_state)
            
            # Final state save
            await self._save_analysis_state(submission_id, analysis_state)
            
            print(f"Analysis completed for {submission_id}")
            
            return {
                "submission_id": submission_id,
                "status": "completed",
                "startup_profile": enriched_profile,
                "investment_memo": final_analysis["investment_memo"],
                "recommendation": final_analysis["recommendation"],
                "investment_score": final_analysis["investment_score"],
                "risk_assessment": risk_analysis,
                "analysis_metadata": final_analysis["analysis_metadata"]
            }
            
        except Exception as e:
            print(f"Error in workflow: {str(e)}")
            analysis_state["status"] = "error"
            analysis_state["error"] = str(e)
            analysis_state["failed_at"] = datetime.utcnow().isoformat()
            await self._save_analysis_state(submission_id, analysis_state)
            
            raise e
    
    async def _save_analysis_state(self, submission_id: str, state: Dict[str, Any]):
        """Save analysis state to Firestore"""
        doc_ref = self.db.collection("analysis_states").document(submission_id)
        doc_ref.set(state, merge=True)
    
    async def _save_to_bigquery(self, submission_id: str, analysis_state: Dict[str, Any]):
        """Save completed analysis to BigQuery for historical data"""
        
        # Extract data for startup_profiles table
        enriched_profile = analysis_state.get("enriched_profile", {})
        final_analysis = analysis_state.get("final_analysis", {})
        
        startup_row = {
            "startup_id": submission_id,
            "company_name": enriched_profile.get("company_name", ""),
            "founders": enriched_profile.get("founders", []),
            "problem_statement": enriched_profile.get("problem_statement", ""),
            "solution_description": enriched_profile.get("solution_description", ""),
            "market_data": enriched_profile.get("market_data", {}),
            "traction_metrics": enriched_profile.get("traction_metrics", {}),
            "financials": enriched_profile.get("financials", {}),
            "created_at": analysis_state.get("started_at"),
            "updated_at": analysis_state.get("completed_at")
        }
        
        # Insert into BigQuery
        table_id = f"{self.project_id}.athena_data.startup_profiles"
        errors = self.gcp_clients.bq_client.insert_rows_json(
            self.gcp_clients.bq_client.get_table(table_id), [startup_row]
        )
        
        if errors:
            print(f"Error inserting to BigQuery: {errors}")
    
    async def get_analysis_status(self, submission_id: str) -> Dict[str, Any]:
        """Get current analysis status"""
        doc_ref = self.db.collection("analysis_states").document(submission_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            return {"status": "not_found"}
    
    async def list_recent_analyses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent analyses"""
        docs = (
            self.db.collection("analysis_states")
            .order_by("started_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        
        analyses = []
        for doc in docs:
            data = doc.to_dict()
            analyses.append({
                "submission_id": doc.id,
                "company_name": data.get("startup_profile", {}).get("company_name", "Unknown"),
                "status": data.get("status", "unknown"),
                "started_at": data.get("started_at"),
                "recommendation": data.get("final_analysis", {}).get("recommendation", {}).get("decision", "Pending")
            })
        
        return analyses
