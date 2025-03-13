import sqlite3

class JumpsDB:
    def __init__(self, db_instance):
        self.db_instance = db_instance

    def insert_jump(self, jump_data):
        """
        Inserts a new jump route into the database.
        """
        query = """
        INSERT INTO jumps (start_sector, start_hex, end_sector, end_hex, jump_distance, requires_fuel, restricted_zone)
        VALUES (:start_sector, :start_hex, :end_sector, :end_hex, :jump_distance, :requires_fuel, :restricted_zone);
        """
        with self.db_instance as conn:
            conn.execute(query, jump_data)
            conn.commit()
