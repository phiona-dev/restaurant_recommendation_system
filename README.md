# Restaurant Recommendation Expert System
---

## Executive Overview & Problem Statement

Finding an optimal dining venue in a dynamic urban landscape like Nairobi involves evaluating multiple conflicting factors: dietary restrictions (e.g., Halal, Vegan, Gluten-Free), budget constraints, geographic distance, and cuisine preferences. Decision fatigue often leads users to make poor choices.

The **Restaurant Recommendation Expert System** is a lightweight, rule-based **Knowledge-Based System (KBS)** designed to replicate human expert reasoning in restaurant selection. By decoupling factual domain knowledge from reasoning algorithms, the system applies **Forward Chaining** inference over user inputs to filter, score, and rank candidate venues deterministically.

---

## System Architecture & KBS Components

The system explicitly adheres to the classical Knowledge-Based System architecture, ensuring strict separation of concerns between the **Knowledge Base**, the **Inference Engine**, and the **User Interface**.

```
                           +------------------------+
                           |     User Interface     |
                           | (Flask Web App / API)  |
                           +-----------+------------+
                                       |
                                User Inputs (Facts)
                                       v
                           +------------------------+
                           |   Inference Engine     |
                           |  (Forward Chaining)    |
                           +-----+------------+-----+
                                 |            |
                    Rules/Constraints      Data Fetching
                                 v            v
               +-------------------+        +--------------------+
               |    Rule Base      |        | External Geospatial|
               | (Hard/Soft Rules) |        |  API / Haversine   |
               +-------------------+        +--------------------+
                                 |
                          Query Fact Base
                                 v
                     +------------------------+
                     |     Knowledge Base     |
                     |  (restaurants.json)    |
                     +------------------------+
```

---

## Knowledge Representation & Schema

Domain facts are externally represented in a structured, multi-attribute `JSON` schema (`restaurants.json`). This decoupling allows dynamic expansion of the KB without altering source code logic.

### 1. External Fact Base Schema
Each entity in the Knowledge Base is represented with both categorical, numeric, and array-based attributes:

```json
{
  "id": 1,
  "name": "CRAVE Restaurant",
  "cuisine": "American",
  "budget_tier": "$$",
  "location": "Kilimani",
  "lat": -1.2912,
  "lon": 36.7972,
  "rating": 4.6,
  "description": "A stylish, trendy hotspot directly across from Yaya Centre...",
  "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600",
  "phone": "+254 756 600600",
  "hours": "9:30 AM - 10:30 PM",
  "dietary_options": ["Halal", "Vegetarian"]
}
```

### 2. Formal Production Rules (IF-THEN Logic)

The rule base consists of **Hard Constraint Rules** (elimination) and **Soft Preference Rules** (scoring and certainty factor assignment).

#### Hard Rules (Elimination Phase)
* **Rule 1 (Dietary Safety Threshold):**  
  $$\text{IF } (\text{User.Dietary} \neq \text{'None'}) \land (\text{User.Dietary} \notin \text{Restaurant.DietaryOptions}) \implies \text{ELIMINATE}$$

* **Rule 2 (Budget Constraint):**  
  $$\text{IF } (\text{User.Budget} \neq \text{'Any'}) \land (\text{User.Budget} \neq \text{Restaurant.BudgetTier}) \implies \text{ELIMINATE}$$

* **Rule 3 (Geospatial Proximity Boundary):**  
  $$\text{IF } (\text{ActualDistance}(\text{User}, \text{Restaurant}) > \text{User.MaxDistance}) \implies \text{ELIMINATE}$$

#### Soft Rules (Scoring & Ranking Phase)
* **Rule 4 (Baseline Certainty):**  
  $$\text{BaseScore} = 50.0$$

* **Rule 5 (Cuisine Match Bonus):**  
  $$\text{IF } (\text{User.Cuisine} \neq \text{'Any'}) \land (\text{User.Cuisine} == \text{Restaurant.Cuisine}) \implies \text{Score} = \text{Score} + 30.0$$

* **Rule 6 (Quality Heuristic Scaling):**  
  $$\text{Score} = \text{Score} + (\text{Restaurant.Rating} \times 4.0)$$

* **Rule 7 (Score Normalization):**  
  $$\text{FinalMatchScore} = \min(\text{Score}, 100.0)$$

---

## Inference Engine Strategy

The system utilizes a **Forward Chaining (Data-Driven)** reasoning mechanism:

