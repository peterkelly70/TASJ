#!/usr/bin/env python3
"""
Test script for the mission generator.
This script demonstrates generating missions using the mission generator.
"""

from controller.mission_generator import MissionGenerator
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Generate and display sample missions."""
    logger.info("Initializing mission generator...")
    generator = MissionGenerator()
    
    # Get available worlds
    worlds = generator.get_available_worlds()
    if not worlds:
        logger.error("No worlds available!")
        return
    
    # Display available worlds
    logger.info(f"Available worlds: {', '.join(world['name'] for world in worlds)}")
    
    # Select a world
    selected_world = worlds[0]
    logger.info(f"Selected world: {selected_world['name']} ({selected_world['UWP']})")
    
    # Generate missions
    logger.info("Generating missions...")
    missions = generator.generate_multiple_missions(
        world_data=selected_world,
        count=2,
        use_gpt=False  # Set to True to use GPT if available
    )
    
    # Display missions
    logger.info(f"Generated {len(missions)} missions:")
    for i, mission in enumerate(missions, 1):
        print(f"\n{'='*80}\nMISSION {i}: {mission['title']}\n{'='*80}")
        
        # Display mission structure
        print("\nMISSION STRUCTURE:")
        print(f"Scenario Type: {mission['structure']['scenario_type']['name']}")
        print("\nDetails:")
        for table_name, detail in mission['structure']['details'].items():
            print(f"- {table_name}: {detail['name']}")
        
        # Display mission description
        print("\nDESCRIPTION:")
        print(mission['description'])
        
        # Display map description
        print("\nMAP DESCRIPTION:")
        print(mission['map_description'])
    
    logger.info("Mission generation test complete!")

if __name__ == "__main__":
    main()
