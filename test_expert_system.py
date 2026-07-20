import unittest
import os
import json
from expert_systeM import load_knowledge_base, diagnose

class TestExpertSystem(unittest.TestCase):

    def setUp(self):
        """Set up standard rules to use across diagnostic tests."""
        self.rules = [
            {"disease": "Malaria", "symptoms": ["Fever", "Headache", "Fatigue"]},
            {"disease": "Pneumonia", "symptoms": ["Cough", "Chest Pain", "Fatigue"]},
            {"disease": "Flu", "symptoms": ["Sneezing", "Runny Nose", "Sore Throat"]},
            {"disease": "Food Poisoning", "symptoms": ["Vomiting", "Diarrhea", "Fatigue"]}
        ]
        self.test_filepath = "test_healthcentre.json"

    def tearDown(self):
        """Clean up any temporary files created during testing."""
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)

    # --- Tests for load_knowledge_base() ---

    def test_load_knowledge_base_fallback(self):
        """Test if the system loads the hardcoded fallback when the file is missing."""
        kb = load_knowledge_base(filepath="non_existent_file.json")
        self.assertIn("symptoms", kb)
        self.assertIn("rules", kb)
        self.assertEqual(len(kb["rules"]), 4) # Should have the 4 default rules

    def test_load_knowledge_base_from_file(self):
        """Test if the system correctly loads data from an existing JSON file."""
        test_data = {
            "symptoms": ["Cough", "Fever"],
            "rules": [{"disease": "Test Disease", "symptoms": ["Cough", "Fever"]}]
        }
        with open(self.test_filepath, "w") as f:
            json.dump(test_data, f)
            
        kb = load_knowledge_base(filepath=self.test_filepath)
        self.assertEqual(kb["symptoms"], ["Cough", "Fever"])
        self.assertEqual(kb["rules"][0]["disease"], "Test Disease")

    # --- Tests for diagnose() ---

    def test_diagnose_exact_match(self):
        """Test if providing exact symptoms returns the correct disease."""
        symptoms = ["Fever", "Headache", "Fatigue"]
        results = diagnose(symptoms, self.rules)
        self.assertEqual(results, ["Malaria"])

    def test_diagnose_superset_match(self):
        """Test if providing required symptoms plus extra ones still finds the disease."""
        symptoms = ["Fever", "Headache", "Fatigue", "Sneezing", "Cough"]
        results = diagnose(symptoms, self.rules)
        self.assertIn("Malaria", results)

    def test_diagnose_partial_match(self):
        """Test if missing a required symptom correctly results in NO diagnosis."""
        symptoms = ["Fever", "Headache"] # Missing Fatigue
        results = diagnose(symptoms, self.rules)
        self.assertEqual(results, [])

    def test_diagnose_multiple_diseases(self):
        """Test if having symptoms for multiple diseases returns all matches."""
        symptoms = ["Fever", "Headache", "Fatigue", "Sneezing", "Runny Nose", "Sore Throat"]
        results = diagnose(symptoms, self.rules)
        self.assertIn("Malaria", results)
        self.assertIn("Flu", results)
        self.assertEqual(len(results), 2)

    def test_diagnose_case_and_whitespace_insensitivity(self):
        """Test if the diagnose function handles messy string inputs properly."""
        symptoms = [" fever ", "HEADACHE", "  fatigue"]
        results = diagnose(symptoms, self.rules)
        self.assertEqual(results, ["Malaria"])

    def test_diagnose_empty_input(self):
        """Test behavior with no symptoms provided."""
        results = diagnose([], self.rules)
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()