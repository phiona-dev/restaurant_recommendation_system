from app import run_inference_engine

def test_full_engine_integration():
    print("Executing full master inference engine integration test..\n")
    
    mock_database = [
        {
            "name": "Sultan Halal Grill",
            "dietary_options": ["Halal", "Vegetarian"],
            "budget_tier": "$$",
            "cuisine": "Indian",
            "rating": 4.6,
            "lat": -1.2850, "lon": 36.8240
        },
        {
            "name": "Burger Joint",
            "dietary_options": ["None"],
            "budget_tier": "$",
            "cuisine": "Fast Food",
            "rating": 4.0,
            "lat": -1.2810, "lon": 36.8110
        },
        {
            "name": "The High-End Curry House",
            "dietary_options": ["Halal", "Vegetarian"],
            "budget_tier": "$$$",
            "cuisine": "Indian",
            "rating": 4.9,
            "lat": -1.2860, "lon": 36.8290
        }
    ]
    
    simulated_user_request = {
        "lat": "-1.2833",
        "lon": "36.8219",
        "dietary": "Halal",
        "budget": "$$",
        "cuisine": "Indian",
        "max_distance": "4.0"
    }
    
    print(f"User Form Submission Received: {simulated_user_request}\n")
    
    final_output = run_inference_engine(simulated_user_request, mock_database)
    
    print("Engine Processing Complete. Final Recommendations Passed to View Layer:")
    for rank, item in enumerate(final_output, 1):
        print(f"   Rank {rank}: {item['name']} | Match Score: {item['match_score']}%")
    print("")

    # --- Verification Guardrails ---
    
    # Assert Check 1: Did we filter correctly?
    # 'Sultan Halal Grill' passes all hard checks.
    # 'Burger Joint' fails Hard Diet Check (Not Halal).
    # 'High-End Curry House' fails Hard Budget Check ($$$ instead of $$).
    if len(final_output) == 1 and final_output[0]["name"] == "Sultan Halal Grill":
        print("SUCCESS: Hard elimination filters properly knocked out non-matches.")
    else:
        print("FAILURE: Incorrect number of restaurants survived the filter stage.")

    # Assert Check 2: Did the score append correctly to the output data schema?
    if len(final_output) > 0 and "match_score" in final_output[0]:
        print("SUCCESS: Multi-criteria scorer successfully injected the match percentage metric.")
    else:
        print("FAILURE: Output object schema is missing the 'match_score' key structure.")

if __name__ == "__main__":
    test_full_engine_integration()