# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import os
import aiofiles
from orchestrator.workflow_manager import WorkflowManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Project Athena - AI Startup Analysis", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow manager
PROJECT_ID = "project-drishti-466708"
REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
workflow_manager = WorkflowManager(PROJECT_ID, REGION)

# Data models
class AnalysisSubmission(BaseModel):
    company_name: Optional[str] = None
    contact_email: Optional[str] = None
    additional_notes: Optional[str] = None

class AnalysisResponse(BaseModel):
    submission_id: str
    status: str
    message: str

@app.post("/api/v1/analyze/upload", response_model=AnalysisResponse)
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = None
):
    """Upload file and start analysis"""
    
    # Validate file type
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'audio/mpeg', 'audio/wav']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not supported"
        )
    
    # Generate submission ID
    submission_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
    file_path = f"{upload_dir}/{submission_id}.{file_extension}"
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Parse metadata
    metadata_dict = {}
    if metadata:
        try:
            import json
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            pass
    
    # Start background analysis
    background_tasks.add_task(
        workflow_manager.process_startup_submission,
        submission_id,
        file_path,
        file_extension,
        metadata_dict
    )
    
    logger.info(f"Started analysis for submission {submission_id}")
    
    return AnalysisResponse(
        submission_id=submission_id,
        status="processing",
        message="Analysis started successfully"
    )

@app.get("/api/v1/analyze/{submission_id}/status")
async def get_analysis_status(submission_id: str):
    """Get analysis status"""
    status = await workflow_manager.get_analysis_status(submission_id)
    return status

@app.get("/api/v1/analyze/{submission_id}/results")
async def get_analysis_results(submission_id: str):
    """Get complete analysis results"""
    status = await workflow_manager.get_analysis_status(submission_id)
    
    if status.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {status.get('status', 'unknown')}"
        )
    
    # Return sanitized results (remove internal processing data)
    final_analysis = status.get("final_analysis", {})
    enriched_profile = status.get("enriched_profile", {})
    
    return {
        "submission_id": submission_id,
        "company_name": enriched_profile.get("company_name", "Unknown"),
        "investment_memo": final_analysis.get("investment_memo", ""),
        "recommendation": final_analysis.get("recommendation", {}),
        "investment_score": final_analysis.get("investment_score", {}),
        "swot_analysis": final_analysis.get("swot_analysis", {}),
        "executive_summary": final_analysis.get("executive_summary", ""),
        "analysis_metadata": final_analysis.get("analysis_metadata", {})
    }

@app.get("/api/v1/analyses/recent")
async def list_recent_analyses(limit: int = 20):
    """List recent analyses"""
    analyses = await workflow_manager.list_recent_analyses(limit)
    return {"analyses": analyses}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "athena-ai-analyst"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
