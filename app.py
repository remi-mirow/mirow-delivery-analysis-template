from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import uvicorn
import json
import os
from pathlib import Path
try:
    from analysis.run import run_analysis
    from analysis.metadata.inputs import get_input_files
    from analysis.metadata.outputs import get_output_files
    from main import main as analysis_main
    print("All imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    raise

# Models
class AnalysisRequest(BaseModel):
    job_id: str
    parameters: Dict[str, Any]

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    results: Optional[Dict[str, Any]] = None

# Simple in-memory storage
jobs = {}

app = FastAPI(title="Analysis Service")

@app.get("/")
async def root():
    return {
        "name": "Analysis Service", 
        "version": "1.0.0", 
        "status": "running"
    }

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "analysis",
        "version": "1.0.0",
        "timestamp": "2025-01-02T21:18:00Z"
    }
    print(f"🏥 Health check requested - Status: {health_status}")
    return health_status

@app.get("/info")
async def info():
    """Get analysis metadata and requirements - used by orchestrator for discovery"""
    return {
        "name": "Analysis Service",
        "version": "1.0.0",
        "description": "A simple analysis service that processes 2 CSV files",
        "input_files": get_input_files("example")
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    files: List[UploadFile] = File(...),
    parameters: str = Form(...)
):
    """
    Start analysis with uploaded files and parameters.
    
    Args:
        files: List of uploaded input files
        parameters: JSON string with analysis parameters
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Parse parameters
        params = json.loads(parameters)
        
        # Store job
        jobs[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Job submitted"
        }
        
        # Start processing
        asyncio.create_task(process_job(job_id, files, params))
        
        return AnalysisResponse(
            job_id=job_id,
            status="pending", 
            message="Job submitted"
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid parameters JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress"),
        results=job.get("results")
    )

@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """Get analysis results and output files"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # Return results and list of output files
    return {
        "job_id": job_id, 
        "results": job["results"],
        "output_files": job.get("output_files", [])
    }

@app.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    """Download an output file"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # Get output file path
    output_path = Path("outputs") / job_id / filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(output_path)

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    jobs[job_id]["status"] = "cancelled"
    return {"message": "Job cancelled"}

async def process_job(job_id: str, files: List[UploadFile], parameters: Dict[str, Any]):
    """
    Process analysis job using the new 3-step workflow.
    
    This function now uses the main() orchestrator function.
    """
    job = jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = "Starting analysis workflow..."
        
        # Get orchestrator URL from environment
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8001")
        
        # Use the new main() function for the 3-step workflow
        result = await analysis_main(orchestrator_url, job_id)
        
        # Update job status based on result
        job["status"] = result["status"]
        job["message"] = result.get("message", "Analysis completed")
        
        if result["status"] == "completed":
            job["output_files"] = result["output_files"]
        else:
            job["error"] = result.get("error", "Unknown error")
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"Analysis failed: {str(e)}"

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting Analysis Service on port {port}")
    print(f"🏥 Health check endpoint: http://0.0.0.0:{port}/health")
    print(f"📊 Info endpoint: http://0.0.0.0:{port}/info")
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        access_log=True
    )
