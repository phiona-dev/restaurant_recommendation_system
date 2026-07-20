import os
from dotenv import load_dotenv
from app import batch_calculate_distances, calculate_haversine

load_dotenv()

def test_distance_heuristics():
    print("Starting routing logic validation tests...")
    
    #mock user position(Nairobi CBD area)
    user_lat = -1.2833
    user_lon = 36.8219
    
    #mock knowledge base dataset array
    mock_restaurants = [
        {
            "name": "Westlands Pizza Hub",
            "lat": -1.2618,
            "lon": 36.8045
        },
        {
            "name": "Mombasa Highway Dinner",
            "lat": -1.3194,
            "lon": 36.8622
        }
    ]
    
    #Test1: fallback haversine mathematics test
    print("\nExecuting Test 1: Straight-line Haversine Calculation...")
    haversine_distance = calculate_haversine(user_lat, user_lon, mock_restaurants[0]["lat"], mock_restaurants[0]["lon"])
    print(f"->Computed Math distance: {round(haversine_distance, 2)} KM")
    if 2.9 < haversine_distance < 3.2:
        print("SUCCESS: The distance math is working and matches real world distances\n")
    else:
        print("FAILURE: The distance math is wrong. Check your formulas.\n")
    
    #Test2: OpenRouteService matrix API
    print("\nExecuting Test 2: Batch Matrix Routing Calculation...")
    api_key = os.environ.get("ORS_API_KEY")
    if api_key:
        print(f"Active API key detected (Starts with: {api_key[:6]}...)")
    else:
        print("No API key found")
    
    #run the batch call
    results = batch_calculate_distances(user_lat, user_lon, mock_restaurants)
        
    print("\n Calculated output grid")
    for name, distance in results.items():
        print(f"-> {name}: {round(distance, 2)} KM")
    
    #validations
    if len(results) == len(mock_restaurants):
        print("\n SUCCESS: The system calculated distances for every single restaurant in the list.")
    else:
        print("\n FAILURE: Some restaurants were skipped or lost during the calculation.")

if __name__ == "__main__":
    test_distance_heuristics();