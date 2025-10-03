# Mirow Delivery Analysis Template

A clean, structured template for creating analysis microservices that integrate with the Mirow Delivery orchestrator.

## What You Get

- **Clean separation** between infrastructure and analysis logic
- **Standard API** that works with the orchestrator
- **Easy customization** - data scientists only edit 4 files
- **Ready to deploy** with Docker and Railway

## Architecture

The template follows a 3-step process:

1. **Preparation** (handled by `app.py`):
   - Receives input files via API upload
   - Receives parameters via API
   - Stores files in `inputs/{job_id}/` folder
   - Stores parameters in `inputs/{job_id}/parameters.json`

2. **Execution** (implemented in `run.py`):
   - Data scientist implements analysis logic
   - Receives input file paths and parameters as arguments
   - Saves results to `outputs/{job_id}/` folder
   - Can use `processing/{job_id}/` for temporary files

3. **Returning** (handled by `app.py`):
   - Collects output files from `outputs/{job_id}/`
   - Returns results and file list via API
   - Provides download endpoints for output files

## How to Use

1. **Copy this folder** for your new analysis service
2. **Customize `files.py`** with your file definitions
3. **Customize `parameters.py`** with your parameter definitions
4. **Implement `analysis/run.py`** with your analysis logic
5. **Add utility functions** to `analysis/src/utils.py` and other helper files in `analysis/src/`
6. **Add dependencies** to `requirements.txt`
7. **Deploy to Railway**

## Quick Start

```bash
# Local development
pip install -r requirements.txt
python app.py

# Docker
docker build -t my-analysis .
docker run -p 8000:8000 my-analysis

# Test
curl http://localhost:8000/info
```

## Customize Your Analysis

### 1. Define Files (`files.py`)

```python
# Input files
DATA = {
    "type": "input",
    "basename": "data",
    "required": True,
    "extension": ".csv",
    "description": "Main data file with delivery information"
}

CONFIG = {
    "type": "input",
    "basename": "config",
    "required": True,
    "extension": ".json",
    "description": "Configuration file with analysis parameters"
}

# Output files
RESULTS = {
    "type": "output",
    "basename": "results",
    "required": True,
    "extension": ".json",
    "description": "Analysis results and KPIs"
}
```

### 2. Define Parameters (`parameters.py`)

```python
ANALYSIS_TYPE = {
    "basename": "analysis_type",
    "type": "string",
    "enum": ["delivery_time", "route_optimization"],
    "description": "Type of analysis to perform",
    "required": True
}

DATE_RANGE = {
    "basename": "date_range",
    "type": "string",
    "enum": ["last_7_days", "last_30_days"],
    "description": "Date range for analysis",
    "required": True
}
```

### 3. Implement Analysis Logic (`analysis/run.py`)

```python
def run_analysis(
    input_files: Dict[str, str],
    parameters: Dict[str, Any],
    output_files: Dict[str, str],
    processing_files: Dict[str, str],
    progress_callback=None
) -> Dict[str, Any]:
    # Read input data
    data_file = input_files.get("data.csv")
    data_df = pd.read_csv(data_file)
    
    # Your analysis logic here
    results = {
        "total_deliveries": len(data_df),
        "avg_delivery_time": data_df['delivery_time'].mean(),
        "success_rate": (data_df['status'] == 'delivered').mean() * 100
    }
    
    # Save results using output file paths
    results_file = output_files.get("results.json")
    json.dump(results, open(results_file, 'w'))
    
    return results
```

### 4. Add Utility Functions (`analysis/src/utils.py`)

```python
# Add your utility functions here
def calculate_metrics(df):
    return {
        "avg_time": df['delivery_time'].mean(),
        "success_rate": (df['status'] == 'delivered').mean()
    }

def generate_insights(metrics):
    insights = []
    if metrics['avg_time'] > 30:
        insights.append("Delivery time is too high")
    return insights
```

### 5. Use Utilities in Your Analysis (`analysis/run.py`)

```python
from analysis.src.utils import calculate_metrics, generate_insights

def run_analysis(input_files, parameters, output_files, processing_files, progress_callback=None):
    # Read data
    data_file = input_files.get("data.csv")
    data_df = pd.read_csv(data_file)
    
    # Use your utility functions
    metrics = calculate_metrics(data_df)
    insights = generate_insights(metrics)
    
    # Your analysis logic here
    results = {**metrics, "insights": insights}
    
    # Save results using output file paths
    results_file = output_files.get("results.json")
    json.dump(results, open(results_file, 'w'))
    
    return results
```

## File I/O Made Simple

Files are automatically handled by the infrastructure:

```python
def run_analysis(input_files, parameters, output_files, processing_files, progress_callback=None):
    # Read input files
    data_file = input_files.get("data.csv")
    data_df = pd.read_csv(data_file)
    
    # Access parameters
    analysis_type = parameters.get("analysis_type")
    
    # Save output files
    results_file = output_files.get("results.json")
    json.dump(results, open(results_file, 'w'))
    
    return results
```

## Environment Configuration

Create a `.env` file for local development:

```bash
# Copy the example
cp env.example .env

# Edit for local development
LOCAL_DATA_PATH=./data
LOCAL_OUTPUT_PATH=./outputs
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check  
- `GET /info` - Analysis metadata (used by orchestrator)
- `POST /analyze` - Submit job
- `GET /status/{job_id}` - Check status
- `GET /results/{job_id}` - Get results
- `DELETE /jobs/{job_id}` - Cancel job

## Deployment

The template is ready for Railway deployment. The orchestrator will automatically discover your service and make it available to users.

## File Structure

```
mirow-delivery-analysis-template/
├── app.py                 # Railway infrastructure (don't modify)
├── files.py               # File definitions (customize this)
├── parameters.py          # Parameter definitions (customize this)
├── analysis/              # Data scientist's workspace
│   ├── run.py             # Your analysis logic (implement this)
│   └── src/               # Your utility functions
│       ├── __init__.py
│       ├── utils.py       # Add your utility functions here
│       └── ...            # Add other helper files as needed
├── requirements.txt       # Dependencies
├── Dockerfile            # Container configuration
└── README.md             # This file
```

## Benefits

- **API-based file transfer** - no shared volumes needed
- **Simple structure** - only modify `files.py`, `parameters.py`, and `analysis/` folder
- **Clean slate** - `analysis/src/utils.py` is empty, add your own functions
- **No infrastructure complexity** - file handling done automatically
- **Clean separation** - focus on analysis logic only
- **Standard interface** - works with orchestrator out of the box
- **Easy testing** - local development with simple file paths
- **Scalable** - each analysis runs as independent service

That's it! 🎉

