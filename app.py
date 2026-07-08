import os
import json
import math
import requests
from dotenv import load_dotenv

#load environment variables from the .env file immediately on startup
load_dotenv()

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