"""
Mission Generator package for Traveller RPG campaigns.

This package contains modules for generating random missions for planets/systems
using the gamePlanner tables, UWP data, and optionally enhances them using ChatGPT API.
"""

from .mission_generator_base import MissionGenerator

__all__ = ['MissionGenerator']
