"""
Parameter definitions for the analysis.

Data scientists define their input parameters here.
"""

# Input parameters
ANALYSIS_TYPE = {
    "basename": "analysis_type",
    "type": "string",
    "enum": ["delivery_time", "route_optimization", "cost_analysis"],
    "description": "Type of analysis to perform",
    "required": True
}

DATE_RANGE = {
    "basename": "date_range",
    "type": "string",
    "enum": ["last_7_days", "last_30_days", "last_3_months", "custom"],
    "description": "Date range for analysis",
    "required": True
}

REGION = {
    "basename": "region",
    "type": "string",
    "enum": ["all", "north", "south", "east", "west"],
    "description": "Geographic region to analyze",
    "required": False
}

PRIORITY = {
    "basename": "priority",
    "type": "string",
    "enum": ["normal", "high", "urgent"],
    "description": "Analysis priority level",
    "required": False
}

def get_all_parameters():
    """Get all parameter definitions"""
    return [ANALYSIS_TYPE, DATE_RANGE, REGION, PRIORITY]
