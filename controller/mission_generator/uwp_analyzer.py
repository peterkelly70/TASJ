"""
UWP Analyzer module for the mission generator.

This module provides functionality for analyzing and interpreting
Universal World Profile (UWP) data for Traveller RPG worlds.
"""

import logging
from typing import Dict, Any, Optional

# Set up logger
logger = logging.getLogger(__name__)

# UWP code mappings
STARPORT_CODES = {
    'A': 'class A starport (excellent)',
    'B': 'class B starport (good)',
    'C': 'class C starport (routine)',
    'D': 'class D starport (poor)',
    'E': 'class E starport (frontier)',
    'X': 'no starport'
}

SIZE_CODES = {
    '0': 'asteroid/planetoid belt',
    '1': 'tiny world (1,000 km)',
    '2': 'small world (2,000 km)',
    '3': 'small world (3,000 km)',
    '4': 'medium-small world (4,000 km)',
    '5': 'medium world (5,000 km)',
    '6': 'medium world (6,000 km)',
    '7': 'medium-large world (7,000 km)',
    '8': 'large world (8,000 km)',
    '9': 'large world (9,000 km)',
    'A': 'massive world (10,000 km)'
}

ATMOSPHERE_CODES = {
    '0': 'no atmosphere',
    '1': 'trace atmosphere',
    '2': 'very thin, tainted',
    '3': 'very thin',
    '4': 'thin, tainted',
    '5': 'thin',
    '6': 'standard',
    '7': 'standard, tainted',
    '8': 'dense',
    '9': 'dense, tainted',
    'A': 'exotic',
    'B': 'exotic, corrosive',
    'C': 'insidious',
    'D': 'dense, high',
    'E': 'thin, low',
    'F': 'unusual'
}

HYDROGRAPHICS_CODES = {
    '0': 'desert world (0-5%)',
    '1': 'dry world (6-15%)',
    '2': 'dry world (16-25%)',
    '3': 'wet world (26-35%)',
    '4': 'wet world (36-45%)',
    '5': 'wet world (46-55%)',
    '6': 'wet world (56-65%)',
    '7': 'wet world (66-75%)',
    '8': 'wet world (76-85%)',
    '9': 'wet world (86-95%)',
    'A': 'water world (96-100%)'
}

POPULATION_CODES = {
    '0': 'unpopulated',
    '1': 'few (tens)',
    '2': 'hundreds',
    '3': 'thousands',
    '4': 'tens of thousands',
    '5': 'hundreds of thousands',
    '6': 'millions',
    '7': 'tens of millions',
    '8': 'hundreds of millions',
    '9': 'billions',
    'A': 'teeming megacities'
}

GOVERNMENT_CODES = {
    '0': 'no government',
    '1': 'company/corporation',
    '2': 'participating democracy',
    '3': 'self-perpetuating oligarchy',
    '4': 'representative democracy',
    '5': 'feudal technocracy',
    '6': 'captive government',
    '7': 'balkanization',
    '8': 'civil service bureaucracy',
    '9': 'impersonal bureaucracy',
    'A': 'charismatic dictator',
    'B': 'non-charismatic dictator',
    'C': 'charismatic oligarchy',
    'D': 'religious dictatorship',
    'E': 'religious autocracy',
    'F': 'totalitarian oligarchy'
}

LAW_LEVEL_CODES = {
    '0': 'no law (anarchy)',
    '1': 'low law level',
    '2': 'low law level',
    '3': 'low law level',
    '4': 'moderate law level',
    '5': 'moderate law level',
    '6': 'moderate law level',
    '7': 'high law level',
    '8': 'high law level',
    '9': 'high law level',
    'A': 'extreme law level',
    'B': 'extreme law level',
    'C': 'extreme law level',
    'D': 'extreme law level',
    'E': 'extreme law level',
    'F': 'extreme law level'
}

TECH_LEVEL_CODES = {
    '0': 'primitive (stone age)',
    '1': 'primitive (bronze/iron age)',
    '2': 'primitive (renaissance)',
    '3': 'primitive (early industrial)',
    '4': 'average (industrial)',
    '5': 'average (industrial)',
    '6': 'average (industrial)',
    '7': 'average (pre-stellar)',
    '8': 'average (pre-stellar)',
    '9': 'average (pre-stellar)',
    'A': 'advanced (early stellar)',
    'B': 'advanced (average stellar)',
    'C': 'advanced (average stellar)',
    'D': 'advanced (high stellar)',
    'E': 'advanced (high stellar)',
    'F': 'advanced (high stellar)'
}


