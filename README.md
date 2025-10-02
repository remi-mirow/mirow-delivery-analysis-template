# Simple Analysis Service

A minimal FastAPI service template for analysis microservices.

## What You Get

- **Single file** (`app.py`) with everything you need
- **Standard API** that works with the orchestrator
- **Ready to deploy** with Docker

## How to Use

1. **Copy this folder** for your new service
2. **Edit the `process_job()` function** in `app.py` with your analysis logic
3. **Add dependencies** to `requirements.txt`
4. **Deploy**

## Quick Start

```bash
# Local development
pip install -r requirements.txt
python app.py

# Docker
docker build -t my-analysis .
docker run -p 8000:8000 my-analysis

# Test
curl http://localhost:8000/
```

## Customize Your Analysis

Replace the `process_job()` function with your logic:

```python
async def process_job(job_id: str):
    job = jobs[job_id]
    
    try:
        job["status"] = "running"
        
        # YOUR ANALYSIS CODE HERE
        documents = job["documents"]
        config = job["config"]
        
        # Example: Process each document
        results = []
        for i, doc in enumerate(documents):
            # Do your analysis on 'doc'
            result = your_analysis_function(doc, config)
            results.append(result)
            
            # Update progress
            job["progress"] = (i + 1) / len(documents)
        
        # Store results
        job["results"] = {
            "analysis_results": results,
            "summary": "Your analysis summary"
        }
        
        job["status"] = "completed"
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check  
- `POST /analyze` - Submit job
- `GET /status/{job_id}` - Check status
- `GET /results/{job_id}` - Get results
- `DELETE /jobs/{job_id}` - Cancel job

That's it! 🎉

