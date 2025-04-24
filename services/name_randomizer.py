import requests
import json

def generate_scifi_names(type_name="Star Wars", gender="Male", count=1):
    """
    Generate random sci-fi names by calling an external API.
    
    Args:
        type_name (str): The sci-fi universe type ("Star Wars" or "Cyberpunk")
        gender (str): Gender for the name ("Male" or "Female")
        count (int): Number of names to generate
        
    Returns:
        list: A list of generated names or None if the request failed
    """
    
    # Validate inputs
    if type_name not in ["Star Wars", "Cyberpunk"]:
        raise ValueError("type_name must be 'Star Wars' or 'Cyberpunk'")
    
    if gender not in ["Male", "Female"]:
        raise ValueError("gender must be 'Male' or 'Female'")
    
    if not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer")
    
    # Construct the URL
    base_url = "https://donjon.bin.sh/name/rpc-name.fcgi"
    query_params = {
        "type": f"{type_name} {gender}",
        "n": count,
        "as_json": 1
    }
    
    try:
        # Make the request
        response = requests.get(base_url, params=query_params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse the response
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error generating names: {str(e)}")
        return None

# Example usage:
# star_wars_names = generate_scifi_names(type_name="Star Wars", gender="Male", count=1)
# cyberpunk_names = generate_scifi_names(type_name="Cyberpunk", gender="Female", count=2)
# print(star_wars_names)
# print(cyberpunk_names)