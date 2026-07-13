import os
import json
import math
import requests
from flask import Flask , render_template, request #flask toolkit
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort  # Added abort
from urllib.parse import unquote                          # Added unquote to decode URLs

#load environment variables from the .env file immediately on startup
load_dotenv()

app = Flask(__name__) #initializes the flask app

ORS_API_KEY = os.environ.get("ORS_API_KEY", "MISSING_API_KEY_IN_ENV")

def load_knowledge_base():
    """
    Opens and reads the factual knowledge base from the local JSON file.
    converts JSON text data into a native Python list of dictionaries
    """
    try:
        with open("restaurants.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    
#fallback heuristics
def calculate_haversine(lat1, lon1, lat2, lon2):
    """calculates flat sphere distance when the API drops or hits rate limits"""
    R=6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    latitude_distance = lat2 - lat1
    longitude_distance = lon2 - lon1
    
    a = math.sin(latitude_distance/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(longitude_distance/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c


#API matrix
def batch_calculate_distances(user_lat, user_lon, restaurants):
    """
    provides real road distances for all restaurants via OpenRouteService
    Fallback is Haversine heuristics in case of API key fail, timeout or hit rate limits
    """
    #skip if no restaurants to process
    if not restaurants:
        return {}
    
    #ORS matrix expects locations in [longitude, latitude] format
    user_coordinates = [user_lon, user_lat]
    
    #compile a flat master list of locations: [User, Restaurant1, Restaurant2, ...]
    locations = [user_coordinates]
    for restaurant in restaurants:
        locations.append([restaurant["lon"], restaurant["lat"]])
        
    #setup endpoint request parameters
    url = "https://api.openrouteservice.org/v2/matrix/driving-car"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    #index[0] is the user. destination are all indices after o
    body = {
        "locations": locations,
        "sources": [0],
        "destinations": list(range(1, len(locations))),
        "metrics": ["distance"] # return only the distance metrics
    }
    
    distance_map = {}
    
    try:
        #send the batch request with a strict 4-second timeout guardrail
        response = requests.post(url, json=body, headers=headers, timeout=4)
        
        if response.status_code == 200:
            data = response.json()
            #convert to km since ORS returns distances in meters
            api_distances = data["distances"][0]
            
            for index, restaurant in enumerate(restaurants):
                raw_distance = api_distances[index]
                if raw_distance is not None:
                    distance_map[restaurant["name"]] = raw_distance/1000.0
                else:
                    #fallback if a single location cannot be snapped to a road mapping
                    distance_map[restaurant["name"]] = calculate_haversine(user_lat, user_lon, restaurant["lat"], restaurant["lon"])
            return distance_map
    except (requests.exceptions.RequestException, KeyError, ValueError):
        #catch network timeouts, connection drops or wrong schema errors silently
        pass

        
    #if anything failed above, instantly run calculations locally
    for restaurant in restaurants:
        distance_map[restaurant["name"]] = calculate_haversine(user_lat, user_lon, restaurant["lat"], restaurant["lon"])
    return distance_map


def filter_by_hard_constraints(user_prefs, knowledge_base, calculated_distances):
    """ 
    Step 1 of the inference engine: Matches user choices against restaurant facts.
    if a restaurant violates even ONE choice, it is eliminated immediately.
    """
    surviving_restaurants = []
    
    #loop through every single restaurant in our knowledge base data list
    for restaurant in knowledge_base:
        #rule 1: dietary constraint check
        #extract what user wants. default is None(if they didn't specify)
        user_diet = user_prefs.get("dietary", "None")
        if user_diet != "None":
            if user_diet not in restaurant["dietary_options"]:
                continue #skip and move to the next restaurant
        
        #rule2: budget tier check
        user_budget = user_prefs.get("budget", "Any")
        if user_budget != "Any":
            if restaurant["budget_tier"] != user_budget:
                continue
        
        #rule3: distance range check
        actual_distance = calculated_distances.get(restaurant["name"],0)
        
        max_allowed_distance = user_prefs.get("max_distance")
        
        if max_allowed_distance:
            if actual_distance > float(max_allowed_distance):
                continue
            
        #if the loop reaches this point, the restaurant has passed all rules
        surviving_restaurants.append(restaurant)
        
    return surviving_restaurants

def calculate_match_scores(user_prefs, surviving_restaurants):
    """
    Ranks the surviving options. Evaluates soft preferences (like cuisine matching) and restaurant quality
    to assign overall match percentage score
    """
    scored_recommendations= []
    
    user_cuisine = user_prefs.get("cuisine", "Any")
    
    for restaurant in surviving_restaurants:
        #base score of 50 points
        score = 50.0
        
        #feature1: cuisine matching(+30 points)
        if user_cuisine != "Any":
            if restaurant["cuisine"] == user_cuisine:
                score +=30
        
        #feature2: user rating factor(+20 points)
        # 4.5 out of 5 star rating -> 4.5 * 4 = 18 points
        rating = float(restaurant.get("rating", 3.5))
        score += (rating*4.0)
        
        #system boundary
        if score > 100.0:
            score = 100.0 
            
        #append the computed scored directly onto a copy of the restaurant dictionary
        scored_item = restaurant.copy()
        scored_item["match_score"] = round(score, 1)
        
        scored_recommendations.append(scored_item)
        
    #sort the array in descending order
    scored_recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    return scored_recommendations

def run_inference_engine(user_prefs, knowledge_base):
    """ 
    Links all parts of the forward chaining inference engine.
    takes incoming user choices, calculates routing, filters rules, and returns a sorted ranking list
    """
    
    #get user coordinates(safely fallback to central Nairobi if missing)
    user_lat = float(user_prefs.get("lat", -1.2833))
    user_lon = float(user_prefs.get("lon", 36.8219))
    
    #step 1: routing integration
    calculated_distances = batch_calculate_distances(user_lat, user_lon, knowledge_base)
    
    #step2: hard rule elimination
    surviving_restaurants = filter_by_hard_constraints(user_prefs, knowledge_base, calculated_distances)
    
    #step 3: heuristic scoring and order ranking
    final_ranked_commendations = calculate_match_scores(user_prefs, surviving_restaurants)
    
    return final_ranked_commendations


#Flask routes
@app.route('/')
def home():
    return render_template("index.html")

#route listens for the user clicking "Search" on the webpage
@app.route('/recommend', methods=['POST'])
def recommend_restaurants():
    user_preferences = {
        "lat": request.form.get("latitude", -1.2833),
        "lon": request.form.get("longitude", 36.8219),
        "dietary": request.form.get("dietary_restriction"),
        "budget": request.form.get("budget_tier"),
        "cuisine": request.form.get("preferred_cuisine"),
        "max_distance": request.form.get("distance_radius")
    }
    knowledge_base = load_knowledge_base()
    
    results = run_inference_engine(user_preferences, knowledge_base)
    
    return render_template("results.html", restaurants=results)


#this is added route to handle the detailed restaurant page
@app.route('/restaurant/<string:name>')
def restaurant_detail(name):
    """
    Handles fetching and showing the detailed layout page for a single restaurant
    """
    # Clean up the URL-encoded name (e.g., converting 'Sakura%20Sushi' back to 'Sakura Sushi')
    decoded_name = unquote(name)
    
    # Load the master list of hotels/restaurants
    knowledge_base = load_knowledge_base()
    
    # Scan the JSON knowledge base for a name match (case-insensitive)
    restaurant = next((r for r in knowledge_base if r["name"].lower() == decoded_name.lower()), None)
    
    # Safety guardrail: bounce back a 404 error if someone modifies the URL manually to a fake hotel
    if not restaurant:
        abort(404)
        
    # Heuristic fallback if an explicit 'about' string field isn't set in your JSON database yet
    if "about" not in restaurant:
        restaurant["about"] = f"World-famous for its incredible premium selection of curated dishes, local {restaurant.get('cuisine', 'gourmet')} specialties, and an unparalleled ambiance right here in {restaurant.get('location', 'Nairobi')}."
    
    # Mocking sample menu structure array matching your system's layout assets
    sample_menu = [
        {"name": "Grilled Platter", "img": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500"},
        {"name": "Artisan Pizza", "img": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=500"},
        {"name": "Garden Salad", "img": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500"},
        {"name": "Stack Pancakes", "img": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=500"},
        {"name": "Classic Burger", "img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"},
        {"name": "Seafood Pasta", "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"}
    ]
    
    # Generate an explicit query intent link for web or mobile native redirection mapping
    # Pulls lat/lon properties straight out of your database layout structure
    lat = restaurant.get("lat", -1.2833)
    lon = restaurant.get("lon", 36.8219)
    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    
    # Format a safe display metric match score percentage
    # (Defaulting to a safe backup calculation value if called outside of recommendation cache contexts)
    match_percentage = restaurant.get("match_score", 94.0)

    return render_template(
        "detail.html", 
        restaurant=restaurant, 
        menu=sample_menu, 
        maps_url=maps_url,
        match_percentage=match_percentage
    )
    
if __name__ == "__main__":
    app.run(debug=True)