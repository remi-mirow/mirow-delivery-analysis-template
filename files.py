"""
File definitions for the analysis.

Data scientists define their input and output files here.
"""

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

def get_all_input_files():
    """Get all input file definitions"""
    return [DATA, CONFIG, ADDITIONAL_DATA, REFERENCE]

def get_all_output_files():
    """Get all output file definitions"""
    return [RESULTS, PROCESSED_DATA, INSIGHTS]
