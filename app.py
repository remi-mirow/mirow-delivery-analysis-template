from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import uvicorn
import json
import os
from pathlib import Path

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

app = FastAPI(title="Simple Analysis Service")

@app.get("/")
async def root():
    return {"name": "Simple Analysis Service", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/info")
async def info():
    return {
        "name": "Simple Analysis Service",
        "version": "1.0.0",
        "input_requirements": {"file_types": [".pdf", ".txt", ".docx"]},
        "config_schema": {"parameter1": "string", "parameter2": "number"}
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    job_id = request.job_id
    
    # Check if input directory exists
    if not os.path.exists(request.input_path):
        raise HTTPException(status_code=400, detail="Input directory not found")
    
    # Load config from input directory
    config_file = Path(request.input_path) / "config.json"
    config = {}
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    
    # Get list of input files
    input_files = []
    for file_path in Path(request.input_path).iterdir():
        if file_path.is_file() and file_path.name != "config.json":
            input_files.append(str(file_path))
    
    # Store job
    jobs[job_id] = {
        "status": "pending",
        "input_path": request.input_path,
        "input_files": input_files,
        "config": config,
        "progress": 0.0
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

# YOUR ANALYSIS LOGIC GOES HERE
async def process_job(job_id: str):
    """Replace this function with your actual analysis logic"""
    job = jobs[job_id]
    
    try:
        job["status"] = "running"
        
        # Simulate processing (replace with your analysis)
        for i in range(5):
            if job["status"] == "cancelled":
                return
            
            await asyncio.sleep(1)  # Replace with actual work
            job["progress"] = (i + 1) / 5
        
         # Save results to shared volume outputs directory
         shared_path = os.getenv("SHARED_VOLUME_PATH", "/shared-files")
         output_dir = Path(shared_path) / "outputs" / f"job-{job_id}"
         output_dir.mkdir(parents=True, exist_ok=True)
         
         # Your analysis results
         results = {
             "analysis_type": "example",
             "documents_processed": len(job["input_files"]),
             "config_used": job["config"],
             "findings": ["result1", "result2", "result3"],
             "files_analyzed": [os.path.basename(f) for f in job["input_files"]]
         }
         
         # Save results.json to outputs directory
         results_file = output_dir / "results.json"
         with open(results_file, 'w') as f:
             json.dump(results, f, indent=2)
         
         # Example: Create additional output file
         summary_file = output_dir / "analysis_summary.txt"
         with open(summary_file, 'w') as f:
             f.write(f"Analysis completed for {len(job['input_files'])} files\n")
             f.write(f"Configuration: {job['config']}\n")
             f.write("Findings:\n")
             for finding in results["findings"]:
                 f.write(f"- {finding}\n")
         
         job["results"] = results
        
        job["status"] = "completed"
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
