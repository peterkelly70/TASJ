"""
Image Generation module for the mission generator.

This module provides functionality for generating images for missions,
including maps, NPCs, and items using DALL-E API.
"""

import logging
from typing import Dict, Any, Optional, List

from model.mission import Mission
from .openai_client import get_openai_client

# Set up logger
logger = logging.getLogger(__name__)

# Constants
OPENAI_UNAVAILABLE_MSG = "OpenAI client not available. Skipping operation."
UNKNOWN_TECH_LEVEL = "unknown tech level"
UNKNOWN_WORLD = "unknown world"
UNKNOWN_SCENARIO = "unknown scenario"
UNKNOWN_ENVIRONMENT = "unknown environment"


def generate_vtt_map_image(mission: Mission, api_key: Optional[str] = None) -> Optional[str]:
    """
    Generate a map image for a virtual tabletop using DALL-E.
    
    Args:
        mission: The Mission object
        api_key: Optional API key for OpenAI
        
    Returns:
        URL of the generated image, or None if generation failed
    """
    client = get_openai_client(api_key)
    if not client:
        logger.warning(OPENAI_UNAVAILABLE_MSG)
        return None
    
    try:
        # Prepare prompt for DALL-E
        world_name = mission.world.get("name", UNKNOWN_WORLD)
        scenario_type = mission.scenario_type.get("name", UNKNOWN_SCENARIO)
        environment = getattr(mission, "environment", UNKNOWN_ENVIRONMENT)
        tech_context = getattr(mission, "tech_context", UNKNOWN_TECH_LEVEL)
        
        # Use map description if available, otherwise generate a basic one
        map_description = getattr(mission, "map_description", "")
        if not map_description:
            map_description = f"Map for {scenario_type} mission on {world_name}. {environment}. {tech_context} level."
        
        prompt = f"""Create a top-down map for a Traveller RPG virtual tabletop.
        {map_description}
        
        Style: Detailed sci-fi map with grid overlay, suitable for virtual tabletop gaming.
        Include relevant terrain features, structures, and points of interest.
        """
        
        # Call DALL-E API
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Extract and return the image URL
        if response.data and response.data[0].url:
            return response.data[0].url
        
        return None
    
    except Exception as e:
        logger.error(f"Error generating map image with DALL-E: {e}")
        return None


def generate_npc_images(mission: Mission, api_key: Optional[str] = None) -> List[str]:
    """
    Generate NPC images for the mission using DALL-E.
    
    Args:
        mission: The Mission object
        api_key: Optional API key for OpenAI
        
    Returns:
        List of URLs for the generated images
    """
    client = get_openai_client(api_key)
    if not client:
        logger.warning(OPENAI_UNAVAILABLE_MSG)
        return []
    
    # Check if we have NPC descriptions
    if not hasattr(mission, "particulars") or not mission.particulars or not mission.particulars.npcs:
        logger.warning("No NPC descriptions available for image generation")
        return []
    
    try:
        # Extract NPC descriptions
        npc_text = mission.particulars.npcs
        
        # Split into paragraphs to identify individual NPCs
        npc_paragraphs = [p.strip() for p in npc_text.split("\n\n") if p.strip()]
        
        # Limit to 3 NPCs to avoid excessive API usage
        npc_paragraphs = npc_paragraphs[:3]
        
        image_urls = []
        
        for npc_desc in npc_paragraphs:
            # Prepare prompt for DALL-E
            tech_context = getattr(mission, "tech_context", UNKNOWN_TECH_LEVEL)
            
            prompt = f"""Create a portrait image of a Traveller RPG character:
            {npc_desc}
            
            Technology level: {tech_context}
            Style: Detailed sci-fi character portrait, front-facing, upper body.
            """
            
            # Call DALL-E API
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            # Extract and add the image URL
            if response.data and response.data[0].url:
                image_urls.append(response.data[0].url)
        
        return image_urls
    
    except Exception as e:
        logger.error(f"Error generating NPC images with DALL-E: {e}")
        return []


def generate_item_images(mission: Mission, api_key: Optional[str] = None) -> List[str]:
    """
    Generate item images for the mission using DALL-E.
    
    Args:
        mission: The Mission object
        api_key: Optional API key for OpenAI
        
    Returns:
        List of URLs for the generated images
    """
    client = get_openai_client(api_key)
    if not client:
        logger.warning(OPENAI_UNAVAILABLE_MSG)
        return []
    
    # Check if we have reward descriptions (which might contain items)
    if not hasattr(mission, "particulars") or not mission.particulars or not mission.particulars.rewards:
        logger.warning("No reward descriptions available for item image generation")
        return []
    
    try:
        # Extract reward descriptions
        rewards_text = mission.particulars.rewards
        
        # Generate a single item image based on the rewards
        tech_context = getattr(mission, "tech_context", UNKNOWN_TECH_LEVEL)
        scenario_type = mission.scenario_type.get("name", UNKNOWN_SCENARIO)
        
        prompt = f"""Create an image of a key item for a Traveller RPG mission:
        Mission type: {scenario_type}
        Technology level: {tech_context}
        
        Based on these rewards:
        {rewards_text}
        
        Style: Detailed sci-fi item on a neutral background, well-lit to show details.
        """
        
        # Call DALL-E API
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Extract and return the image URL
        if response.data and response.data[0].url:
            return [response.data[0].url]
        
        return []
    
    except Exception as e:
        logger.error(f"Error generating item images with DALL-E: {e}")
        return []
