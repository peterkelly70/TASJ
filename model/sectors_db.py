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
            # Optionally, merge or update specific fields
            result = self.db.update_record("sectors", data, {"name": sector_name})
            if result == 1:
                print(f"Successfully updated sector '{sector_name}'.")
                return True
            else:
                print(f"Failed to update sector '{sector_name}'.")
                return False
        else:
            result = self.db.create_record("sectors", data)
            if result == 1:
                print(f"Successfully created sector '{sector_name}'.")
                return True
            else:
                print(f"Failed to create sector '{sector_name}'.")
                return False
