"""
Mission Particulars module for the mission generator.

This module provides functionality for generating mission particulars
including NPCs, complications, and rewards.
"""

import logging
from typing import Dict, Any, Optional, List

from model.mission import Mission, MissionParticulars
from .openai_client import get_openai_client

# Set up logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PARTICULARS_CONTENT = "Mission particulars not available."
OPENAI_UNAVAILABLE_MSG = "OpenAI client not available. Skipping operation."
UNKNOWN_WORLD = "unknown world"
UNKNOWN_SCENARIO = "unknown scenario"
UNKNOWN_ENVIRONMENT = "unknown environment"
UNKNOWN_TECH_LEVEL = "unknown tech level"
UNKNOWN_LAW_LEVEL = "unknown law level"
UNKNOWN_DETAIL_NAME = "Unknown"
DETAIL_NAME_KEY = "detail_name"
NAME_KEY = "name"
GPT_MODEL = "gpt-3.5-turbo"
GPT_SYSTEM_PROMPT = "You are a helpful assistant creating content for a Traveller RPG campaign."
GPT_MAX_TOKENS_LARGE = 500
GPT_MAX_TOKENS_MEDIUM = 400


def generate_mission_particulars(mission: Mission, use_gpt: bool, gpt_available: bool, api_key: Optional[str] = None) -> MissionParticulars:
    """
    Generate mission particulars including NPCs, complications, and rewards.
    
    Args:
        mission: The Mission object
        use_gpt: Whether to use GPT to enhance the particulars
        gpt_available: Whether GPT is available
        api_key: Optional API key for OpenAI
        
    Returns:
        MissionParticulars object with generated content
    """
    # Start with default particulars
    particulars = MissionParticulars(
        content=DEFAULT_PARTICULARS_CONTENT,
        map_image=None,
        npc_images=[],
        item_images=[],
        npcs="",
        complications="",
        rewards=""
    )
    
    # If GPT is not requested or not available, generate basic particulars
    if not use_gpt or not gpt_available:
        particulars.content = _generate_basic_particulars(mission)
        return particulars
    
    # Generate enhanced particulars with GPT
    npcs = _generate_npcs(mission, api_key)
    complications = _generate_complications(mission, api_key)
    rewards = _generate_rewards(mission, api_key)
    
    # Update particulars
    particulars.npcs = npcs
    particulars.complications = complications
    particulars.rewards = rewards
    
    # Combine all particulars into content
    content_parts = []
    if npcs:
        content_parts.append(f"NPCs:\n{npcs}")
    if complications:
        content_parts.append(f"Complications:\n{complications}")
    if rewards:
        content_parts.append(f"Rewards:\n{rewards}")
    
    if content_parts:
        particulars.content = "\n\n".join(content_parts)
    
    return particulars


def _get_detail_name(detail) -> str:
    """
    Extract the name from a detail object or dict.
    
    Args:
        detail: The detail object or dict
        
    Returns:
        The name of the detail
    """
    if isinstance(detail, dict):
        if DETAIL_NAME_KEY in detail:
            return detail[DETAIL_NAME_KEY]
        elif NAME_KEY in detail:
            return detail[NAME_KEY]
        return UNKNOWN_DETAIL_NAME
    else:
        # Assume it's an object with attributes
        return getattr(detail, DETAIL_NAME_KEY, getattr(detail, NAME_KEY, UNKNOWN_DETAIL_NAME))


def _generate_basic_particulars(mission: Mission) -> str:
    """
    Generate basic mission particulars without using GPT.
    
    Args:
        mission: The Mission object
        
    Returns:
        String containing basic mission particulars
    """
    world_name = mission.world.get("name", UNKNOWN_WORLD)
    scenario_type = mission.scenario_type.get("name", UNKNOWN_SCENARIO)
    
    # Generate basic particulars based on mission type and world
    content = f"Mission on {world_name}: {scenario_type}\n\n"
    
    # Add details
    if mission.details:
        content += "Details:\n"
        for detail_type, detail in mission.details.items():
            detail_name = _get_detail_name(detail)
            content += f"- {detail_type}: {detail_name}\n"
    
    # Add UWP summary if available
    if "UWP" in mission.world:
        content += f"\nWorld UWP: {mission.world['UWP']}\n"
        
        # Add trade codes if available
        if "trade_codes" in mission.world:
            trade_codes = mission.world["trade_codes"]
            if trade_codes:
                content += f"Trade Codes: {', '.join(trade_codes)}\n"
    
    return content


