import os
import sqlite3
import mysql.connector

class TravellerDatabase:
    _instance = None

    def __new__(cls, db_type=None, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TravellerDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_type=None):
        if not self._initialized:
            self.db_type = db_type
            if db_type == 'sqlite':
                self.conn = sqlite3.connect(os.getenv('DB_URL'))
            elif db_type == 'mysql':
                self.conn = mysql.connector.connect(
                    host=os.getenv('DB_HOST'),
                    user=os.getenv('DB_USERNAME'),
                    password=os.getenv('DB_PASSWORD'),
                    database=os.getenv('DB_NAME')
                )
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
            print(f"Error executing script: {e}")
            return -1

    def sanity_check(self, table, data):
        if not isinstance(data, dict) or not table:
            return False
        return True

    def create_record(self, table, data):
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
            print(f"Error creating record: {e}")
            return -1

    def read_records(self, table, conditions=None):
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
            print(f"Error reading records: {e}")
            return []

    def update_record(self, table, data, conditions):
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
            print(f"Error updating record: {e}")
            return -1

    def delete_record(self, table, conditions):
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
            print(f"Error deleting record: {e}")
            return -1

    def close(self):
        self.conn.close()
        self._initialized = False  # Allow reinitialization if needed