1. **Working Memory Initialization:** User preferences (`dietary`, `budget`, `cuisine`, `max_distance`, `lat`, `lon`) are injected as temporary initial facts.
2. **Geospatial Distance Calculation:** The engine dynamically calls the OpenRouteService API (with automatic mathematical **Haversine formula fallback**) to determine true driving distance.
3. **Constraint Evaluation (Pattern Matching):** The engine evaluates all candidate facts against Hard Rules 1–3. Entities failing any condition are pruned.
4. **Conflict Resolution & Ranking:** Surviving candidates are evaluated against Soft Rules 4–7. Recommendations are ordered by `match_score` descending.

---

## Knowledge Acquisition Process

Knowledge acquisition for the system followed a three-phase structured process:

1. **Domain Identification & Elicitation:** Information was collected on key dining hubs across Nairobi (Kilimani, Westlands, CBD, Upper Hill, Karen, Lavington, Madaraka).
2. **Attribute Structuring & Categorization:** Attributes were standardized into discrete tiers:
   - Budget Tiers: `$` (Under 1000 KES), `$$` (1000–2500 KES), `$$$` (2500–5000 KES), `$$$$` (5000+ KES).
   - Dietary Tags: Standardized set including `Halal`, `Vegetarian`, `Vegan`, `Gluten-Free`.
3. **Geospatial & Entity Normalization:** Coordinates (`lat`, `lon`) were extracted via Google Maps geocoding and cross-verified for accurate distance calculations.

---

## Technology Stack

| Layer | Technology Used |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Framework** | Flask (Web Server & REST APIs) |
| **Knowledge Base** | External JSON (`restaurants.json`) |
| **Geospatial Routing** | OpenRouteService Matrix API + Haversine Math Fallback |
| **Frontend UI** | HTML5, CSS3, JavaScript, Jinja2 Templates |
| **Version Control** | Git & GitHub |

---

## Installation & Local Setup

### Prerequisites
* Python 3.9+ installed
* Git

### Step 1: Clone Repository
```bash
git clone https://github.com/phiona-dev/restaurant-recommendation-kbs.git
cd restaurant-recommendation-kbs
```

### Step 2: Set Up Virtual Environment
```bash
# On Linux/macOS
python3 -m venv venv
source venv/bin/venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the root directory:
```env
ORS_API_KEY=your_openrouteservice_api_key_here
FLASK_ENV=development
```

### Step 5: Run the Application
```bash
python app.py
```
Navigate to `http://127.0.0.1:5000` in your web browser.

---

## User Guide & Screenshots

1. **Landing Page (`/`):** Explains the system and provides a pop quiz to get the customers preference and then direct navigation to discovery.
   <img width="1258" height="617" alt="Screenshot 2026-08-05 123902" src="https://github.com/user-attachments/assets/37151548-2dc7-4f4a-add0-7df37c37fe18" />

   - Based on the results from the popquiz, a personalized match with recommended restaurants is made visible to the customer.
   - The preferences can be further customised on the left side filter bar
     <img width="1274" height="605" alt="Screenshot 2026-08-05 124026" src="https://github.com/user-attachments/assets/7f60d9d2-c459-487d-9848-355f71501988" />
     <img width="1268" height="620" alt="Screenshot 2026-08-05 142217" src="https://github.com/user-attachments/assets/b670cfc7-01bc-447b-b1c7-81a3ffac2832" />
     <img width="1237" height="620" alt="Screenshot 2026-08-05 142408" src="https://github.com/user-attachments/assets/4ef943e3-6870-4ce1-9d41-7dbb99b67615" />



2. **Interactive Discovery (`/discover`):**
   - Filter by dietary restrictions, budget tier, preferred cuisine, and maximum distance radius.
   - Enter keyword queries to filter descriptions or locations.
   - View dynamically computed match scores (%) and distance matrix values.
   <img width="1261" height="617" alt="Screenshot 2026-08-05 142517" src="https://github.com/user-attachments/assets/5cd35fd3-68b8-4fda-9393-d8af5530b2f2" />


3. **Restaurant Detail (`/restaurant/<name>`):** Shows complete metadata, menu items, opening hours, and direct Google Maps navigation links.
   <img width="1264" height="621" alt="image" src="https://github.com/user-attachments/assets/d43cd36e-57ac-4c38-ad9f-14b8e614894a" />


*(Include screenshot images in `./docs/screenshots/` directory when submitting)*

---

## 🤝 GitHub Collaboration & Evidence

The repository maintains strict contribution hygiene:
* **Branches:** Feature branches used for isolation (`feature/inference-engine`, `feature/ui-flask`, `fix/routing`).
* **Pull Requests & Merges:** All code updates integrated via peer-reviewed Pull Requests.
* **Commit History:** Atomic commits detailing architectural progression.

---

## 📄 License
Distributed under the MIT License. Academic submission for USIU-Africa Knowledge-Based Systems course.
