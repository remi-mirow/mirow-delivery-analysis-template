from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import uvicorn
import json
import os
from pathlib import Path
from run import run_analysis
from files import SHARED_VOLUME_PATH, DATA, CONFIG, ADDITIONAL_DATA, REFERENCE
from parameters import ANALYSIS_TYPE, DATE_RANGE, REGION, PRIORITY

# Simple models
class AnalysisRequest(BaseModel):
    job_id: str
    input_path: str  # Path to shared volume input directory
    analysis_id: Optional[int] = None

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
async def health():
    return {"status": "healthy"}

@app.get("/info")
async def info():
    """Get analysis metadata and requirements - used by orchestrator for discovery"""
    return {
        "name": "Analysis Service",
        "version": "1.0.0",
        "description": "A sample analysis service",
        "input_files": [DATA, CONFIG, ADDITIONAL_DATA, REFERENCE],
        "input_parameters": [ANALYSIS_TYPE, DATE_RANGE, REGION, PRIORITY]
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    job_id = request.job_id
    
    # Check if input directory exists
    if not os.path.exists(request.input_path):
        raise HTTPException(status_code=400, detail="Input directory not found")
    
    # Store job
    jobs[job_id] = {
        "status": "pending",
        "input_path": request.input_path,
        "progress": 0.0,
        "message": "Job submitted"
    }
    
    # Start processing
    asyncio.create_task(process_job(job_id))
    
    return AnalysisResponse(
        job_id=job_id,
        status="pending", 
        message="Job submitted"
    )

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
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    return {"job_id": job_id, "results": job["results"]}

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    jobs[job_id]["status"] = "cancelled"
    return {"message": "Job cancelled"}

async def process_job(job_id: str):
    """
    Process analysis job using the run_analysis function.
    
    This function handles the Railway infrastructure complexity.
    Data scientists implement their logic in run_analysis()
    """
    job = jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = "Analysis started"
        
        # Progress callback function
        def progress_callback(progress: float, message: str):
            job["progress"] = progress
            job["message"] = message
        
        # Run the analysis
        results = run_analysis(job_id, progress_callback)
        
        # Store results
        job["results"] = results
        job["status"] = "completed"
        job["message"] = "Analysis completed successfully"
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"Analysis failed: {str(e)}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
