import math
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# =========================================================
# KNOWLEDGE BASE: Restaurant Domain Facts
# =========================================================
RESTAURANTS_KB = [
    {
        "id": 1,
        "name": "Carnivore Restaurant",
        "cuisine": "African",
        "dietary_options": ["Halal"],
        "budget_tier": "$$$",
        "quality_of_food": 4.8,
        "aesthetics": 4.6,
        "customer_service": 4.7,
        "lat": -1.3323,
        "lon": 36.7905,
        "image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&auto=format&fit=crop",
        "description": "An iconic open-air meat buffet dining experience featuring traditional African roasted meats and game."
    },
    {
        "id": 2,
        "name": "Haandi Restaurant",
        "cuisine": "Indian",
        "dietary_options": ["Vegetarian", "Halal"],
        "budget_tier": "$$",
        "quality_of_food": 4.7,
        "aesthetics": 4.3,
        "customer_service": 4.5,
        "lat": -1.2650,
        "lon": 36.8050,
        "image": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=800&auto=format&fit=crop",
        "description": "Renowned North Indian culinary experience with rich curries, naan, and signature tandoori dishes."
    },
    {
        "id": 3,
        "name": "Habesha Ethiopian Restaurant",
        "cuisine": "African",
        "dietary_options": ["Vegetarian", "Halal"],
        "budget_tier": "$$",
        "quality_of_food": 4.6,
        "aesthetics": 4.5,
        "customer_service": 4.2,
        "lat": -1.2885,
        "lon": 36.7820,
        "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&auto=format&fit=crop",
        "description": "Authentic Ethiopian dining set in a lush garden, serving traditional communal injera platters."
    },
    {
        "id": 4,
        "name": "Lucca Italian Restaurant",
        "cuisine": "Italian",
        "dietary_options": ["Vegetarian"],
        "budget_tier": "$$$",
        "quality_of_food": 4.9,
        "aesthetics": 4.8,
        "customer_service": 4.8,
        "lat": -1.2680,
        "lon": 36.8070,
        "image": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&auto=format&fit=crop",
        "description": "Upscale Italian dining known for hand-crafted pastas, wood-fired pizzas, and refined atmosphere."
    },
    {
        "id": 5,
        "name": "Al-Yousuf Shawarma & Grill",
        "cuisine": "Middle Eastern",
        "dietary_options": ["Halal"],
        "budget_tier": "$",
        "quality_of_food": 4.4,
        "aesthetics": 3.8,
        "customer_service": 4.1,
        "lat": -1.2830,
        "lon": 36.8250,
        "image": "https://images.unsplash.com/photo-1529006557810-274b9b2fc783?w=800&auto=format&fit=crop",
        "description": "Fast-casual Middle Eastern spot offering flavorful spiced shawarmas, falafel, and mixed grills."
    },
    {
        "id": 6,
        "name": "Urban Burger",
        "cuisine": "Fast Food",
        "dietary_options": ["Halal"],
        "budget_tier": "$$",
        "quality_of_food": 4.3,
        "aesthetics": 4.2,
        "customer_service": 4.4,
        "lat": -1.2620,
        "lon": 36.8020,
        "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&auto=format&fit=crop",
        "description": "Gourmet burgers, loaded fries, and thick milkshakes served in a modern, vibrant setting."
    }
]

# Haversine distance calculator in kilometers
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def batch_calculate_distances(user_lat, user_lon, restaurants):
    return {r["name"]: haversine_distance(user_lat, user_lon, r["lat"], r["lon"]) for r in restaurants}


# =========================================================
# EXPERT SYSTEM PRODUCTION RULES
# =========================================================

HARD_RULES = [
    {
        "id": "RULE_HARD_DIET",
        "description": "Strict Dietary Constraint",
        "check": lambda prefs, rest: prefs.get("dietary") == "None" or prefs.get("dietary") in rest.get("dietary_options", [])
    },
    {
        "id": "RULE_HARD_BUDGET",
        "description": "Budget Cap Constraint",
        "check": lambda prefs, rest: prefs.get("budget") == "Any" or rest.get("budget_tier") == prefs.get("budget")
    }
]

