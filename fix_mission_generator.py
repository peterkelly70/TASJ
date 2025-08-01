#!/usr/bin/env python3
"""
Fix script for mission generator.

This script updates the mission_generator.py file to:
1. Use _get_openai_client consistently
2. Fix database constraint errors
"""

import os
import re
import sys
from pathlib import Path

# Configure paths
project_root = Path(__file__).parent
mission_generator_path = project_root / "controller" / "mission_generator.py"

# Check if mission_generator.py exists
if not mission_generator_path.exists():
    print(f"Error: {mission_generator_path} does not exist.")
    sys.exit(1)

# Read the mission generator file
with open(mission_generator_path, "r") as f:
    content = f.read()

# Define the replacements to make
replacements = [
    # Replace direct OpenAI client creation with _get_openai_client helper
    (
        r"# Create OpenAI client\s+client = OpenAI\(api_key=self\.api_key\)",
        """# Get OpenAI client
            client = self._get_openai_client()
            if not client:
                logger.warning("OpenAI client not available. Skipping operation.")
                return"""
    ),
    
    # Replace "Use the client created earlier" comments to ensure we're using the right client
    (
        r"# Use the client created earlier",
        """# Ensure we have a valid client
            if not client:
                client = self._get_openai_client()
                if not client:
                    logger.warning("OpenAI client not available. Skipping operation.")
                    return"""
    ),
    
    # Ensure mission particulars are properly initialized in _generate_mission_for_world
    (
        r"def generate_mission_for_world\(self, world_data: Dict\[str, Any\], use_gpt: bool = True\) -> Dict\[str, Any\]:",
        """def generate_mission_for_world(self, world_data: Dict[str, Any], use_gpt: bool = True) -> Dict[str, Any]:
        # Initialize mission structure
        mission = {
            "world": world_data,
            "particulars": {
                "content": "",  # Ensure content field is initialized
                "map_image": None,
                "npc_images": [],
                "item_images": [],
                "npcs": "",
                "complications": "",
                "rewards": ""
            }
        }"""
    ),
    
    # Update _save_mission_to_db to handle missing particulars
    (
        r"# Save mission particulars if available\s+if \"particulars\" in mission and mission\[\"particulars\"\]:",
        """# Save mission particulars if available
            if "particulars" in mission and mission["particulars"]:
                # Ensure content field exists
                if "content" not in mission["particulars"]:
                    mission["particulars"]["content"] = ""
                    
                # If we have any GPT-generated content, use it as the content field
                if not mission["particulars"]["content"]:
                    content_parts = []
                    if mission["particulars"].get("npcs"):
                        content_parts.append("NPCs:\\n" + mission["particulars"]["npcs"])
                    if mission["particulars"].get("complications"):
                        content_parts.append("Complications:\\n" + mission["particulars"]["complications"])
                    if mission["particulars"].get("rewards"):
                        content_parts.append("Rewards:\\n" + mission["particulars"]["rewards"])
                    
                    if content_parts:
                        mission["particulars"]["content"] = "\\n\\n".join(content_parts)
                    else:
                        mission["particulars"]["content"] = "Mission particulars not available."
            else:
                # Create default particulars if missing
                mission["particulars"] = {
                    "content": "Mission particulars not available.",
                    "map_image": None,
                    "npc_images": [],
                    "item_images": []
                }"""
    )
]

# Apply the replacements
updated_content = content
for pattern, replacement in replacements:
    updated_content = re.sub(pattern, replacement, updated_content)

# Write the updated content back to the file
with open(mission_generator_path, "w") as f:
    f.write(updated_content)

print(f"Updated {mission_generator_path}.")
print("Please run the test script to verify the fixes.")
