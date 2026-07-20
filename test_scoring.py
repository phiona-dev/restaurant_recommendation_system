from app import calculate_match_scores

def test_heuristic_scoring():
    print("starting multi-criteria scoring heuristic tests..\n")
    
    mock_surviving_restaurants = [
        {
            "name": "Bella Italia",
            "cuisine": "Italian",
            "rating": 4.5
        },
        {
            "name": "Tokyo Sushi",
            "cuisine": "Japanese",
            "rating": 4.8
        },
        {
            "name": "Luigi's Pizza Place",
            "cuisine": "Italian",
            "rating": 3.8
        }
    ]
    
    user_preferences = {
        "cuisine": "Italian"
    }
    
    print(f"Submitting user soft preferences: {user_preferences}\n")
    
    results = calculate_match_scores(user_preferences, mock_surviving_restaurants)
    
    print("Sorted Recommendation Output:")
    for rank, item in enumerate(results, 1):
        print(f"    Rank {rank}: {item['name']} | Cuisine: {item['cuisine']} | Rating: {item['rating']} | Final Score: {item['match_score']}%")
    print("")
    
    
    if results[0]["name"] == "Bella Italia" and results[0]["match_score"] == 98.0:
        print("SUCCESS: 'Bella Italia' correctly ranked #1 with exactly 98.0% match score.")
    else:
        print("FAILURE: 'Bella Italia' score or rank is mathematically incorrect.")

    # Check 2: Did the lower-rated Italian spot beat the higher-rated Japanese spot because of cuisine preference?
    # Luigi's Math: 50 (Base) + 30 (Cuisine Match) + (3.8 * 4.0 = 15.2) = 95.2%
    # Tokyo Sushi Math: 50 (Base) + 0 (No Cuisine Match) + (4.8 * 4.0 = 19.2) = 69.2%
    if results[1]["name"] == "Luigi's Pizza Place":
        print("SUCCESS: 'Luigi's' correctly took rank #2 because cuisine relevancy outweighs a raw star rating.")
    else:
        print("FAILURE: The engine prioritized raw star ratings over the user's explicit cuisine preference.")

    # Check 3: Is the array perfectly ordered from highest score to lowest score?
    if results[0]["match_score"] >= results[1]["match_score"] >= results[2]["match_score"]:
        print("SUCCESS: The recommendation array is cleanly sorted in descending order.")
    else:
        print("FAILURE: Sorting array failed; low match percentages are mixed up.")

if __name__ == "__main__":
    test_heuristic_scoring()