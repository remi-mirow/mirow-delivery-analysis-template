"""
Main analysis runner - Data scientists implement their analysis logic here.

This is the ONLY file data scientists need to modify.
All infrastructure complexity is handled automatically.

Data scientists can easily modify:
- Input file paths in analysis/metadata/inputs.py
- Output file paths in analysis/metadata/outputs.py
- Analysis logic in this file
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, Any
from analysis.metadata.inputs import get_input_files
from analysis.metadata.outputs import get_output_files
from analysis.metadata.processed import get_processed_files

def run_analysis(job_id: str, progress_callback=None):
    """
    Simple analysis function: Process 2 CSV files and save as XLSX.
    
    Args:
        job_id: Job identifier for file paths
        progress_callback: Optional progress callback function
        
    Returns:
        Status string indicating completion
    """
    
    if progress_callback:
        progress_callback(0.1, "Loading CSV files...")
    
    # Get file paths using metadata functions
    input_files = get_input_files(job_id)
    output_files = get_output_files(job_id)
    processing_files = get_processed_files(job_id)
    
    # ========================================
    # SIMPLE ANALYSIS LOGIC
    # ========================================
    
    # Read the 2 CSV files
    file1_path = input_files["file1"]["path"]
    file2_path = input_files["file2"]["path"]
    
    if not Path(file1_path).exists():
        file1_info = input_files["file1"]
        raise ValueError(f"Required file 'file1' ({file1_info['name']}) not found at {file1_path}")
    
    if not Path(file2_path).exists():
        file2_info = input_files["file2"]
        raise ValueError(f"Required file 'file2' ({file2_info['name']}) not found at {file2_path}")
    
    # Load CSV files using pandas
    df1 = pd.read_csv(file1_path)
    df2 = pd.read_csv(file2_path)
    
    print(f"File1 shape: {df1.shape}")
    print(f"File2 shape: {df2.shape}")
    
    if progress_callback:
        progress_callback(0.3, "Processing data...")
    
    print(f"Processing {len(df1)} rows from file1 and {len(df2)} rows from file2")
    
    # Example: Use processed files for temporary data
    temp_data_file = processing_files["temp_data"]["path"]
    temp_info = processing_files["temp_data"]
    print(f"Using temporary file: {temp_info['name']}")
    # Example: Save intermediate data
    df1.to_csv(temp_data_file, index=False)
    
    if progress_callback:
        progress_callback(0.7, "Saving as XLSX...")
    
    # Save files as XLSX using pandas
    # Save first file as XLSX
    output1_file = output_files["output1"]["path"]
    output1_info = output_files["output1"]
    print(f"Saving file1 as XLSX to {output1_info['name']}")
    df1.to_excel(output1_file, index=False)
    
    # Save second file as XLSX
    output2_file = output_files["output2"]["path"]
    output2_info = output_files["output2"]
    print(f"Saving file2 as XLSX to {output2_info['name']}")
    df2.to_excel(output2_file, index=False)
    
    if progress_callback:
        progress_callback(1.0, "Analysis completed!")
    
    return "completed"