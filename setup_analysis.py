#!/usr/bin/env python3
"""
Script to create Analysis record in orchestrator database.
This dynamically collects metadata from analysis/metadata/ files.
"""

import os
import sys
import httpx
import asyncio
from datetime import datetime
from pathlib import Path

# Add analysis directory to path to import metadata modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'analysis'))

# Import analysis metadata
from analysis.metadata.inputs import get_input_files
from analysis.metadata.outputs import get_output_files

# Configuration - all configurable via environment variables
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "https://mirow-delivery-orchestrator-production.up.railway.app")
SERVICE_NAME = os.getenv("RAILWAY_SERVICE_NAME", "mirow-delivery-analysis-template")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
MAX_FILE_SIZE = os.getenv("MAX_FILE_SIZE", "10MB")
CAPABILITIES = os.getenv("CAPABILITIES", "csv_processing,data_analysis").split(",")

class AnalysisMetadataCollector:
    """Collects and processes analysis metadata in a pythonic way"""
    
    def __init__(self, job_id: str = "metadata"):
        self.job_id = job_id
        self._input_files = None
        self._output_files = None
        self._supported_formats = None
    
    @property
    def input_files(self):
        """Lazy load input files metadata"""
        if self._input_files is None:
            self._input_files = get_input_files(self.job_id)
        return self._input_files
    
    @property
    def output_files(self):
        """Lazy load output files metadata"""
        if self._output_files is None:
            self._output_files = get_output_files(self.job_id)
        return self._output_files
    
    @property
    def supported_formats(self):
        """Extract supported formats from input files"""
        if self._supported_formats is None:
            formats = set()
            for file_info in self.input_files.values():
                if dtype := file_info.get("dtype"):
                    formats.add(dtype)
            self._supported_formats = list(formats)
        return self._supported_formats
    
    def get_input_requirements(self):
        """Build input requirements from metadata"""
        return {
            "supported_formats": self.supported_formats,
            "max_file_size": MAX_FILE_SIZE,
            "input_files": self.input_files,
            "output_files": self.output_files,
            "capabilities": CAPABILITIES
        }
    
    def get_description(self):
        """Generate description from metadata"""
        input_count = len(self.input_files)
        output_count = len(self.output_files)
        return f"Analysis service processing {input_count} input files and generating {output_count} output files"

async def create_analysis_record():
    """Create Analysis record in orchestrator database using dynamic metadata"""
    
    # Use the pythonic metadata collector
    metadata_collector = AnalysisMetadataCollector()
    
    analysis_data = {
        "name": SERVICE_NAME,
        "description": metadata_collector.get_description(),
        "version": SERVICE_VERSION,
        "is_active": True,
        "input_requirements": metadata_collector.get_input_requirements()
    }
    
    print(f"🚀 Creating Analysis record for service: {SERVICE_NAME}")
    print(f"🎯 Orchestrator URL: {ORCHESTRATOR_URL}")
    print(f"📊 Dynamic metadata collected:")
    print(f"   Supported formats: {metadata_collector.supported_formats}")
    print(f"   Input files: {list(metadata_collector.input_files.keys())}")
    print(f"   Output files: {list(metadata_collector.output_files.keys())}")
    print(f"   Capabilities: {CAPABILITIES}")
    print(f"   Max file size: {MAX_FILE_SIZE}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get admin token from environment
            admin_token = os.getenv("ADMIN_TOKEN")
            if not admin_token:
                print("❌ ADMIN_TOKEN environment variable is required")
                print("   Set ADMIN_TOKEN to your admin JWT token")
                return False
            
            # Create the analysis record
            response = await client.post(
                f"{ORCHESTRATOR_URL}/api/v1/analysis/",
                json=analysis_data,
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analysis record created successfully!")
                print(f"   ID: {result['id']}")
                print(f"   Name: {result['name']}")
                print(f"   Version: {result['version']}")
                return True
            elif response.status_code == 400:
                error_data = response.json()
                if "already exists" in error_data.get("detail", ""):
                    print(f"⚠️ Analysis record already exists for service: {SERVICE_NAME}")
                    return True
                else:
                    print(f"❌ Bad request: {error_data}")
                    return False
            else:
                print(f"❌ Failed to create analysis record: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error creating analysis record: {str(e)}")
        return False

async def check_service_registration():
    """Check if service is registered in service registry"""
    
    print(f"🔍 Checking service registration...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/api/v1/services/connected")
            
            if response.status_code == 200:
                services = response.json()
                matching_services = [s for s in services if s['service_name'] == SERVICE_NAME]
                
                if matching_services:
                    service = matching_services[0]
                    print(f"✅ Service found in registry:")
                    print(f"   Name: {service['service_name']}")
                    print(f"   Status: {service['health_status']}")
                    print(f"   URL: {service['base_url']}")
                    return True
                else:
                    print(f"⚠️ Service {SERVICE_NAME} not found in connected services")
                    print(f"   Available services: {[s['service_name'] for s in services]}")
                    return False
            else:
                print(f"❌ Failed to check service registry: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error checking service registry: {str(e)}")
        return False

async def main():
    """Main function"""
    print("🔧 Mirow Delivery Analysis Setup")
    print("=" * 50)
    
    # Check service registration first
    service_registered = await check_service_registration()
    
    if not service_registered:
        print("\n⚠️ Service is not registered in the service registry.")
        print("   Make sure the analysis service is running and can connect to the orchestrator.")
        print("   Check the analysis service logs for registration errors.")
        return
    
    # Create analysis record
    print("\n📝 Creating Analysis record...")
    success = await create_analysis_record()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("   The analysis should now appear in the frontend.")
    else:
        print("\n❌ Setup failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
