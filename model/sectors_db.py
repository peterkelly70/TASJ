from typing import List, Optional, Set, Tuple


class SectorDB:
    def __init__(self, db_instance):
        """Initialize the SectorDB with a valid database instance."""
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
        Returns the new sector_id if the record was created successfully, None otherwise.
        """
        result = self.db.create_record("sectors", data)
        if result == 1:
            print(f"Sector '{data.get('name')}' created successfully.")
            record = self.get_sector_by_name(data.get("name"))
            return record[0] if record else None
        else:
            print(f"Failed to create sector '{data.get('name')}'.")
            return None

    def upsert_sector(self, data) -> Optional[int]:
        """
        Updates an existing sector record if it exists; otherwise, creates a new one.
        Expects data to contain at least a 'name' key.
        Returns the sector_id if successful, otherwise None.
        """
        sector_name = data.get("name")
        if not sector_name:
            print("Sector name is required for upsert.")
            return None

        existing = self.get_sector_by_name(sector_name)
        if existing:
            result = self.db.update_record("sectors", data, {"name": sector_name})
            if result == 1:
                print(f"Successfully updated sector '{sector_name}'.")
            else:
                print(f"Failed to update sector '{sector_name}'.")
            # Refresh to capture any updated values
            updated = self.get_sector_by_name(sector_name)
            return updated[0] if updated else None

        created_id = self.create_sector(data)
        if created_id is not None:
            print(f"Successfully created sector '{sector_name}'.")
        else:
            print(f"Failed to create sector '{sector_name}'.")
        return created_id

    # --- Query helpers for controllers ---

    def list_sector_names(self) -> List[str]:
        """Return all sector names ordered alphabetically."""
        rows = self.db.execute_query("SELECT name FROM sectors ORDER BY name")
        return [row[0] for row in rows]

    def list_sector_records(self) -> List[Tuple[int, str, Optional[str]]]:
        """Return (sector_id, name, abbreviation) tuples for all sectors."""
        rows = self.db.execute_query(
            "SELECT sector_id, name, abbreviation FROM sectors ORDER BY name"
        )
        return [(row[0], row[1], row[2] if len(row) > 2 else None) for row in rows]

    def list_systems_by_sector(self, sector_id: int) -> List[Tuple[str, str]]:
        """Return distinct (hex, name) pairs for systems within a sector."""
        rows = self.db.execute_query(
            "SELECT hex, name FROM planets WHERE sector_id = ? AND hex IS NOT NULL ORDER BY hex",
            (sector_id,),
        )

        systems: List[Tuple[str, str]] = []
        seen: Set[str] = set()
        for hex_code, name in rows:
            hex_code = (hex_code or "").strip()
            if not hex_code or hex_code in seen:
                continue
            seen.add(hex_code)
            systems.append((hex_code, (name or "").strip()))
        return systems
