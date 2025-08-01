#!/usr/bin/env python3
"""
Script to convert mission tables from gamePlanner.txt to SQLite database.
This script parses the gamePlanner.txt file and creates a structured SQLite database.
"""

import sqlite3
import os
import sys
import logging
import re
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the path so we can import modules properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class MissionTablesConverter:
    """Converts mission tables from text format to SQLite database."""
    
    def __init__(self, input_file, output_db, schema_file=None):
        """
        Initialize the converter.
        
        Args:
            input_file (str): Path to the gamePlanner.txt file
            output_db (str): Path to the output SQLite database
            schema_file (str, optional): Path to the schema SQL file
        """
        self.input_file = Path(input_file)
        self.output_db = Path(output_db)
        
        # Default schema file path if not provided
        if schema_file is None:
            project_root = Path(__file__).parent.parent
            schema_file = project_root / "model" / "mission_tables_schema.sql"
        
        self.schema_file = Path(schema_file)
    
    def parse_game_planner_file(self):
        """
        Parse the gamePlanner.txt file and return structured data.
        
        Returns:
            dict: Dictionary containing the parsed game planner tables
        """
        if not self.input_file.exists():
            logger.error(f"Game planner file not found: {self.input_file}")
            return {}
        
        with open(self.input_file, 'r') as file:
            content = file.read()
        
        # Parse the tables
        phases = []
        tables = []
        entries = []
        
        current_phase_id = 0
        current_phase_name = None
        current_table_id = 0
        current_table = None
        
        logger.info(f"Starting to parse game planner file: {self.input_file}")
        
        # Process each line
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
            
            # Phase line (e.g., "PHASE 1")
            if line.startswith('PHASE'):
                current_phase_name = line
                current_phase_id += 1
                phases.append({
                    'id': current_phase_id,
                    'name': current_phase_name
                })
                logger.debug(f"Line {line_num}: Found phase: {current_phase_name} (ID: {current_phase_id})")
                continue
            
            # Table header line (e.g., "1 General Type of Scenario")
            table_match = re.match(r'^(\d+)\s+(.+)$', line)
            if table_match and current_phase_id > 0:
                table_number = table_match.group(1)
                table_name = table_match.group(2)
                current_table_id += 1
                current_table = {
                    'id': current_table_id,
                    'phase_id': current_phase_id,
                    'table_number': table_number,
                    'name': table_name
                }
                tables.append(current_table)
                logger.debug(f"Line {line_num}: Found table: {table_number} {table_name} (ID: {current_table_id})")
                continue
            
            # Table entry line (e.g., "1. Investigation (2)")
            entry_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if entry_match and current_table_id > 0:
                entry_number = entry_match.group(1)
                entry_content = entry_match.group(2)
                
                # Extract the reference in parentheses if present
                reference = None
                entry_name = entry_content
                
                # Look for reference at the end in parentheses
                ref_match = re.search(r'\((\d+)\)$', entry_content)
                if ref_match:
                    reference = ref_match.group(1)
                    entry_name = entry_content[:ref_match.start()].strip()
                
                entry = {
                    'table_id': current_table_id,
                    'entry_number': entry_number,
                    'name': entry_name,
                    'reference_table': reference
                }
                entries.append(entry)
                logger.debug(f"Line {line_num}: Found entry: {entry_number}. {entry_name} (Ref: {reference})")
        
        logger.info(f"Parsed {len(phases)} phases, {len(tables)} tables, and {len(entries)} entries")
        
        return {
            'phases': phases,
            'tables': tables,
            'entries': entries
        }
    
    def create_database(self):
        """
        Create the SQLite database with the schema.
        
        Returns:
            tuple: (connection, cursor) if successful, (None, None) otherwise
        """
        try:
            # Create parent directory if it doesn't exist
            self.output_db.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to the database
            conn = sqlite3.connect(self.output_db)
            cursor = conn.cursor()
            
            # Create tables from schema
            if self.schema_file.exists():
                with open(self.schema_file, 'r') as f:
                    schema_sql = f.read()
                    cursor.executescript(schema_sql)
                logger.info(f"Created database schema from {self.schema_file}")
            else:
                logger.error(f"Schema file not found: {self.schema_file}")
                conn.close()
                return None, None
            
            return conn, cursor
        
        except Exception as e:
            logger.error(f"Error creating database: {str(e)}")
            return None, None
    
    def populate_database(self, data, conn, cursor):
        """
        Populate the SQLite database with the parsed data.
        
        Args:
            data (dict): Dictionary containing the parsed game planner tables
            conn: SQLite connection
            cursor: SQLite cursor
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Insert phases
            for phase in data.get('phases', []):
                try:
                    cursor.execute(
                        "INSERT INTO phases (id, name) VALUES (?, ?)",
                        (phase['id'], phase['name'])
                    )
                except sqlite3.IntegrityError:
                    logger.warning(f"Duplicate phase ID: {phase['id']} - skipping")
            
            # Insert tables
            for table in data.get('tables', []):
                try:
                    cursor.execute(
                        "INSERT INTO tables (id, phase_id, table_number, name) VALUES (?, ?, ?, ?)",
                        (table['id'], table['phase_id'], table['table_number'], table['name'])
                    )
                except sqlite3.IntegrityError:
                    logger.warning(f"Duplicate table found: Phase {table['phase_id']}, Table {table['table_number']} - skipping")
            
            # Insert entries
            for entry in data.get('entries', []):
                try:
                    cursor.execute(
                        "INSERT INTO entries (table_id, entry_number, name, reference_table) VALUES (?, ?, ?, ?)",
                        (entry['table_id'], entry['entry_number'], entry['name'], entry['reference_table'])
                    )
                except sqlite3.IntegrityError:
                    logger.warning(f"Duplicate entry found: Table {entry['table_id']}, Entry {entry['entry_number']} - skipping")
                except Exception as e:
                    logger.error(f"Error inserting entry {entry}: {str(e)}")
            
            # Commit the changes
            conn.commit()
            
            # Log counts
            cursor.execute("SELECT COUNT(*) FROM phases")
            phase_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tables")
            table_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM entries")
            entry_count = cursor.fetchone()[0]
            
            logger.info(f"Database populated with {phase_count} phases, {table_count} tables, and {entry_count} entries")
            return True
        
        except Exception as e:
            logger.error(f"Error populating database: {str(e)}")
            conn.rollback()
            return False
    
    def convert(self):
        """
        Convert the gamePlanner.txt file to SQLite database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Parse the game planner file
            data = self.parse_game_planner_file()
            if not data:
                logger.error("Failed to parse game planner file or file is empty")
                return False
            
            # Create the database
            conn, cursor = self.create_database()
            if not conn or not cursor:
                logger.error("Failed to create database")
                return False
            
            # Populate the database
            success = self.populate_database(data, conn, cursor)
            
            # Close the connection
            conn.close()
            logger.info("Database connection closed")
            
            if success:
                logger.info(f"Successfully converted game planner file to SQLite database at {self.output_db}")
                return True
            else:
                logger.error("Failed to populate database")
                return False
        
        except Exception as e:
            logger.error(f"Error converting game planner file: {str(e)}")
            return False


def main():
    """Main function to run the conversion."""
    # Define paths
    project_root = Path(__file__).parent.parent
    input_file = project_root / "gamePlanner.txt"
    output_db = project_root / "data" / "mission_tables.db"
    schema_file = project_root / "model" / "mission_tables_schema.sql"
    
    # Create converter and run conversion
    converter = MissionTablesConverter(input_file, output_db, schema_file)
    success = converter.convert()
    
    if success:
        print(f"Conversion successful! Database created at {output_db}")
        return 0
    else:
        print("Conversion failed. Check the logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
