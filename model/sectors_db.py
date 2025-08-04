class SectorDB:
    def __init__(self, db_instance):
        """
        Initialize the SectorDB with a valid database instance.
        """
        self.db = db_instance

    def get_sector_by_name(self, sector_name):
        """
        Retrieves the sector record for the given sector name.
        Returns the first matching record (as a tuple) or None if not found.
        Assumes the 'sectors' table has a unique 'name' field.
        """
        conditions = {"name": sector_name}
        records = self.db.read_records("sectors", conditions)
        return records[0] if records else None

    def update_sector_image(self, sector_name, image_path):
        """
        Updates the image_path for the specified sector in the sectors table.
        Uses the db_instance's update_record() method.
        Returns True if the update was successful, False otherwise.
        """
        data = {"image_path": image_path}
        conditions = {"name": sector_name}
        result = self.db.update_record("sectors", data, conditions)
        if result == 1:
            print(f"Successfully updated sector '{sector_name}' with image path '{image_path}'.")
            return True
        else:
            print(f"Failed to update sector '{sector_name}' with image path '{image_path}'.")
            return False

    def create_sector(self, data):
        """
        Creates a new sector record in the sectors table.
        Data should be a dictionary containing at least:
            - name
            - x_coordinate
            - y_coordinate
            - description (optional)
            - image_path (optional)
        Returns True if the record was created successfully, False otherwise.
        """
        result = self.db.create_record("sectors", data)
        if result == 1:
            print(f"Sector '{data.get('name')}' created successfully.")
            return True
        else:
            print(f"Failed to create sector '{data.get('name')}'.")
            return False

    def upsert_sector(self, data):
        """
        Updates an existing sector record if it exists; otherwise, creates a new one.
        Expects data to contain at least a 'name' key.
        Returns True if the operation was successful, False otherwise.
        """
        sector_name = data.get("name")
        if not sector_name:
            print("Sector name is required for upsert.")
            return False

        existing = self.get_sector_by_name(sector_name)
        if existing:
            # For updates, temporarily disable foreign key constraints to avoid conflicts
            try:
                self.db.conn.execute('PRAGMA foreign_keys = OFF')
                result = self.db.update_record("sectors", data, {"name": sector_name})
                self.db.conn.execute('PRAGMA foreign_keys = ON')
                self.db.conn.commit()
                
                if result == 1:
                    print(f"Successfully updated sector '{sector_name}'.")
                    return True
                else:
                    print(f"Failed to update sector '{sector_name}'.")
                    return False
            except Exception as e:
                # Re-enable foreign keys even if there's an error
                self.db.conn.execute('PRAGMA foreign_keys = ON')
                self.db.conn.commit()
                print(f"Error updating sector '{sector_name}': {e}")
                return False
        else:
            result = self.db.create_record("sectors", data)
            if result == 1:
                print(f"Successfully created sector '{sector_name}'.")
                return True
            else:
                print(f"Failed to create sector '{sector_name}'.")
                return False
                
    def get_all_sectors(self):
        """
        Retrieves all sectors from the database.
        Returns a list of dictionaries, each representing a sector.
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT * FROM sectors")
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        except Exception as e:
            print(f"Error retrieving sectors: {e}")
            return []
        
    def get_sector_by_id(self, sector_id):
        """
        Retrieves the sector record for the given sector ID.
        Returns the matching record as a dictionary or None if not found.
        """
        conditions = {"id": sector_id}
        records = self.db.read_records("sectors", conditions)
        return records[0] if records else None
        
    def search_sectors(self, search_text):
        """
        Searches for sectors matching the given search text in name or description.
        Returns a list of matching sector dictionaries.
        """
        # Use SQL LIKE for case-insensitive partial matching
        search_pattern = f"%{search_text}%"
        query = "SELECT * FROM sectors WHERE name LIKE ? OR description LIKE ?"
        params = (search_pattern, search_pattern)
        
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        except Exception as e:
            print(f"Error searching sectors: {e}")
            return []
            
    def search_systems(self, search_text):
        """
        Searches for systems matching the given search text in name or UWP.
        Returns a list of matching system dictionaries.
        """
        # Use SQL LIKE for case-insensitive partial matching
        search_pattern = f"%{search_text}%"
        query = "SELECT * FROM systems WHERE name LIKE ? OR UWP LIKE ?"
        params = (search_pattern, search_pattern)
        
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        except Exception as e:
            print(f"Error searching systems: {e}")
            return []
            
    def get_systems_for_sector(self, sector_id):
        """
        Retrieves all systems for the given sector ID.
        Returns a list of system dictionaries.
        """
        conditions = {"sector_id": sector_id}
        records = self.db.read_records("systems", conditions)
        return records
        
    def get_planets_for_system(self, system_id):
        """
        Retrieves all planets for the given system ID.
        Returns a list of planet dictionaries.
        """
        conditions = {"system_id": system_id}
        records = self.db.read_records("planets", conditions)
        return records
