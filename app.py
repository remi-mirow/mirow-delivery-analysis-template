"""
Analysis Service - FastAPI web service implementing 3-step workflow:

1. Receive files from orchestrator API and store in inputs folder
2. Execute run() in analysis 
3. Extract outputs and return files
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import uvicorn
import os
import aiofiles
from pathlib import Path

# Analysis imports
from analysis.run import run_analysis
from analysis.metadata.inputs import get_input_files, INPUTS_DIR
from analysis.metadata.outputs import get_output_files, OUTPUTS_DIR

# Models
class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    output_files: Optional[List[Dict[str, Any]]] = None

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
    files: List[UploadFile] = File(...)
):
    """
    Start analysis with uploaded files.
    
    Args:
        files: List of uploaded input files
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Store job
        jobs[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Job submitted"
        }
        
        # Start processing
        asyncio.create_task(process_job(job_id, files))
        
        return AnalysisResponse(
            job_id=job_id,
            status="pending", 
            message="Job submitted"
        )
        
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
        output_files=job.get("output_files")
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
    output_path = OUTPUTS_DIR / job_id / filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(output_path)

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    jobs[job_id]["status"] = "cancelled"
    return {"message": "Job cancelled"}

async def process_job(job_id: str, files: List[UploadFile]):
    """
    Process analysis job using the 3-step workflow:
    1. Store input files
    2. Execute analysis
    3. Extract outputs
    """
    job = jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = "Starting analysis workflow..."
        
        # Step 1: Store input files
        await step1_store_files(job_id, files)
        
        # Step 2: Execute analysis
        await step2_execute_analysis(job_id)
        
        # Step 3: Extract outputs
        output_files = await step3_extract_outputs(job_id)
        
        # Update job status
        job["status"] = "completed"
        job["message"] = "Analysis completed successfully"
        job["output_files"] = output_files
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"Analysis failed: {str(e)}"

async def step1_store_files(job_id: str, files: List[UploadFile]):
    """Step 1: Store uploaded files in inputs folder"""
    job = jobs[job_id]
    job["message"] = "Storing input files..."
    job["progress"] = 0.1
    
    # Create job directory
    job_input_dir = INPUTS_DIR / job_id
    job_input_dir.mkdir(parents=True, exist_ok=True)
    
    # Store files
    for file in files:
        file_path = job_input_dir / file.filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        print(f"Stored file: {file.filename}")
    
    job["progress"] = 0.3
    job["message"] = "Input files stored"

async def step2_execute_analysis(job_id: str):
    """Step 2: Execute run() in analysis"""
    job = jobs[job_id]
    job["message"] = "Executing analysis..."
    job["progress"] = 0.3
    
    # Progress callback
    def progress_callback(progress: float, message: str):
        # Map analysis progress (0-1) to job progress (0.3-0.9)
        job_progress = 0.3 + (progress * 0.6)
        job["progress"] = job_progress
        job["message"] = message
        print(f"Progress: {job_progress:.1%} - {message}")
    
    # Run the analysis
    status = run_analysis(job_id, progress_callback=progress_callback)
    
    if status != "completed":
        raise Exception(f"Analysis failed with status: {status}")
    
    job["progress"] = 0.9
    job["message"] = "Analysis completed"

async def step3_extract_outputs(job_id: str) -> List[Dict[str, Any]]:
    """Step 3: Extract output files"""
    job = jobs[job_id]
    job["message"] = "Extracting outputs..."
    job["progress"] = 0.9
    
    # Collect output files using metadata
    output_files = []
    all_output_metadata = get_output_files(job_id)
    for file_key, file_info in all_output_metadata.items():
        file_path = Path(file_info["path"])
        if file_path.exists():
            output_files.append({
                "key": file_key,
                "filename": file_info["name"],
                "dtype": file_info["dtype"],
                "description": file_info["description"],
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "required": file_info.get("required", False)
            })
    
    job["progress"] = 1.0
    job["message"] = "Outputs extracted"
    
    return output_files

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