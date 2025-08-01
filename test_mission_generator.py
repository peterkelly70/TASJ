#!/usr/bin/env python3
"""
Test script for the mission generator with UWP data and ChatGPT image generation.
"""

import os
import sys
import logging
import json
from controller.mission_generator import MissionGenerator
from dotenv import load_dotenv

# Configure logging to show all logs on console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    # Load environment variables
    load_dotenv()
    load_dotenv("tasj.env")
    
    # Ensure we load from config/.env with correct path
    config_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", ".env")
    if os.path.exists(config_env_path):
        load_dotenv(config_env_path)
    else:
        print(f"WARNING: Could not find {config_env_path}")
        # Try relative path as fallback
        load_dotenv("config/.env")
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: No OpenAI API key found. Set OPENAI_API_KEY in your environment.")
        print("Image generation and detailed mission particulars will not be available.")
        print("Checked the following locations for API key:")
        print("- Environment variables")
        print("- .env in current directory")
        print("- tasj.env")
        print(f"- {config_env_path}")
    else:
        print("OpenAI API key found. GPT features will be enabled if the OpenAI package is installed.")
        
    # Check if OpenAI package is installed
    try:
        import openai
        print("OpenAI package is installed.")
    except ImportError:
        print("WARNING: OpenAI package is not installed. Install it with: pip install openai")
        print("Image generation and detailed mission particulars will not be available.")
        print("Even with a valid API key, GPT features will not work without the OpenAI package.")
        print("\n")
    
    # Initialize mission generator
    mission_generator = MissionGenerator()
    
    # Sample world data with UWP
    test_world = {
        "id": 1,
        "name": "Aramis",
        "UWP": "A867A74-B",
        "sector": "Spinward Marches",
        "subsector": "Aramis",
        "hex": "3110"
    }
    
    print(f"Generating mission for world: {test_world['name']} ({test_world['UWP']})")
    
    # Generate mission with GPT enhancements
    mission = mission_generator.generate_mission_for_world(test_world, use_gpt=True)
    
    # Print mission details
    print("\n=== MISSION DETAILS ===")
    print(f"World: {mission['world']['name']} - {mission_generator.uwp_summary(mission['world']['UWP'])}")
    
    if 'structure' in mission:
        print(f"Scenario Type: {mission['structure']['scenario_type']['name']}")
        
        print("\nDetails:")
        for detail_id, detail in mission['structure']['details'].items():
            print(f"- {detail['name']}")
    else:
        print("\nWARNING: Mission structure not found in the returned data.")
        print("Available keys in mission:", list(mission.keys()))
    
    print("\nUWP Factors:")
    for factor, value in mission.get('uwp_factors', {}).items():
        print(f"- {factor}: {value}")
    
    print("\nUWP-based Adjustments:")
    for key in ['tech_context', 'population_density', 'environment', 'law_context', 'port_context']:
        if key in mission:
            print(f"- {key}: {mission[key]}")
    
    print("\nMap Description:")
    print(mission.get('map_description', 'No map description available'))
    
    # Print GPT-generated particulars
    print("\n=== GPT-GENERATED PARTICULARS ===")
    particulars = mission.get('particulars', {})
    
    if not particulars:
        print("No GPT-generated particulars found. This could be because:")
        print("1. OpenAI package is not available")
        print("2. No API key was provided")
        print("3. An error occurred during generation")
    else:
        if 'briefing' in particulars:
            print("\nMission Briefing:")
            print(particulars['briefing'])
        
        if 'npcs' in particulars:
            print("\nNPCs:")
            print(particulars['npcs'])
        
        if 'complications' in particulars:
            print("\nComplications:")
            print(particulars['complications'])
        
        if 'rewards' in particulars:
            print("\nRewards:")
            print(particulars['rewards'])
        
        # Print image URLs if available
        print("\n=== GENERATED IMAGES ===")
        
        if 'map_image' in particulars:
            print("\nVTT Map Image URL:")
            print(particulars['map_image'])
        else:
            print("\nNo VTT map image was generated.")
        
        if 'npc_images' in particulars and particulars['npc_images']:
            print("\nNPC Image URLs:")
            for i, url in enumerate(particulars['npc_images']):
                print(f"{i+1}. {url}")
        else:
            print("\nNo NPC images were generated.")
        
        if 'item_images' in particulars and particulars['item_images']:
            print("\nItem Image URLs:")
            for i, url in enumerate(particulars['item_images']):
                print(f"{i+1}. {url}")
        else:
            print("\nNo item images were generated.")
    
    print("\nMission saved to database with ID:", mission.get('id', 'Unknown'))

if __name__ == "__main__":
    main()