def uwp_summary(uwp: str) -> str:
    """
    Generate a human-readable summary of a UWP code.
    
    Args:
        uwp: The Universal World Profile code (e.g., "A553A85-D")
        
    Returns:
        A string containing a human-readable summary
    """
    if not uwp or len(uwp) < 9:
        return "Invalid UWP code"
    
    try:
        starport = uwp[0]
        size = uwp[1]
        atmosphere = uwp[2]
        hydrographics = uwp[3]
        population = uwp[4]
        government = uwp[5]
        law_level = uwp[6]
        tech_level = uwp[8] if len(uwp) > 8 else '0'
        
        summary_parts = []
        
        # Add starport description
        if starport in STARPORT_CODES:
            summary_parts.append(STARPORT_CODES[starport])
        
        # Add size description
        if size in SIZE_CODES:
            summary_parts.append(SIZE_CODES[size])
        
        # Add atmosphere description
        if atmosphere in ATMOSPHERE_CODES:
            summary_parts.append(f"atmosphere: {ATMOSPHERE_CODES[atmosphere]}")
        
        # Add hydrographics description
        if hydrographics in HYDROGRAPHICS_CODES:
            summary_parts.append(HYDROGRAPHICS_CODES[hydrographics])
        
        # Add population description
        if population in POPULATION_CODES:
            summary_parts.append(f"population: {POPULATION_CODES[population]}")
        
        # Add government description
        if government in GOVERNMENT_CODES:
            summary_parts.append(f"government: {GOVERNMENT_CODES[government]}")
        
        # Add law level description
        if law_level in LAW_LEVEL_CODES:
            summary_parts.append(LAW_LEVEL_CODES[law_level])
        
        # Add tech level description
        if tech_level in TECH_LEVEL_CODES:
            summary_parts.append(f"TL-{tech_level} ({TECH_LEVEL_CODES[tech_level]})")
        
        return ", ".join(summary_parts)
    
    except Exception as e:
        logger.error(f"Error parsing UWP code '{uwp}': {e}")
        return "Error parsing UWP code"


def get_environment_type(uwp: str) -> str:
    """
    Determine the environment type based on UWP code.
    
    Args:
        uwp: The Universal World Profile code
        
    Returns:
        A string describing the environment type
    """
    if not uwp or len(uwp) < 4:
        return "unknown environment"
    
    try:
        atmosphere = uwp[2]
        hydrographics = uwp[3]
        
        atmo_level = ord(atmosphere) - ord('0') if atmosphere.isdigit() else 0
        hydro_level = ord(hydrographics) - ord('0') if hydrographics.isdigit() else 0
        
        if atmo_level in [0, 1, 2, 3, 10, 11, 12, 13, 14, 15]:
            return "hostile environment"
        elif hydro_level >= 8:
            return "water world"
        elif hydro_level <= 2:
            return "desert world"
        else:
            return "habitable world"
    
    except Exception as e:
        logger.error(f"Error determining environment type for UWP '{uwp}': {e}")
        return "unknown environment"


def get_tech_context(uwp: str) -> str:
    """
    Determine the technology context based on UWP code.
    
    Args:
        uwp: The Universal World Profile code
        
    Returns:
        A string describing the technology context
    """
    if not uwp or len(uwp) < 9:
        return "unknown tech level"
    
    try:
        tech_level = uwp[8]
        tech_level_num = ord(tech_level) - ord('0') if tech_level.isdigit() else 0
        
        if tech_level_num <= 4:
            return "low tech"
        elif tech_level_num <= 9:
            return "moderate tech"
        elif tech_level_num <= 12:
            return "high tech"
        else:
            return "very high tech"
    
    except Exception as e:
        logger.error(f"Error determining tech context for UWP '{uwp}': {e}")
        return "unknown tech level"


def get_population_density(uwp: str) -> str:
    """
    Determine the population density based on UWP code.
    
    Args:
        uwp: The Universal World Profile code
        
    Returns:
        A string describing the population density
    """
    if not uwp or len(uwp) < 5:
        return "unknown population"
    
    try:
        population = uwp[4]
        pop_level = ord(population) - ord('0') if population.isdigit() else 0
        
        if pop_level <= 3:
            return "sparse population"
        elif pop_level <= 6:
            return "moderate population"
        elif pop_level <= 9:
            return "dense population"
        else:
            return "teeming megacities"
    
    except Exception as e:
        logger.error(f"Error determining population density for UWP '{uwp}': {e}")
        return "unknown population"
