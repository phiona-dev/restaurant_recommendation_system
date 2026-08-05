# Restaurant Recommendation System

A lightweight Flask-based expert system that recommends restaurants using rule-based filtering and heuristic scoring. The app reads a JSON knowledge base and ranks matching restaurants based on user preferences (cuisine, budget, dietary restrictions, distance, and quality metrics).

## Contents

- Features
- Tech stack
- Quickstart (install & run)
- Running tests
- Environment & configuration
- Troubleshooting
- Contributing

## Features

- Preference-driven discovery UI and restaurant detail pages
- Rule-based filtering (forward chaining) for hard constraints
- Heuristic scoring for ranked recommendations
- Local JSON knowledge base (`restaurants.json`)
- Unit tests with `unittest`/`pytest`

Tech stack

- Python 3.8+ (tested on 3.12)
- Flask for web server and templates
- Requests for optional routing API calls
- pytest / unittest for tests

Repository layout

```text
restaurant_recommendation_system/
├── app.py                 # Flask app + inference engine
├── restaurants.json      # Knowledge base
├── test_cases.py         # Example unit tests (unittest)
├── test_master_engine.py # Additional tests
├── templates/            # Jinja2 templates (landing/discover/detail)
├── static/               # CSS and static assets
└── README.md
```

Quickstart

1. Clone the repo and enter the folder:

```bash
git clone https://github.com/phiona-dev/restaurant_recommendation_system.git
cd restaurant_recommendation_system
```

2. (Optional) create and activate a virtual environment:

```powershell
# Windows PowerShell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. (Optional) set the OpenRouteService API key (used for distance matrix). If not provided, the app falls back to Haversine distances.

5. Start the app:

```powershell
python app.py
```

Open http://127.0.0.1:5000 in your browser.

Running tests

- Run all tests (recommended via module invocation to avoid PATH issues):

```powershell
python -m pytest -q
```

- Run a single test file:

```powershell
python -m pytest test_cases.py -q
```

- Run a single test function:

```powershell
python -m pytest test_cases.py::test_exact_cuisine_match -q
```

- Alternatively, run the unittest-style file directly:

```powershell
python test_cases.py
```

Troubleshooting

- pytest not found: If `pytest` was installed for your user but scripts are not on PATH, use `python -m pytest` or add the Scripts folder to your PATH. Example (PowerShell):

- Missing environment key: The app uses `ORS_API_KEY` for the OpenRouteService matrix endpoint. If absent, the app calculates distances with Haversine formula (approximate).

Notes for developers

- `app.py` contains the inference pipeline functions: `batch_calculate_distances`, `filter_by_hard_constraints`, `calculate_match_scores`, and `run_inference_engine`.
- The knowledge base schema is in `restaurants.json`. Add fields like `quality_of_food`, `aesthetics`, and `customer_service` to influence scoring.

Contact

- Repository: https://github.com/phiona-dev/restaurant_recommendation_system
