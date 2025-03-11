import requests

BASE_URL = "https://travellermap.com/api"

def get_sector_data(sector_name):
    url = f"{BASE_URL}/sec?sector={sector_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text  # Returns the sector data in SEC format
    else:
        print(f"Error fetching sector {sector_name}: {response.status_code}")
        return None

# Example usage
print(get_sector_data("Spinward Marches"))
