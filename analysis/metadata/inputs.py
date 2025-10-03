"""
Input file metadata for the analysis.

Data scientists define their input files here.
"""

import os
from pathlib import Path

# Directory derived from DATA_DIR environment variable
DATA_DIR = Path(os.getenv("DATA_DIR", "./analysis/data"))
INPUTS_DIR = DATA_DIR / "inputs"

def get_input_files(job_id: str):
    """Get input files with full paths for a job"""
    return {
        "file1": {
            "dtype": "csv",
            "name": "file1.csv",
            "description": "First CSV input file",
            "path": str(INPUTS_DIR / job_id / "file1.csv"),
            "required": True
        },
        "file2": {
            "dtype": "csv",
            "name": "file2.csv", 
            "description": "Second CSV input file",
            "path": str(INPUTS_DIR / job_id / "file2.csv"),
            "required": True
        }
    }
