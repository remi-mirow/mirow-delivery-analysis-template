# Mirow Delivery Analysis Template

A clean, structured template for creating analysis microservices that integrate with the Mirow Delivery orchestrator.

## What You Get

- **Clean separation** between infrastructure and analysis logic
- **Standard API** that works with the orchestrator
- **Easy customization** - data scientists only edit 4 files
- **Ready to deploy** with Docker and Railway

## Architecture

The template follows a **3-step workflow** orchestrated by a `main()` function:

1. **Step 1: Receive Files** (handled by `main.py`):
   - Receives all files from orchestrator API
   - Stores files in `inputs/{job_id}/` folder
   - Stores parameters in `inputs/{job_id}/parameters.yaml` (YAML format for easy editing)

2. **Step 2: Execute Analysis** (implemented in `analysis/run.py`):
   - Data scientist implements analysis logic
   - Reads input files and parameters from configured paths
   - Saves results to `outputs/{job_id}/` folder
   - Saves KPIs to `outputs/{job_id}/kpis.yaml`

3. **Step 3: Extract Outputs** (handled by `main.py`):
   - Collects all output files from `outputs/{job_id}/`
   - Returns files and KPIs to orchestrator
   - Provides structured results with metadata

## How to Use

1. **Copy this folder** for your new analysis service
2. **Configure `analysis/config.py`** with your file paths and settings
3. **Implement `analysis/run.py`** with your analysis logic
4. **Add utility functions** to `analysis/src/utils.py` and other helper files in `analysis/src/`
5. **Add dependencies** to `requirements.txt`
6. **Deploy to Railway**

### For Data Scientists

**Only 2 files to edit:**
- `analysis/config.py` - Configure input/output file paths
- `analysis/run.py` - Implement your analysis logic

See `analysis/README.md` for detailed configuration guide.

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

### 1. Configure Files (`analysis/config/`)

**Input files** (`analysis/config/inputs.py`):
```python
INPUT_FILES = {
    "file1": {
        "dtype": "csv",
        "name": "file1.csv",
        "description": "First CSV input file",
        "path": "file1.csv",
        "required": True
    },
    "file2": {
        "dtype": "csv",
        "name": "file2.csv",
        "description": "Second CSV input file", 
        "path": "file2.csv",
        "required": True
    }
}
```

**Output files** (`analysis/config/outputs.py`):
```python
OUTPUT_FILES = {
    "output1": {
        "dtype": "xlsx",
        "name": "output1.xlsx",
        "description": "First processed file saved as XLSX",
        "path": "output1.xlsx",
        "required": True
    },
    "output2": {
        "dtype": "xlsx",
        "name": "output2.xlsx",
        "description": "Second processed file saved as XLSX",
        "path": "output2.xlsx",
        "required": True
    }
}
```

### 2. Define Parameters (`analysis/config/parameters.py`)

```python
MULTIPLIER = {
    "basename": "multiplier",
    "type": "number",
    "description": "Number to multiply by 2",
    "required": True,
    "default": 1
}
```

### 3. Implement Analysis (`analysis/run.py`)

```python
def run_analysis(input_files, parameters, output_files, processing_files, progress_callback):
    # Load 2 CSV files
    df1 = pd.read_csv(input_files["file1"])
    df2 = pd.read_csv(input_files["file2"])
    
    # Get parameter and calculate result
    multiplier = parameters.get('multiplier', 1)
    result = 2 * multiplier
    
    # Save as XLSX files
    df1.to_excel(output_files["output1"], index=False)
    df2.to_excel(output_files["output2"], index=False)
    
    # Save KPIs
    kpis = {"multiplier": multiplier, "result": result}
    with open(output_files["kpis"], 'w') as f:
        yaml.dump(kpis, f)
    
    return {"multiplier": multiplier, "result": result}
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

