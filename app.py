import os
import json
import math
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

# Load environment variables from the .env file immediately on startup
load_dotenv()

app = Flask(__name__)

ORS_API_KEY = os.environ.get("ORS_API_KEY", "MISSING_API_KEY_IN_ENV")

def load_knowledge_base():
    """Opens and reads the factual knowledge base from the local JSON file."""
    try:
        with open("restaurants.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    
# Fallback heuristics
def calculate_haversine(lat1, lon1, lat2, lon2):
    """Calculates flat sphere distance when the API drops or hits rate limits"""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    latitude_distance = lat2 - lat1
    longitude_distance = lon2 - lon1
    
    a = math.sin(latitude_distance/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(longitude_distance/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

# API matrix
def batch_calculate_distances(user_lat, user_lon, restaurants):
    """Provides real road distances for all restaurants via OpenRouteService"""
    if not restaurants:
        return {}
    
    user_coordinates = [user_lon, user_lat]
    locations = [user_coordinates]
    for restaurant in restaurants:
        locations.append([restaurant["lon"], restaurant["lat"]])
        
    url = "https://api.openrouteservice.org/v2/matrix/driving-car"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "locations": locations,
        "sources": [0],
        "destinations": list(range(1, len(locations))),
        "metrics": ["distance"]
    }
    
    distance_map = {}
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=4)
        if response.status_code == 200:
            data = response.json()
            api_distances = data["distances"][0]
            
            for index, restaurant in enumerate(restaurants):
                raw_distance = api_distances[index]
                if raw_distance is not None:
                    distance_map[restaurant["name"]] = raw_distance/1000.0
                else:
                    distance_map[restaurant["name"]] = calculate_haversine(user_lat, user_lon, restaurant["lat"], restaurant["lon"])
            return distance_map
    except (requests.exceptions.RequestException, KeyError, ValueError):
        pass

    for restaurant in restaurants:
        distance_map[restaurant["name"]] = calculate_haversine(user_lat, user_lon, restaurant["lat"], restaurant["lon"])
    return distance_map



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Grab the database records
        restaurants_list = load_knowledge_base()
        
        # Hardcoded coordinates for USIU area/Nairobi testing to feed the distance engine
        user_lat, user_lon = -1.221, 36.883 
        
        # Calculate distances using your teammate's backend matrix
        distances = batch_calculate_distances(user_lat, user_lon, restaurants_list)
        
        # Attach the calculated distances and a mock rating for your UI layout to display
        for r in restaurants_list:
            r['distance'] = round(distances.get(r['name'], 0.0), 1)
            r['match_rating'] = 4 # Temporary visual placeholder for stars
            r['description'] = f"A great spot located in {r.get('location', 'Nairobi')}."

        return render_template('search.html', restaurants=restaurants_list)
    
    return render_template('search.html', restaurants=[])

if __name__ == '__main__':
    app.run(debug=True)