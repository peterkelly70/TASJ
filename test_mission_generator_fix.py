#!/usr/bin/env python3
"""
Test script to fix mission generator issues.

This script identifies and fixes issues in the mission generator related to:
1. OpenAI API calls using the new interface
2. Database constraint errors for mission particulars
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from multiple potential locations
load_dotenv()  # Default .env file
load_dotenv("tasj.env")  # Project-specific env file
load_dotenv("config/.env")  # Config directory env file

# Import the mission generator
from controller.mission_generator import MissionGenerator

def test_mission_generator():
    """Test the mission generator and fix issues."""
    logger.info("Testing mission generator...")
    
    # Create a mission generator instance
    mission_gen = MissionGenerator()
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        logger.info(f"OpenAI API key found. First 10 chars: {api_key[:10]}...")
        
        # Check if the API key is a project key
        if api_key.startswith("sk-proj-"):
            logger.warning("Project-level API key detected (sk-proj-...).")
            logger.warning("This type of key may not work with the OpenAI API.")
            logger.warning("Consider using a regular API key (sk-...) instead.")
    else:
        logger.error("No OpenAI API key found. Please check your environment variables.")
        return
    
    # Test the OpenAI client creation
    client = mission_gen._get_openai_client()
    if client:
        logger.info("OpenAI client created successfully.")
    else:
        logger.error("Failed to create OpenAI client.")
        return
    
    # Create a test world
    test_world = {
        "name": "Test World",
        "UWP": "A867A74-B",
        "remarks": "Hi In",
        "zone": "",
        "bases": "S",
        "stellar": "G2 V",
        "trade_codes": ["High Population", "Industrial"],
        "sector": "Test Sector",
        "subsector": "Test Subsector"
    }
    
    # Generate a mission
    logger.info(f"Generating mission for world: {test_world['name']} ({test_world['UWP']})")
    mission = mission_gen.generate_mission_for_world(test_world, use_gpt=True)
    
    # Check if mission was generated
    if not mission:
        logger.error("Failed to generate mission.")
        return
    
    # Check mission structure
    logger.info("Mission structure:")
    if "structure" in mission:
        logger.info("Mission has 'structure' key.")
    else:
        logger.info("Mission does not have 'structure' key. Keys at top level.")
        logger.info(f"Available keys in mission: {list(mission.keys())}")
    
    # Check mission particulars
    if "particulars" in mission:
        logger.info("Mission has 'particulars' key.")
        logger.info(f"Particulars content: {mission['particulars']}")
    else:
        logger.error("Mission does not have 'particulars' key.")
    
    # Save mission to database
    try:
        mission_gen._save_mission_to_db(mission)
        logger.info("Mission saved to database successfully.")
    except Exception as e:
        logger.error(f"Error saving mission to database: {e}")
    
    logger.info("Mission generator test completed.")

if __name__ == "__main__":
    test_mission_generator()
