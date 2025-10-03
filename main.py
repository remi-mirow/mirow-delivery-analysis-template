"""
Main orchestrator function for the analysis service.

This function handles the 3-step workflow:
1. Receive files from orchestrator API and store in inputs folder
2. Execute run() in analysis 
3. Extract outputs and return files with KPIs
"""

import os
import json
import yaml
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, Any, List, Optional
from analysis.metadata.inputs import get_input_files
from analysis.metadata.outputs import get_output_files
from analysis.metadata.processed import get_processed_files
from analysis.run import run_analysis

# Directory definitions derived from DATA_DIR environment variable
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", "./analysis/data"))
INPUTS_DIR = DATA_DIR / "inputs"
OUTPUTS_DIR = DATA_DIR / "outputs"
PROCESSED_DIR = DATA_DIR / "processed"

class AnalysisOrchestrator:
    """Main orchestrator class for the analysis workflow"""
    
    def __init__(self, orchestrator_url: str, job_id: str):
        self.orchestrator_url = orchestrator_url
        self.job_id = job_id
        self.inputs_dir = INPUTS_DIR / job_id
        self.outputs_dir = OUTPUTS_DIR / job_id
        
    async def main(self) -> Dict[str, Any]:
        """
        Main function that orchestrates the 3-step analysis workflow
        
        Returns:
            Dictionary with analysis results, output files, and KPIs
        """
        try:
            # Step 1: Receive files from orchestrator API
            print(f"Step 1: Receiving files for job {self.job_id}")
            await self._step1_receive_files()
            
            # Step 2: Execute analysis
            print(f"Step 2: Executing analysis for job {self.job_id}")
            status = await self._step2_execute_analysis()
            
            if status != "completed":
                raise Exception(f"Analysis failed with status: {status}")
            
            # Step 3: Extract outputs and return
            print(f"Step 3: Extracting outputs for job {self.job_id}")
            output_data = await self._step3_extract_outputs()
            
            return {
                "job_id": self.job_id,
                "status": "completed",
                "output_files": output_data["files"]
            }
            
        except Exception as e:
            print(f"Analysis failed for job {self.job_id}: {str(e)}")
            return {
                "job_id": self.job_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _step1_receive_files(self):
        """Step 1: Receive all files from orchestrator API and store in inputs folder"""
        
        # Create directories
        self.inputs_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Get job data from orchestrator
        async with aiohttp.ClientSession() as session:
            # Get job information
            job_url = f"{self.orchestrator_url}/api/v1/analysis/{self.job_id}"
            async with session.get(job_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get job data: {response.status}")
                job_data = await response.json()
            
            # Download input files
            files_to_download = job_data.get("input_files", [])
            for file_info in files_to_download:
                file_url = file_info["url"]
                filename = file_info["filename"]
                
                # Download file
                async with session.get(file_url) as file_response:
                    if file_response.status == 200:
                        file_path = self.inputs_dir / filename
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in file_response.content.iter_chunked(8192):
                                await f.write(chunk)
                        print(f"Downloaded: {filename}")
                    else:
                        print(f"Failed to download {filename}: {file_response.status}")
            
            print(f"All files downloaded to: {self.inputs_dir}")
    
    async def _step2_execute_analysis(self) -> str:
        """Step 2: Execute run() in analysis"""
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            print(f"Progress: {progress:.1%} - {message}")
        
        # Run the analysis
        status = run_analysis(self.job_id, progress_callback=progress_callback)
        
        return status
    
    async def _step3_extract_outputs(self) -> Dict[str, Any]:
        """Step 3: Extract all files in outputs and return them"""
        
        # Collect output files using metadata directly
        output_files = []
        all_output_metadata = get_output_files(self.job_id)
        for file_key, file_info in all_output_metadata.items():
            file_path = Path(file_info["path"])
            if file_path.exists():
                output_files.append({
                    "key": file_key,
                    "filename": file_info["name"],
                    "dtype": file_info["dtype"],
                    "description": file_info["description"],
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "required": file_info.get("required", False)
                })
        
        return {
            "files": output_files
        }

async def main(orchestrator_url: str, job_id: str) -> Dict[str, Any]:
    """
    Main entry point for the analysis service.
    
    Args:
        orchestrator_url: URL of the orchestrator service
        job_id: Unique job identifier
        
    Returns:
        Dictionary with analysis results
    """
    orchestrator = AnalysisOrchestrator(orchestrator_url, job_id)
    return await orchestrator.main()

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python main.py <orchestrator_url> <job_id>")
        sys.exit(1)
    
    orchestrator_url = sys.argv[1]
    job_id = sys.argv[2]
    
    # Run the analysis
    result = asyncio.run(main(orchestrator_url, job_id))
    print(json.dumps(result, indent=2))
