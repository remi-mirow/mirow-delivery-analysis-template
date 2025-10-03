#!/usr/bin/env python3
"""
Script to create Analysis record in orchestrator database.
This should be run after the analysis service is deployed and registered.
"""

import os
import sys
import httpx
import asyncio
from datetime import datetime

# Configuration
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "https://mirow-delivery-orchestrator-production.up.railway.app")
SERVICE_NAME = os.getenv("RAILWAY_SERVICE_NAME", "mirow-delivery-analysis-template")
SERVICE_VERSION = "1.0.0"

async def create_analysis_record():
    """Create Analysis record in orchestrator database"""
    
    analysis_data = {
        "name": SERVICE_NAME,
        "description": "A simple analysis service that processes 2 CSV files",
        "version": SERVICE_VERSION,
        "git_repository": "https://github.com/your-org/mirow-delivery-analysis-template",
        "docker_image": f"mirow-delivery-analysis-template:{SERVICE_VERSION}",
        "service_port": 8000,
        "is_active": True,
        "config_schema": {
            "type": "object",
            "properties": {
                "dateRange": {"type": "string", "enum": ["last-7-days", "last-30-days", "last-3-months", "last-year", "custom"]},
                "region": {"type": "string", "enum": ["all", "north", "south", "east", "west"]},
                "priority": {"type": "string", "enum": ["normal", "high", "urgent"]}
            }
        },
        "input_requirements": {
            "required_files": 2,
            "supported_formats": ["csv", "xlsx"],
            "max_file_size": "10MB"
        }
    }
    
    print(f"🚀 Creating Analysis record for service: {SERVICE_NAME}")
    print(f"🎯 Orchestrator URL: {ORCHESTRATOR_URL}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, try to get admin token (you'll need to provide this)
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
