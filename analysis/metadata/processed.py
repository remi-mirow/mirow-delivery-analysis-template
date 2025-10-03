"""
Processed file metadata for the analysis.

Data scientists define their processed/temporary files here.
"""

import os
from pathlib import Path

# Directory derived from DATA_DIR environment variable
DATA_DIR = Path(os.getenv("DATA_DIR", "./analysis/data"))
PROCESSED_DIR = DATA_DIR / "processed"

def get_processed_files(job_id: str):
    """Get processed files with full paths for a job"""
    return {
        "temp_data": {
            "dtype": "csv",
            "name": "temp_data.csv",
            "description": "Temporary data file for processing",
            "path": str(PROCESSED_DIR / job_id / "temp_data.csv"),
            "required": False
        },
        "temp_results": {
            "dtype": "json",
            "name": "temp_results.json",
            "description": "Temporary results file for processing",
            "path": str(PROCESSED_DIR / job_id / "temp_results.json"),
            "required": False
        }
    }
