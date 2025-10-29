import os
import json
import requests

class TravellerMapAPI:
    def __init__(self, base_url="https://travellermap.com", timeout: int = 30):
        # Base URL should not include the trailing /data; we'll add it as needed.
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    # -----------------------------
    # Universe Endpoints
    # -----------------------------
    def get_universe(self):
        """
        Retrieves the universe data.
        Endpoint: https://travellermap.com/data
        Returns: A JSON object with a "Sectors" key.
        """
        url = f"{self.base_url}/data"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        # Get the sectors list from the JSON response.
        
        return response.json()

    # -----------------------------
    # Sector Endpoints
    # -----------------------------
    def get_sector_sec(self, sector):
        """
        Retrieves sector data in legacy SEC format.
        Endpoint: https://travellermap.com/data/sector/sec
        Parameters:
        sector: Sector name or T5SS abbreviation.
        Returns: Text data.
        """
        url = f"{self.base_url}/data/sector/sec"
        params = {"sector": sector}
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def parse_sec_line(self, line):
        """
        Parses a single line of SEC data.
        Expected format: HEX NAME UPP [other tokens...]
        Returns a dictionary with keys: 'hex', 'name', 'upp', and optionally 'raw_data'
        """
        tokens = line.split()
        if len(tokens) < 3:
            return None
        data = {"hex": tokens[0], "name": tokens[1], "upp": tokens[2]}
        if len(tokens) > 3:
            data["raw_data"] = " ".join(tokens[3:])
        return data
    
    def get_sector_tab(self, sector: str, fmt: str = "tab") -> str:
        """Retrieve sector data in the requested tabular format (tab, tab.2e, tab.fx, etc.)."""
        url = f"{self.base_url}/data/sector/{fmt}"
        params = {"sector": sector}
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def download_sector_image(self, sector, save_path=None):
        url = f"{self.base_url}/data/sector/image"
        params = {"sector": sector}
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        if not save_path:
            folder = os.path.join("database", "content", "images", "sector")
            os.makedirs(folder, exist_ok=True)
            save_path = os.path.join(folder, f"{sector.replace(' ', '_')}_map.png")
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path

    # (Other endpoint methods omitted for brevity.)

# Example usage:
if __name__ == "__main__":
    api = TravellerMapAPI()
    try:
        # Retrieve the universe data.
        universe_json = api.get_universe()
        print("Universe data (partial):", json.dumps(universe_json, indent=2)[:500] + "...")
        
        # Extract the sectors list.
        if not (isinstance(universe_json, dict) and "Sectors" in universe_json):
            raise Exception("Universe data does not contain 'Sectors'.")
        sectors_list = universe_json["Sectors"]
        
        # Extract sector names from each entry.
        sector_names = []
        for sector_entry in sectors_list:
            if isinstance(sector_entry, dict):
                # Try to extract the name from the first element in the "Names" list.
                name = ""
                if "Names" in sector_entry and isinstance(sector_entry["Names"], list) and sector_entry["Names"]:
                    name = sector_entry["Names"][0].get("Text", "")
                if not name:
                    name = sector_entry.get("Abbreviation", "")
                if name:
                    sector_names.append(name)
        
        print("Retrieved sectors: " + ", ".join(sector_names))
        
        # Process each sector.
        for sector_entry in sectors_list:
            if not isinstance(sector_entry, dict):
                continue
            
            # Extract the sector name.
            sector_name = ""
            if "Names" in sector_entry and isinstance(sector_entry["Names"], list) and sector_entry["Names"]:
                sector_name = sector_entry["Names"][0].get("Text", "")
            if not sector_name:
                sector_name = sector_entry.get("Abbreviation", "")
            if not sector_name:
                print("Skipping sector due to missing name/abbreviation.")
                continue
            
            print(f"\nProcessing sector: {sector_name}")
            
            # Get sector T5 data (showing only a truncated portion).
            try:
                t5_data = api.get_sector_tab(sector_name)
                display_data = t5_data[:200] + "..." if len(t5_data) > 200 else t5_data
                print("Sector T5 data:", display_data)
            except Exception as e:
                print(f"Error getting T5 data for sector '{sector_name}':", e)
            
            # Download sector map image.
            try:
                image_path = api.download_sector_image(sector_name)
                print("Sector image saved at:", image_path)
            except Exception as e:
                print(f"Error downloading sector image for '{sector_name}':", e)
            
            # (Additional processing can be added here.)

    except Exception as e:
        print("Error:", e)
