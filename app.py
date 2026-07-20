import os
import json
import math
import requests
from flask import Flask, render_template, request, abort
from dotenv import load_dotenv

# Load environment variables
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
    
# Fallback distance calculations
def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    latitude_distance = lat2 - lat1
    longitude_distance = lon2 - lon1
    
    a = math.sin(latitude_distance/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(longitude_distance/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# API matrix routing
def batch_calculate_distances(user_lat, user_lon, restaurants):
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
                    distance_map[restaurant["name"]] = raw_distance / 1000.0
                else:
                    distance_map[restaurant["name"]] = calculate_haversine(user_lat, user_lon, restaurant["lat"], restaurant["lon"])
            return distance_map
    except (requests.exceptions.RequestException, KeyError, ValueError):
        pass

    for restaurant in restaurants:
        distance_map[restaurant["name"]] = calculate_haversine(user_lat, user_lon, restaurant["lat"], restaurant["lon"])
    return distance_map


def filter_by_hard_constraints(user_prefs, knowledge_base, calculated_distances):
    surviving_restaurants = []
    
    for restaurant in knowledge_base:
        # 1. Dietary constraint check
        user_diet = user_prefs.get("dietary", "None")
        if user_diet != "None":
            if user_diet not in restaurant.get("dietary_options", []):
                continue
        
        # 2. Budget tier check
        user_budget = user_prefs.get("budget", "Any")
        if user_budget != "Any":
            if restaurant.get("budget_tier") != user_budget:
                continue
        
        # 3. Distance range check
        actual_distance = calculated_distances.get(restaurant["name"], 0)
        max_allowed_distance = user_prefs.get("max_distance")
        if max_allowed_distance:
            if actual_distance > float(max_allowed_distance):
                continue
            
        surviving_restaurants.append(restaurant)
        
    return surviving_restaurants


def calculate_match_scores(user_prefs, surviving_restaurants):
    scored_recommendations = []
    user_cuisine = user_prefs.get("cuisine", "Any")
    
    for restaurant in surviving_restaurants:
        score = 50.0
        
        # 1. Cuisine matching (+30 points)
        if user_cuisine != "Any":
            if restaurant.get("cuisine") == user_cuisine:
                score += 30
        
        # 2. Dynamic rating factor from your new data structure (+20 points max)
        # We calculate an aggregate performance average from quality, aesthetics, and service
        quality = float(restaurant.get("quality_of_food", 4))
        aesthetics = float(restaurant.get("aesthetics", 4))
        service = float(restaurant.get("customer_service", 4))
        
        calculated_rating = round((quality + aesthetics + service) / 3.0, 1)
        score += (calculated_rating * 4.0)
        
        if score > 100.0:
            score = 100.0 
            
        scored_item = restaurant.copy()
        scored_item["match_score"] = round(score, 1)
        scored_item["rating"] = calculated_rating # Smooth compatibility injection for templates
        
        scored_recommendations.append(scored_item)
        
    scored_recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_recommendations


def run_inference_engine(user_prefs, knowledge_base):
    user_lat = float(user_prefs.get("lat", -1.2833))
    user_lon = float(user_prefs.get("lon", 36.8219))
    
    calculated_distances = batch_calculate_distances(user_lat, user_lon, knowledge_base)
    surviving_restaurants = filter_by_hard_constraints(user_prefs, knowledge_base, calculated_distances)
    final_ranked_recommendations = calculate_match_scores(user_prefs, surviving_restaurants)
    
    return final_ranked_recommendations



# FLASK ROUTES

# Page 1: Landing Page
@app.route("/")
def landing_page():
    return render_template("landing.html")


# Page 2: Discovery Page
@app.route("/discover", methods=["GET", "POST"])
def discover_page():
    # Pulls directly from your real local restaurants.json file!
    restaurants_db = load_knowledge_base()
    
    user_preferences = {
        "lat": -1.2833, "lon": 36.8219,
        "dietary": "None", "budget": "Any", "cuisine": "Any", "max_distance": "10.0"
    }
    
    if request.method == "POST":
        user_preferences["dietary"] = request.form.get("dietary_restriction", "None")
        user_preferences["budget"] = request.form.get("budget_tier", "Any")
        user_preferences["cuisine"] = request.form.get("preferred_cuisine", "Any")
        user_preferences["max_distance"] = request.form.get("distance_radius", "10.0")
        
        search_query = request.form.get("search_query", "").lower()
        if search_query:
            restaurants_db = [
                r for r in restaurants_db 
                if search_query in r["name"].lower() or 
                   search_query in r.get("description", "").lower() or 
                   search_query in r.get("cuisine", "").lower() or
                   search_query in r.get("location", "").lower()
            ]
  
    results = run_inference_engine(user_preferences, restaurants_db)
    return render_template("discover.html", restaurants=results, current_filters=user_preferences)


# Page 3: Dedicated Detailed View Page
@app.route('/restaurant/<string:res_name>')
def detail_page(res_name):
    db = load_knowledge_base()
    
    # Safely scan your JSON structure using the unique text names as routing parameters
    restaurant_match = next((item for item in db if item["name"].lower() == res_name.lower()), None)
    
    if not restaurant_match:
        abort(404)
        
    # Standard template fallback injection for description fields
    if "description" not in restaurant_match:
        restaurant_match["description"] = f"A popular gathering spot in {restaurant_match.get('location', 'Nairobi')} specializing in local {restaurant_match.get('cuisine')} culinary crafts."
        
    # Injecting safe calculated fields to keep UI layouts clean
    q = restaurant_match.get("quality_of_food", 4)
    a = restaurant_match.get("aesthetics", 4)
    s = restaurant_match.get("customer_service", 4)
    restaurant_match["rating"] = round((q + a + s) / 3.0, 1)
    
    # Mock fallback hours/contact values if missing in JSON schema
    if "hours" not in restaurant_match:
        restaurant_match["hours"] = "10:00 AM - 10:00 PM"
    if "phone" not in restaurant_match:
        restaurant_match["phone"] = "+254 700 123 456"
        
    # Mocking custom signature delicacies showcase grid cards
    sample_menu = [
        {"name": "House Special Entrée", "img": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500"},
        {"name": "Artisanal Side Dish", "img": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=500"},
        {"name": "Gourmet Dessert Selection", "img": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=500"}
    ]
    
    lat = restaurant_match.get("lat", -1.2833)
    lon = restaurant_match.get("lon", 36.8219)
    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    
    return render_template(
        "detail.html", 
        restaurant=restaurant_match, 
        menu=sample_menu, 
        maps_url=maps_url
    )

if __name__ == "__main__":
    app.run(debug=True)