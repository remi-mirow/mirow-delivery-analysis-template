"""
File definitions for the analysis.

Data scientists define their input and output files here.
"""

import os

# Shared volume path from environment
SHARED_VOLUME_PATH = os.getenv("SHARED_VOLUME_PATH", "/shared-files")

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

ADDITIONAL_DATA = {
    "type": "input",
    "basename": "additional_data",
    "required": False,
    "extension": ".xlsx",
    "description": "Optional additional data file"
}

REFERENCE = {
    "type": "input",
    "basename": "reference",
    "required": False,
    "extension": ".json",
    "description": "Optional reference data file"
}

# Output files
RESULTS = {
    "type": "output",
    "basename": "results",
    "required": True,
    "extension": ".json",
    "description": "Analysis results and KPIs"
}

PROCESSED_DATA = {
    "type": "output",
    "basename": "processed_data",
    "required": True,
    "extension": ".csv",
    "description": "Processed data output"
}

INSIGHTS = {
    "type": "output",
    "basename": "insights",
    "required": False,
    "extension": ".txt",
    "description": "Analysis insights summary"
}

# Helper function to get file path
def get_file_path(job_id: str, file_def: dict) -> str:
    """
    Get the full path for a file based on job_id and file definition.
    
    Args:
        job_id: Unique job identifier
        file_def: File definition dictionary
        
    Returns:
        Full file path
    """
    filename = file_def["basename"] + file_def["extension"]
    return f"{SHARED_VOLUME_PATH}/{job_id}/{filename}"
