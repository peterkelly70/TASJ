"""
Game Planner Tables module for the mission generator.

This module provides functionality for loading and using the Traveller
Game Planner tables for mission generation.
"""

import os
import json
import random
import logging
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

class GamePlannerTables:
    """
    Handles loading and using the Game Planner tables for mission generation.
    """
    
    def __init__(self):
        """Initialize the game planner tables."""
        self.tables = {}
        
    def load_tables(self) -> Dict[str, Any]:
        """
        Load the game planner tables from the data file.
        
        Returns:
            Dict containing the game planner tables
        """
        if self.tables:
            return self.tables
            
        # Find the game planner file
        project_root = Path(__file__).parent.parent.parent
        game_planner_file = project_root / "gamePlanner.txt"
        
        if not game_planner_file.exists():
            logger.error(f"Game planner file not found at {game_planner_file}")
            return {}
            
        try:
            # Parse the game planner file
            tables = self._parse_game_planner_file(game_planner_file)
            self.tables = tables
            return tables
        except Exception as e:
            logger.error(f"Error loading game planner tables: {e}")
            return {}
    
    def _parse_game_planner_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse the game planner file into a structured format.
        
        Args:
            file_path: Path to the game planner file
            
        Returns:
            Dict containing the parsed tables
        """
        tables = {}
        current_phase = None
        current_table = None
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Check for phase header
                if line.startswith("PHASE"):
                    current_phase = line
                    tables[current_phase] = {}
                    continue
                    
                # Check for table header
                if current_phase and line.startswith("TABLE"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        table_num = parts[0].replace("TABLE", "").strip()
                        table_name = parts[1].strip()
                        
                        tables[current_phase][table_num] = {
                            "name": table_name,
                            "entries": {}
                        }
                        current_table = table_num
                    continue
                    
                # Parse table entries
                if current_phase and current_table and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        entry_id = parts[0].strip()
                        entry_text = parts[1].strip()
                        
                        # Check for reference
                        reference = None
                        if "(" in entry_text and entry_text.endswith(")"):
                            ref_start = entry_text.rfind("(")
                            ref_text = entry_text[ref_start+1:-1].strip()
                            
                            # Check if reference is to another table
                            if ref_text.isdigit() or ref_text.startswith("PHASE"):
                                reference = ref_text
                                entry_text = entry_text[:ref_start].strip()
                        
                        tables[current_phase][current_table]["entries"][entry_id] = {
                            "name": entry_text,
                            "reference": reference
                        }
        
        return tables
    
    def roll_on_table(self, phase: str, table_id: str) -> Tuple[str, str, Optional[str]]:
        """
        Roll on a specific table to get a random result.
        
        Args:
            phase: The phase containing the table (e.g., "PHASE 1")
            table_id: The table ID within the phase (e.g., "1")
            
        Returns:
            Tuple of (entry name, entry ID, reference to next table)
        """
        if not self.tables:
            self.load_tables()
            
        # Check if the phase and table exist
        if phase not in self.tables or table_id not in self.tables[phase]:
            logger.warning(f"Table {phase}.{table_id} not found")
            return "Unknown", "0", None
            
        # Get the table entries
        table = self.tables[phase][table_id]
        entries = table.get("entries", {})
        
        if not entries:
            logger.warning(f"No entries found in table {phase}.{table_id}")
            return "Unknown", "0", None
            
        # Roll on the table
        entry_id = random.choice(list(entries.keys()))
        entry = entries[entry_id]
        
        return entry.get("name", "Unknown"), entry_id, entry.get("reference")
    
    def get_table_info(self, phase: str, table_id: str) -> Dict[str, Any]:
        """
        Get information about a specific table.
        
        Args:
            phase: The phase containing the table (e.g., "PHASE 1")
            table_id: The table ID within the phase (e.g., "1")
            
        Returns:
            Dict containing table information
        """
        if not self.tables:
            self.load_tables()
            
        # Check if the phase and table exist
        if phase not in self.tables or table_id not in self.tables[phase]:
            logger.warning(f"Table {phase}.{table_id} not found")
            return {"name": f"Unknown Table {table_id}", "entries": {}}
            
        return self.tables[phase][table_id]
