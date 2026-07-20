
# 1. MOCK RESTAURANT RECOMMENDATION SYSTEM


def recommend_restaurants(user_prefs, restaurant_db):
    """
    Mock function to filter restaurants based on cuisine, max price, and min rating.
    """
    recommendations = []
    for restaurant in restaurant_db:
        # Check matching criteria
        cuisine_match = not user_prefs.get("cuisine") or restaurant["cuisine"] == user_prefs["cuisine"]
        price_match = not user_prefs.get("max_price") or restaurant["price"] <= user_prefs["max_price"]
        rating_match = not user_prefs.get("min_rating") or restaurant["rating"] >= user_prefs["min_rating"]
        
        if cuisine_match and price_match and rating_match:
            recommendations.append(restaurant["name"])
            
    return recommendations 
# 2. PYTHON TEST CASES


class TestRestaurantRecommender(unittest.TestCase):
    
    def setUp(self):
        """
        Prerequisites: Setup the test environment and Test Data.
        This runs before every single test case.
        """
        self.restaurant_db = [
            {"name": "Pasta Palace", "cuisine": "Italian", "price": 2, "rating": 4.5},
            {"name": "Burger Barn", "cuisine": "American", "price": 1, "rating": 3.8},
            {"name": "Sushi Station", "cuisine": "Japanese", "price": 3, "rating": 4.9},
            {"name": "Luigi's", "cuisine": "Italian", "price": 4, "rating": 4.8},
            {"name": "Taco Tent", "cuisine": "Mexican", "price": 1, "rating": 4.2}
        ]

    def test_exact_cuisine_match(self):
        """
        Test Case ID: RECOM_001
        Test Case Description: Verify correct recommendation for a specific cuisine.
        Created By: Micahel
        QA Tester's Log: Verify that only Italian restaurants are returned.
        Test Data: User prefers Italian, no price/rating limit.
        """
        preferences = {"cuisine": "Italian"}
        result = recommend_restaurants(preferences, self.restaurant_db)
        
        # Expected Pass Condition: Should return Pasta Palace and Luigi's
        self.assertEqual(len(result), 2)
        self.assertIn("Pasta Palace", result)
        self.assertIn("Luigi's", result)

    def test_budget_filtering(self):
        """
        Test Case ID: RECOM_002
        Test Case Description: Verify correct recommendation based on max price.
        Created By: Munge
        QA Tester's Log: Verify that expensive restaurants are filtered out.
        Test Data: User prefers max price of 2.
        """
        preferences = {"max_price": 2}
        result = recommend_restaurants(preferences, self.restaurant_db)
        
        # Expected Pass Condition: Should return Pasta Palace, Burger Barn, Taco Tent
        self.assertEqual(len(result), 3)
        self.assertNotIn("Sushi Station", result)
        self.assertNotIn("Luigi's", result)

    def test_strict_multi_criteria(self):
        """
        Test Case ID: RECOM_003
        Test Case Description: Verify recommendations matching multiple strict conditions.
        Created By: Michael
        QA Tester's Log: Verify area calculation (metaphorically) by checking tight constraints.
        Test Data: Italian cuisine, max price 2, min rating 4.0.
        """
        preferences = {
            "cuisine": "Italian",
            "max_price": 2,
            "min_rating": 4.0
        }
        result = recommend_restaurants(preferences, self.restaurant_db)
        
        # Expected Pass Condition: Only Pasta Palace meets ALL criteria
        self.assertEqual(result, ["Pasta Palace"])

    def test_no_results_found(self):
        """
        Test Case ID: RECOM_004
        Test Case Description: Verify system handles impossible criteria gracefully.
        Created By: Michael
        QA Tester's Log: Verify empty list is returned, not an error.
        Test Data: Max price 1, min rating 5.0 (impossible in DB).
        """
        preferences = {
            "max_price": 1,
            "min_rating": 5.0
        }
        result = recommend_restaurants(preferences, self.restaurant_db)
        
        # Expected Pass Condition: Empty list
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main(verbosity=2)