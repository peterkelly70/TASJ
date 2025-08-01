import os
import sqlite3
from dotenv import load_dotenv

# Only import mysql.connector when needed
mysql_connector = None

# Flag to check if MySQL is available
MYSQL_AVAILABLE = False

# Try to import mysql.connector, but don't fail if it's not available
try:
    import mysql.connector as mysql_connector
    MYSQL_AVAILABLE = True
except ImportError:
    # MySQL is not available, but that's okay
    pass

# Constants
AND_SEPARATOR = ' AND '

class TravellerDatabase:
    _instance = None

    def __new__(cls, db_type=None, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TravellerDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_type=None):
        if not self._initialized:
            # Default to SQLite if no database type is specified
            if db_type is None:
                db_type = 'sqlite'
                
            print(f"Initializing database with type: {db_type}")  # Debug line
            self.db_type = db_type

            # ✅ Ensure `.env` is loaded before retrieving database values
            load_dotenv("config/.env")

            self._initialize_connection()
            self._initialized = True
            
    def _initialize_connection(self):
        """Initialize the database connection based on the database type."""
        if self.db_type == 'sqlite':
            self._initialize_sqlite_connection()
        elif self.db_type == 'mysql':
            self._initialize_mysql_connection()
        else:
            raise ValueError(f"❌ Unsupported database type: {self.db_type}")
    
    def _initialize_sqlite_connection(self):
        """Initialize SQLite database connection."""
        db_path = os.getenv('DATABASE_FILE_PATH')
        if not db_path:
            raise ValueError("❌ DATABASE_FILE_PATH is not set in .env or is invalid!")

        self.conn = sqlite3.connect(db_path)
        print(f"✅ Connected to SQLite database at {db_path}")
    
    def _initialize_mysql_connection(self):
        """Initialize MySQL database connection."""
        # Check if MySQL is available
        if not MYSQL_AVAILABLE:
            print("⚠️ MySQL connector not installed. Falling back to SQLite.")
            self.db_type = 'sqlite'
            self._initialize_sqlite_connection()
            return
        
        db_host = os.getenv('DATABASE_HOST')
        db_user = os.getenv('DATABASE_USERNAME')
        db_password = os.getenv('DATABASE_PASSWORD')
        db_name = os.getenv('DATABASE_NAME')

        if not all([db_host, db_user, db_password, db_name]):
            raise ValueError("❌ MySQL database credentials are not fully set in .env!")

        self.conn = mysql_connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        print(f"✅ Connected to MySQL database {db_name}")

    def execute_script(self, script):
        try:
            cursor = self.conn.cursor()
            if self.db_type == 'sqlite':
                cursor.executescript(script)
            elif self.db_type == 'mysql':
                for _ in cursor.execute(script, multi=True):
                    # Process each result if needed
                    pass
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"❌ Error executing script: {e}")
            return -1

    def sanity_check(self, table, data):
        """ Ensures input is a valid dictionary and table name exists. """
        if not isinstance(data, dict) or not table:
            return False
        return True

    def create_record(self, table, data):
        """ Inserts a new record into the given table. """
        if not self.sanity_check(table, data):
            return -1
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s' if self.db_type == 'mysql' else '?' for _ in data])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor = self.conn.cursor()
            cursor.execute(sql, list(data.values()))
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"❌ Error creating record: {e}")
            return -1

    def read_records(self, table, conditions=None):
        """ Retrieves records from a table, with optional conditions. """
        try:
            cursor = self.conn.cursor()
            if conditions:
                condition_string = AND_SEPARATOR.join([f"{key} = %s" if self.db_type == 'mysql' else f"{key} = ?" for key in conditions.keys()])
                sql = f"SELECT * FROM {table} WHERE {condition_string}"
                cursor.execute(sql, list(conditions.values()))
            else:
                sql = f"SELECT * FROM {table}"
                cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error reading records: {e}")
            return []

    def update_record(self, table, data, conditions):
        """ Updates a record in the database. """
        if not self.sanity_check(table, data):
            return -1
        try:
            set_string = ', '.join([f"{key} = %s" if self.db_type == 'mysql' else f"{key} = ?" for key in data.keys()])
            condition_string = AND_SEPARATOR.join([f"{key} = %s" if self.db_type == 'mysql' else f"{key} = ?" for key in conditions.keys()])
            sql = f"UPDATE {table} SET {set_string} WHERE {condition_string}"
            cursor = self.conn.cursor()
            cursor.execute(sql, list(data.values()) + list(conditions.values()))
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"❌ Error updating record: {e}")
            return -1

    def delete_record(self, table, conditions):
        """ Deletes records based on conditions. """
        if not self.sanity_check(table, conditions):
            return -1
        try:
            condition_string = 'AND_SEPARATOR'.join([f"{key} = %s" if self.db_type == 'mysql' else f"{key} = ?" for key in conditions.keys()])
            sql = f"DELETE FROM {table} WHERE {condition_string}"
            cursor = self.conn.cursor()
            cursor.execute(sql, list(conditions.values()))
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"❌ Error deleting record: {e}")
            return -1

    def get_table_names(self):
        """ Retrieves all table names in the database. """
        try:
            cursor = self.conn.cursor()
            if self.db_type == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            elif self.db_type == 'mysql':
                cursor.execute("SHOW TABLES;")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error fetching table names: {e}")
            return []

    def get_table_columns(self, table_name):
        """ Returns a list of column names for the given table. """
        cursor = self.conn.cursor()
        if self.db_type == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [row[1] for row in cursor.fetchall()]
        elif self.db_type == 'mysql':
            cursor.execute(f"DESCRIBE {table_name}")
            return [row[0] for row in cursor.fetchall()]
        return []

    def column_exists(self, table_name, column_name):
        """ Checks if a column exists in a table. """
        return column_name in self.get_table_columns(table_name)

    def get_planets_for_system(self, system_id):
        """ Retrieves all planets for the given system ID. 
        
        Note: This is a temporary implementation that uses sector_id since the schema
        doesn't have a direct system_id column yet.
        """
        try:
            cursor = self.conn.cursor()
            # Using sector_id as a temporary workaround since the schema doesn't have system_id
            sql = "SELECT * FROM planets WHERE sector_id = ?"
            cursor.execute(sql, [system_id])
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error retrieving planets for system {system_id}: {e}")
            return []

    def close(self):
        """ Closes the database connection and allows reinitialization. """
        self.conn.close()
        self._initialized = False
