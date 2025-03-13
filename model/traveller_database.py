import os
import sqlite3
import mysql.connector
from dotenv import load_dotenv

class TravellerDatabase:
    _instance = None

    def __new__(cls, db_type=None, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TravellerDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_type=None):
        if not self._initialized:
            print(f"Initializing database with type: {db_type}")  # Debug line
            self.db_type = db_type

            # ✅ Ensure `.env` is loaded before retrieving database values
            load_dotenv("config/.env")

            if self.db_type == 'sqlite':
                db_path = os.getenv('DATABASE_FILE_PATH')
                if not db_path:
                    raise ValueError("❌ DATABASE_FILE_PATH is not set in .env or is invalid!")

                self.conn = sqlite3.connect(db_path)
                print(f"✅ Connected to SQLite database at {db_path}")

            elif self.db_type == 'mysql':
                db_host = os.getenv('DATABASE_HOST')
                db_user = os.getenv('DATABASE_USERNAME')
                db_password = os.getenv('DATABASE_PASSWORD')
                db_name = os.getenv('DATABASE_NAME')

                if not all([db_host, db_user, db_password, db_name]):
                    raise ValueError("❌ MySQL database credentials are not fully set in .env!")

                self.conn = mysql.connector.connect(
                    host=db_host,
                    user=db_user,
                    password=db_password,
                    database=db_name
                )
                print(f"✅ Connected to MySQL database {db_name}")

            else:
                raise ValueError(f"❌ Unsupported database type: {self.db_type}")

            self._initialized = True

    def execute_script(self, script):
        try:
            cursor = self.conn.cursor()
            if self.db_type == 'sqlite':
                cursor.executescript(script)
            elif self.db_type == 'mysql':
                for result in cursor.execute(script, multi=True):
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
                condition_string = ' AND '.join([f"{key} = %s" if self.db_type == 'mysql' else f"{key} = ?" for key in conditions.keys()])
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
            condition_string = ' AND '.join([f"{key} = %s" if self.db_type == 'mysql' else f"{key} = ?" for key in conditions.keys()])
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
            condition_string = ' AND '.join([f"{key} = %s" if self.db_type == 'mysql' else f"{key} = ?" for key in conditions.keys()])
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

    def close(self):
        """ Closes the database connection and allows reinitialization. """
        self.conn.close()
        self._initialized = False
