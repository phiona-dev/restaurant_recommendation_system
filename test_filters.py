from app import filter_by_hard_constraints

def test_hard_filters():
    print("Starting hard constraints elimination logic test...\n")
    
    mock_knowledge_base = [
        {
            "name": "Green Garden Vegan Bistro",
            "dietary_options": ["Vegan", "Vegetarian"],
            "budget_tier": "$$",
            "cuisine": "Healthy"
        },
        {
            "name": "Downtown Steakhouse",
            "dietary_options": ["None"],
            "budget_tier": "$$$",
            "cuisine": "Western"
        },
        {
            "name": "Quick Bite Cafe",
            "dietary_options": ["Vegetarian", "Halal"],
            "budget_tier": "$",
            "cuisine": "Fast Food"
        }
    ]
    
    #precalculated mock distances
    mock_distances = {
        "Green Garden Vegan Bistro": 2.5,   # Close
        "Downtown Steakhouse": 1.2,         # Very close
        "Quick Bite Cafe": 8.5              # Too far away!
    }
    
    #run test scenario. A vegan user on a budget ($$) maximum 5km radius
    user_preferences =  {
        "dietary": "Vegan",
        "budget": "$$",
        "max_distance": "5.0"
    }
    
    print(f"Submitting user preferences: {user_preferences}\n")
    
    results = filter_by_hard_constraints(user_preferences, mock_knowledge_base, mock_distances)
    
    #extract names of restaurants that survived the test
    surviving_names = [r["name"] for r in results]
    print(f"Restaurants that survived the filter loop: {surviving_names}")
    
    #verify individual restaurant compliance
    
    if "Green Garden Vegan Bistro" in surviving_names:
        print("SUCCESS: Green Garden passed because it matches all criteria.")
    else:
        print("FAILURE: Green Garden was accidentally eliminated")
    
    if "Downtown Steakhouse" not in surviving_names:
        print("SUCCESS: Downtown SteakHouse was correctly eliminated(wrong diet and budget)")
    else:
        print("FAILURE: Downtown SteakHouse sneaked through the rules.")
        
    if "Quick Bite Cafe" not in surviving_names:
        print("SUCCESS: Quick Bite Cafe was correctly eliminated(Too far: 8.5km)")
    else:
        print("FAILURE: Quick Bite Cafe was allowed despite violating max distance")
        
if __name__ == "__main__":
    test_hard_filters()