def _generate_npcs(mission: Mission, api_key: Optional[str] = None) -> str:
    """
    Generate NPCs for the mission using GPT.
    
    Args:
        mission: The Mission object
        api_key: Optional API key for OpenAI
        
    Returns:
        String containing NPC descriptions
    """
    client = get_openai_client(api_key)
    if not client:
        logger.warning(OPENAI_UNAVAILABLE_MSG)
        return ""
    
    try:
        # Prepare prompt for GPT
        world_name = mission.world.get("name", "unknown world")
        scenario_type = mission.scenario_type.get("name", "unknown scenario")
        tech_context = getattr(mission, "tech_context", "unknown tech level")
        population_density = getattr(mission, "population_density", "unknown population")
        
        prompt = f"""Create 3-5 interesting NPCs for a Traveller RPG mission.
        World: {world_name}
        Mission Type: {scenario_type}
        Tech Level: {tech_context}
        Population: {population_density}
        
        For each NPC, provide:
        1. Name
        2. Role in the mission
        3. Brief description
        4. Motivation
        5. One unique trait or quirk
        
        Format each NPC as a short paragraph."""
        
        # Call GPT API
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": GPT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=GPT_MAX_TOKENS_LARGE
        )
        
        # Extract and return the NPCs
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        
        return ""
    
    except Exception as e:
        logger.error(f"Error generating NPCs with GPT: {e}")
        return ""


def _generate_complications(mission: Mission, api_key: Optional[str] = None) -> str:
    """
    Generate complications for the mission using GPT.
    
    Args:
        mission: The Mission object
        api_key: Optional API key for OpenAI
        
    Returns:
        String containing complication descriptions
    """
    client = get_openai_client(api_key)
    if not client:
        logger.warning(OPENAI_UNAVAILABLE_MSG)
        return ""
    
    try:
        # Prepare prompt for GPT
        world_name = mission.world.get("name", UNKNOWN_WORLD)
        scenario_type = mission.scenario_type.get("name", UNKNOWN_SCENARIO)
        environment = getattr(mission, "environment", UNKNOWN_ENVIRONMENT)
        law_context = getattr(mission, "law_context", UNKNOWN_LAW_LEVEL)
        
        prompt = f"""Create 2-3 interesting complications for a Traveller RPG mission.
        World: {world_name}
        Mission Type: {scenario_type}
        Environment: {environment}
        Law Level: {law_context}
        
        For each complication, provide:
        1. A title
        2. Brief description of the complication
        3. Potential impact on the mission
        
        Format each complication as a short paragraph."""
        
        # Call GPT API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant creating content for a Traveller RPG campaign."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        
        # Extract and return the complications
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        
        return ""
    
    except Exception as e:
        logger.error(f"Error generating complications with GPT: {e}")
        return ""


def _generate_rewards(mission: Mission, api_key: Optional[str] = None) -> str:
    """
    Generate rewards for the mission using GPT.
    
    Args:
        mission: The Mission object
        api_key: Optional API key for OpenAI
        
    Returns:
        String containing reward descriptions
    """
    client = get_openai_client(api_key)
    if not client:
        logger.warning(OPENAI_UNAVAILABLE_MSG)
        return ""
    
    try:
        # Prepare prompt for GPT
        world_name = mission.world.get("name", "unknown world")
        scenario_type = mission.scenario_type.get("name", "unknown scenario")
        tech_context = getattr(mission, "tech_context", "unknown tech level")
        
        prompt = f"""Create 2-3 interesting rewards for a Traveller RPG mission.
        World: {world_name}
        Mission Type: {scenario_type}
        Tech Level: {tech_context}
        
        For each reward, provide:
        1. Type of reward (credits, item, information, favor, etc.)
        2. Description of the reward
        3. Potential value or usefulness to players
        
        Format each reward as a short paragraph."""
        
        # Call GPT API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant creating content for a Traveller RPG campaign."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        
        # Extract and return the rewards
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        
        return ""
    
    except Exception as e:
        logger.error(f"Error generating rewards with GPT: {e}")
        return ""