HEURISTIC_RULES = [
    {
        "id": "RULE_CUISINE_MATCH",
        "weight": 35,
        "condition": lambda prefs, rest: prefs.get("cuisine") != "Any" and rest.get("cuisine") == prefs.get("cuisine"),
        "explanation": lambda prefs, rest: f"Matches requested '{rest.get('cuisine')}' cuisine (+35 pts)"
    },
    {
        "id": "RULE_HIGH_FOOD_QUALITY",
        "weight": 25,
        "condition": lambda prefs, rest: float(rest.get("quality_of_food", 0)) >= 4.5,
        "explanation": lambda prefs, rest: f"Top-tier food quality rating of {rest.get('quality_of_food')}/5.0 (+25 pts)"
    },
    {
        "id": "RULE_GREAT_SERVICE",
        "weight": 15,
        "condition": lambda prefs, rest: float(rest.get("customer_service", 0)) >= 4.3,
        "explanation": lambda prefs, rest: f"High customer service score of {rest.get('customer_service')}/5.0 (+15 pts)"
    },
    {
        "id": "RULE_EXCELLENT_AESTHETICS",
        "weight": 15,
        "condition": lambda prefs, rest: float(rest.get("aesthetics", 0)) >= 4.4,
        "explanation": lambda prefs, rest: f"Premium interior aesthetics & dining ambiance (+15 pts)"
    }
]


# =========================================================
# INFERENCE ENGINE (Forward Chaining Execution)
# =========================================================

def run_inference_engine(user_prefs, knowledge_base):
    user_lat = float(user_prefs.get("lat", -1.2833))
    user_lon = float(user_prefs.get("lon", 36.8219))
    max_dist = float(user_prefs.get("max_distance", 10.0))
    
    calculated_distances = batch_calculate_distances(user_lat, user_lon, knowledge_base)
    ranked_results = []

    for restaurant in knowledge_base:
        dist = calculated_distances.get(restaurant["name"], 0.0)
        
        # 1. Distance Hard Filter
        if dist > max_dist:
            continue

        # 2. Hard Rule Evaluation
        passed_hard_rules = True
        for rule in HARD_RULES:
            if not rule["check"](user_prefs, restaurant):
                passed_hard_rules = False
                break
        
        if not passed_hard_rules:
            continue

        # 3. Heuristic Soft Rule Evaluation & Explanation Trace
        score = 10.0
        explanation_trace = []

        for rule in HEURISTIC_RULES:
            if rule["condition"](user_prefs, restaurant):
                score += rule["weight"]
                explanation_trace.append(rule["explanation"](user_prefs, restaurant))

        explanation_trace.append(f"Located within {round(dist, 1)} km radius")

        final_score = min(round(score, 1), 100.0)

        q = float(restaurant.get("quality_of_food", 4))
        a = float(restaurant.get("aesthetics", 4))
        s = float(restaurant.get("customer_service", 4))
        avg_rating = round((q + a + s) / 3.0, 1)

        result = restaurant.copy()
        result["match_score"] = final_score
        result["rating"] = avg_rating
        result["distance"] = round(dist, 1)
        result["explanations"] = explanation_trace

        ranked_results.append(result)

    # Conflict Resolution: Sort by highest confidence match score
    ranked_results.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked_results


# =========================================================
# FLASK ROUTES
# =========================================================

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/quiz")
def quiz_page():
    return render_template("quiz.html")

@app.route("/discover", methods=["GET", "POST"])
def discover_page():
    if request.method == "POST":
        preferred_cuisine = request.form.get("preferred_cuisine", "Any")
        dietary_restriction = request.form.get("dietary_restriction", "None")
        budget_tier = request.form.get("budget_tier", "Any")
        distance_radius = request.form.get("distance_radius", "10.0")
    else:
        preferred_cuisine = request.args.get("preferred_cuisine", "Any")
        dietary_restriction = request.args.get("dietary_restriction", "None")
        budget_tier = request.args.get("budget_tier", "Any")
        distance_radius = request.args.get("distance_radius", "10.0")

    user_preferences = {
        "cuisine": preferred_cuisine,
        "dietary": dietary_restriction,
        "budget": budget_tier,
        "max_distance": float(distance_radius),
        "lat": -1.2833,
        "lon": 36.8219
    }

    recommendations = run_inference_engine(user_preferences, RESTAURANTS_KB)

    return render_template(
        "discover.html",
        restaurants=recommendations,
        prefs=user_preferences
    )

@app.route("/detail/<int:restaurant_id>")
def detail_page(restaurant_id):
    # Retrieve matching restaurant from Knowledge Base by ID
    restaurant = next((r for r in RESTAURANTS_KB if r["id"] == restaurant_id), None)
    
    # If invalid ID, safely redirect back to recommendations page
    if not restaurant:
        return redirect(url_for("discover_page"))
        
    return render_template("detail.html", restaurant=restaurant)
if __name__ == "__main__":
    app.run(debug=True)