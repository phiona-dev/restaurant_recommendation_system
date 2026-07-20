import json
import os

def load_knowledge_base(filepath="healthcentre.json"):
    """Loads facts and rules from a JSON file with a hardcoded fallback structure."""
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    else:
        # Fallback configuration matching specifications if JSON file is missing
        return {
            "symptoms": [
                "Fever", "Headache", "Cough", "Chest Pain", "Sneezing",
                "Runny Nose", "Fatigue", "Sore Throat", "Vomiting", "Diarrhea"
            ],
            "rules": [
                {"disease": "Malaria", "symptoms": ["Fever", "Headache", "Fatigue"]},
                {"disease": "Pneumonia", "symptoms": ["Cough", "Chest Pain", "Fatigue"]},
                {"disease": "Flu", "symptoms": ["Sneezing", "Runny Nose", "Sore Throat"]},
                {"disease": "Food Poisoning", "symptoms": ["Vomiting", "Diarrhea", "Fatigue"]}
            ]
        }

def diagnose(user_symptoms, rules):
    """
    Evaluates system production rules against the active user symptom list.
    Applies logical inference to trace matching conditions.
    """
    possible_diagnoses = []
    user_symptoms_set = set(s.strip().title() for s in user_symptoms)
    
    for rule in rules:
        rule_symptoms_set = set(rule["symptoms"])
        # Check if the rule's required symptoms form a subset of user input symptoms
        if rule_symptoms_set.issubset(user_symptoms_set):
            possible_diagnoses.append(rule["disease"])
            
    return possible_diagnoses

def main():
    print("=" * 60)
    print("  MEDICAL EXPERT SYSTEM: KNOWLEDGE REPRESENTATION LAB  ")
    print("=" * 60)
    
    kb = load_knowledge_base()
    available_symptoms = kb["symptoms"]
    rules = kb["rules"]
    
    print("\nAvailable Symptoms in Knowledge Base:")
    for idx, symptom in enumerate(available_symptoms, 1):
        print(f"  [{idx}] {symptom}")
        
    print("\n--- Diagnostic Input Interface ---")
    print("Enter the numbers corresponding to your symptoms, separated by commas (e.g., 1, 2, 7):")
    
    # BONUS: Input Validation loop
    while True:
        user_input = input("Your selection: ").strip()
        if not user_input:
            print("❌ Input error: Field cannot be empty. Select at least one symptom index.")
            continue
            
        try:
            # Parse commas and convert strings to integers safely
            choices = [int(x.strip()) for x in user_input.split(",") if x.strip()]
            
            # Boundary checks for validity
            if any(choice < 1 or choice > len(available_symptoms) for choice in choices):
                print(f"❌ Input error: Indices must fall strictly between 1 and {len(available_symptoms)}.")
                continue
                
            # Extract actual symptom strings from validated indices
            selected_symptoms = [available_symptoms[choice - 1] for choice in choices]
            break
        except ValueError:
            print("❌ Format error: Please enter valid numbers only, separated by commas (e.g., 1,3,5).")

    print("\n--- Selected Symptoms ---")
    for symptom in selected_symptoms:
        print(f"  • {symptom}")
        
    print("\n--- Inference Engine Conclusion ---")
    results = diagnose(selected_symptoms, rules)
    
    if results:
        print("Match found! The system infers the following potential illness condition(s):")
        for disease in results:
            print(f"  ✅ **{disease}** Detected")
    else:
        print("  ⚠ No specific matching condition could be inferred from this symptom combination.")
    print("=" * 60)

if __name__ == "__main__":
    main()