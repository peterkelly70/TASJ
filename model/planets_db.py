class PlanetDB:
    def __init__(self, db_instance):
        """
        Initialize the PlanetDB with a valid database instance.
        The db_instance should implement methods like create_record(),
        read_records(), and update_record() as provided by TravellerDatabase.
        """
        self.db = db_instance

    def get_planet_by_name(self, planet_name, sector_id=None):
        """
        Retrieves the planet record for the given planet name.
        Optionally narrows the search by sector_id.
        Returns the first matching record (as a tuple) or None if not found.
        """
        conditions = {"name": planet_name}
        if sector_id is not None:
            conditions["sector_id"] = sector_id
        records = self.db.read_records("planets", conditions)
        return records[0] if records else None

    def create_planet(self, data):
        """
        Creates a new planet record in the planets table.
        
        'data' should be a dictionary containing keys matching your planets schema.
        Expected keys may include:
            - name
            - sector_id
            - x_coordinate
            - y_coordinate
            - UWP
            - description
            - image_path
            - starport
            - size
            - atmosphere
            - hydrographics
            - population
            - government
            - law_level
            - tech_level
            - allegiance
            - stellar
            - gas_giant
            - bases
            - trade_codes
            - travel_code
            - importance
            - economic
            - hex
        Returns True if the record was created successfully, False otherwise.
        """
        result = self.db.create_record("planets", data)
        if result == 1:
            print(f"Planet '{data.get('name')}' created successfully.")
            return True
        else:
            print(f"Failed to create planet '{data.get('name')}'.")
            return False

    def update_planet(self, planet_name, sector_id, data):
        """
        Updates an existing planet record (identified by 'name' and optionally 'sector_id')
        with the provided data dictionary.
        Uses 'UWP' as the field for the world profile.
        Returns True if the update was successful, False otherwise.
        """
        conditions = {"name": planet_name}
        if sector_id is not None:
            conditions["sector_id"] = sector_id
        result = self.db.update_record("planets", data, conditions)
        if result == 1:
            print(f"Planet '{planet_name}' updated successfully.")
            return True
        else:
            print(f"Failed to update planet '{planet_name}'.")
            return False

    def upsert_planet(self, data):
        """
        Performs an upsert (update if exists, insert if not) for a planet record.
        Uses 'name' and 'sector_id' as unique identifiers.
        Returns True if the operation is successful, False otherwise.
        """
        planet = self.get_planet_by_name(data.get("name"), data.get("sector_id"))
        if planet:
            return self.update_planet(data.get("name"), data.get("sector_id"), data)
        else:
            return self.create_planet(data)
