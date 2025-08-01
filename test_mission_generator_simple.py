#!/usr/bin/env python3
"""
Simple test script for mission generator.

This script tests the mission generator without making any API calls.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # Import the mission generator
    from controller.mission_generator import MissionGenerator
    logger.info("Successfully imported MissionGenerator")
    
    # Create a mission generator instance
    mission_gen = MissionGenerator()
    logger.info("Successfully created MissionGenerator instance")
    
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
    
    # Generate a mission without GPT
    logger.info(f"Generating mission for world: {test_world['name']} ({test_world['UWP']})")
    mission = mission_gen.generate_mission_for_world(test_world, use_gpt=False)
    
    # Check if mission was generated
    if mission:
        logger.info("Mission generated successfully")
        logger.info(f"Mission keys: {list(mission.keys())}")
        
        if "particulars" in mission:
            logger.info("Mission has 'particulars' key")
            logger.info(f"Particulars keys: {list(mission['particulars'].keys())}")
        else:
            logger.error("Mission does not have 'particulars' key")
    else:
        logger.error("Failed to generate mission")
    
except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
