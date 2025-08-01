"""
OpenAI client module for the mission generator.

This module provides functions to create and manage OpenAI API clients
for use in mission generation.
"""

import os
import logging
from typing import Optional, Any

# Check if OpenAI is available
OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

# Set up logger
logger = logging.getLogger(__name__)


def get_openai_client(api_key: Optional[str] = None) -> Optional[Any]:
    """
    Get an OpenAI client instance if the API is available.
    
    Args:
        api_key: Optional API key to use. If not provided, will try to use environment variable.
        
    Returns:
        OpenAI client instance or None if not available
    """
    if not OPENAI_AVAILABLE:
        logger.warning("OpenAI package not installed. Cannot create client.")
        return None
        
    # Use provided API key or get from environment
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        logger.warning("No OpenAI API key available. Cannot create client.")
        return None
        
    try:
        client = OpenAI(api_key=key)
        return client
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {e}")
        return None
