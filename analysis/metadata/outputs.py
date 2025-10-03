"""
Output file metadata for the analysis.

Data scientists define their output files here.
"""

import os
from pathlib import Path

# Directory derived from DATA_DIR environment variable
DATA_DIR = Path(os.getenv("DATA_DIR", "./analysis/data"))
OUTPUTS_DIR = DATA_DIR / "outputs"

def get_output_files(job_id: str):
    """Get output files with full paths for a job"""
    return {
        "output1": {
            "dtype": "xlsx",
            "name": "output1.xlsx",
            "description": "First processed file saved as XLSX",
            "path": str(OUTPUTS_DIR / job_id / "output1.xlsx"),
            "required": True
        },
        "output2": {
            "dtype": "xlsx",
            "name": "output2.xlsx", 
            "description": "Second processed file saved as XLSX",
            "path": str(OUTPUTS_DIR / job_id / "output2.xlsx"),
            "required": True
        }
    }
