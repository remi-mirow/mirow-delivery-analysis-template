from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import uvicorn
import json
import os
from pathlib import Path
from analysis.run import run_analysis
from files import get_all_input_files, get_all_output_files
from parameters import get_all_parameters

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
async def health():
    return {"status": "healthy"}

@app.get("/info")
async def info():
    """Get analysis metadata and requirements - used by orchestrator for discovery"""
    return {
        "name": "Analysis Service",
        "version": "1.0.0",
        "description": "A sample analysis service",
        "input_files": get_all_input_files(),
        "input_parameters": get_all_parameters()
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
    Process analysis job - handles file preparation and execution.
    
    This function handles the infrastructure complexity.
    Data scientists implement their logic in run_analysis()
    """
    job = jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = "Preparing files..."
        
        # 1. PREPARATION: Store input files and parameters
        input_dir = Path("inputs") / job_id
        output_dir = Path("outputs") / job_id
        processing_dir = Path("processing") / job_id
        
        # Create directories
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        processing_dir.mkdir(parents=True, exist_ok=True)
        
        # Store uploaded files
        input_files = {}
        for file in files:
            file_path = input_dir / file.filename
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            input_files[file.filename] = str(file_path)
        
        # Store parameters
        params_file = input_dir / "parameters.json"
        with open(params_file, "w") as f:
            json.dump(parameters, f, indent=2)
        
        job["message"] = "Running analysis..."
        
        # 2. EXECUTION: Call data scientist's run function
        def progress_callback(progress: float, message: str):
            job["progress"] = progress
            job["message"] = message
        
        # Prepare output and processing file paths
        output_files = {
            "results.json": str(output_dir / "results.json"),
            "processed_data.csv": str(output_dir / "processed_data.csv"),
            "insights.txt": str(output_dir / "insights.txt")
        }
        
        processing_files = {
            "temp_data.csv": str(processing_dir / "temp_data.csv"),
            "temp_results.json": str(processing_dir / "temp_results.json")
        }
        
        # Run the analysis with file paths and parameters
        results = run_analysis(
            input_files=input_files,
            parameters=parameters,
            output_files=output_files,
            processing_files=processing_files,
            progress_callback=progress_callback
        )
        
        # 3. RETURNING: Collect output files
        output_file_list = []
        if output_dir.exists():
            for file_path in output_dir.iterdir():
                if file_path.is_file():
                    output_file_list.append(file_path.name)
        
        # Store results
        job["results"] = results
        job["output_files"] = output_file_list
        job["status"] = "completed"
        job["message"] = "Analysis completed successfully"
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"Analysis failed: {str(e)}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
