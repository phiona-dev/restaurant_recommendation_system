import os
import json
import math
import requests
from flask import Flask, render_template, request, abort, jsonify
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
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    latitude_distance = lat2 - lat1
    longitude_distance = lon2 - lon1
    
    a = math.sin(latitude_distance/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(longitude_distance/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# API matrix routing
def batch_calculate_distances(user_lat, user_lon, restaurants):
    if not restaurants:
        return {}
    
    distance_map = {}
    user_coordinates = [float(user_lon), float(user_lat)]
    locations = [user_coordinates]
    for restaurant in restaurants:
        locations.append([float(restaurant["lon"]), float(restaurant["lat"])])
        
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

    # Fallback to pure Haversine math for all restaurants if API call fails or status != 200
    for restaurant in restaurants:
        distance_map[restaurant["name"]] = calculate_haversine(user_lat, user_lon, restaurant["lat"], restaurant["lon"])
    return distance_map


def filter_by_hard_constraints(user_prefs, knowledge_base, calculated_distances):
    surviving_restaurants = []
    
    for restaurant in knowledge_base:
        # 1. Dietary constraint check
        user_diet = user_prefs.get("dietary", "None")
        if user_diet and user_diet != "None":
            if user_diet not in restaurant.get("dietary_options", []):
                continue
        
        # 2. Budget tier check
        user_budget = user_prefs.get("budget", "Any")
        if user_budget and user_budget != "Any":
            if restaurant.get("budget_tier") != user_budget:
                continue
        
        # 3. Distance range check with safe float parsing
        actual_distance = calculated_distances.get(restaurant["name"], 0)
        max_allowed_distance = user_prefs.get("max_distance")
        if max_allowed_distance:
            try:
                if actual_distance > float(max_allowed_distance):
                    continue
            except (ValueError, TypeError):
                pass # Default to passing constraint if invalid float provided
            
        surviving_restaurants.append(restaurant)
        
    return surviving_restaurants


def calculate_match_scores(user_prefs, surviving_restaurants):
    scored_recommendations = []
    user_cuisine = user_prefs.get("cuisine", "Any")
    
    for restaurant in surviving_restaurants:
        score = 50.0
        
        # 1. Cuisine matching (+30 points)
        if user_cuisine and user_cuisine != "Any":
            if restaurant.get("cuisine") == user_cuisine:
                score += 30.0
        
        # 2. Rating Factor (+20 points max)
        # Use existing 'rating' key from JSON, or fall back to sub-field averages
        if "rating" in restaurant:
            calculated_rating = float(restaurant["rating"])
        else:
            quality = float(restaurant.get("quality_of_food", 4))
            aesthetics = float(restaurant.get("aesthetics", 4))
            service = float(restaurant.get("customer_service", 4))
            calculated_rating = round((quality + aesthetics + service) / 3.0, 1)
        
        score += (calculated_rating * 4.0)
        
        if score > 100.0:
            score = 100.0 
            
        scored_item = restaurant.copy()
        scored_item["match_score"] = round(score, 1)
        scored_item["rating"] = calculated_rating
        
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

@app.route("/")
def landing_page():
    return render_template("landing.html")


@app.route("/discover", methods=["GET", "POST"])
def discover_page():
    restaurants_db = load_knowledge_base()
    
    if request.method == "POST":
        dietary = request.form.get("dietary_restriction", "None")
        budget = request.form.get("budget_tier", "Any")
        cuisine = request.form.get("preferred_cuisine", "Any")
        max_distance = request.form.get("distance_radius", "10.0")
        search_query = request.form.get("search_query", "").lower()
    else:
        dietary = request.args.get("dietary_restriction", "None")
        budget = request.args.get("budget_tier", "Any")
        cuisine = request.args.get("preferred_cuisine", "Any")
        max_distance = request.args.get("distance_radius", "10.0")
        search_query = request.args.get("search_query", "").lower()

    user_preferences = {
        "lat": -1.2833, 
        "lon": 36.8219,
        "dietary": dietary, 
        "budget": budget, 
        "cuisine": cuisine, 
        "max_distance": max_distance,
        "search_query": search_query
    }
    
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


@app.route('/restaurant/<string:res_name>')
def detail_page(res_name):
    db = load_knowledge_base()
    
    restaurant_match = next((item for item in db if item["name"].lower() == res_name.lower()), None)
    
    if not restaurant_match:
        abort(404)
        
    if "description" not in restaurant_match:
        restaurant_match["description"] = f"A popular gathering spot in {restaurant_match.get('location', 'Nairobi')} specializing in local {restaurant_match.get('cuisine')} culinary crafts."
        
    if "rating" in restaurant_match:
        restaurant_match["rating"] = float(restaurant_match["rating"])
    else:
        q = restaurant_match.get("quality_of_food", 4)
        a = restaurant_match.get("aesthetics", 4)
        s = restaurant_match.get("customer_service", 4)
        restaurant_match["rating"] = round((q + a + s) / 3.0, 1)
    
    if "hours" not in restaurant_match:
        restaurant_match["hours"] = "10:00 AM - 10:00 PM"
    if "phone" not in restaurant_match:
        restaurant_match["phone"] = "+254 700 123 456"
        
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


@app.route("/api/quiz-recommend", methods=["POST"])
def quiz_recommend():
    data = request.get_json() or {}
    
    # Corrected "max-distance" typo to "max_distance"
    user_prefs = {
        "lat": data.get("lat", -1.2833),
        "lon": data.get("lon", 36.8219),
        "dietary": data.get("dietary", "None"),
        "budget": data.get("budget", "Any"),
        "cuisine": data.get("cuisine", "Any"),
        "max_distance": data.get("max_distance", "10.0")
    }
    
    knowledge_base = load_knowledge_base()
    results = run_inference_engine(user_prefs, knowledge_base)
    
    return jsonify({
        "status": "success",
        "total_matches": len(results),
        "results": results,
        "preferences": user_prefs
    })

if __name__ == "__main__":
    app.run(debug=True)