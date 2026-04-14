# S.N.A.C.C. — Smart Nutrition Assistant Companion & Curator

An AI-powered recipe recommendation system that suggests recipes based on ingredients you have on hand. Supports dietary preference filtering, time-based filtering, and displays rich recipe metadata including prep/cook times, difficulty, cuisine, and dietary profiles.

## How It Works

1. **Preprocessing** cleans raw recipe data, normalizes ingredients and taste tags, removes duplicates, and builds a combined text feature for ML.
2. **Training** fits a TF-IDF vectorizer on the combined text (ingredients + description + tastes) and saves the vectorizer and processed dataframe as pickle files.
3. **Recommendation** transforms a user's ingredient query into the same TF-IDF space, applies dietary and time filters, then ranks recipes by cosine similarity.
4. **Serving** exposes recommendations via a FastAPI REST API and a Streamlit cookbook-style web UI.

## Project Structure

```
AI_nutritionist/
  model/
    preprocess.py      # Consolidated data cleaning and feature engineering
    train.py           # Fits TF-IDF vectorizer and saves model artifacts
    recommend.py       # Cosine similarity recommendation engine
  backend/
    app.py             # FastAPI REST API
  frontend/
    streamlit_app.py   # Streamlit web interface (cookbook layout)
  tests/
    test_api_inputs.py # API endpoint tests
```

## Prerequisites

- Python 3.10+
- pip

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/FaithAkinlade/AI-Nutrition-Assistant.git
   cd AI-Nutrition-Assistant
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # macOS/Linux
   .venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set the paths:

   ```
   MODEL_DIR=/absolute/path/to/AI_nutritionist/model
   DATA_DIR=/absolute/path/to/AI_nutritionist/data
   ```

5. **Add your dataset**

   Place `recipes_extended.csv` in your `DATA_DIR` folder.

## Usage

### 1. Preprocess the data

Cleans the raw CSV, engineers features, removes duplicates, and saves `recipes_cleaned.csv`:

```bash
python AI_nutritionist/model/preprocess.py
```

### 2. Train the model

Builds the TF-IDF vectorizer and saves it alongside the processed dataframe as pickle files:

```bash
python AI_nutritionist/model/train.py
```

### 3. Test recommendations locally

```bash
python AI_nutritionist/model/recommend.py
```

Runs a sample query (`chicken, garlic, butter` with `gluten_free` preference) and prints results.

### 4. Launch the Streamlit interface

```bash
streamlit run AI_nutritionist/frontend/streamlit_app.py
```

Opens the web UI at `http://localhost:8501`. Features:

- Ingredient input with comma-separated values
- Multi-select dietary filters (vegan, vegetarian, gluten-free, dairy-free)
- Prep and cook time limits
- Adjustable number of results (1-20)
- Cookbook-style two-page spread with pagination
- Recipe metadata: prep time, cook time, difficulty, cuisine, taste, dietary profile

### 5. Start the API server

```bash
cd AI_nutritionist/backend
uvicorn app:app --reload
```

The server starts at `http://127.0.0.1:8000`.

## API Reference

### `GET /`

Health check.

**Response:**
```json
{"message": "Recipe Recommendation API is running!"}
```

### `GET /recommend`

Returns recipe recommendations based on ingredients and optional filters.

**Query parameters:**

| Parameter       | Required | Type   | Description                                                             |
|-----------------|----------|--------|-------------------------------------------------------------------------|
| `ingredients`   | Yes      | string | Comma-separated list of ingredients (max 10 used)                       |
| `preference`    | No       | string | Dietary filter(s), comma-separated: `vegan`, `vegetarian`, `gluten_free`, `dairy_free` |
| `top_n`         | No       | int    | Number of recipes to return (default: 5)                                |
| `max_prep_time` | No       | int    | Maximum prep time in minutes                                            |
| `max_cook_time` | No       | int    | Maximum cook time in minutes                                            |

**Examples:**

```
/recommend?ingredients=chicken,garlic,onion
/recommend?ingredients=rice,beans&preference=vegan,gluten_free&top_n=3
/recommend?ingredients=pasta,tomato&max_cook_time=30
```

**Response:**

```json
{
  "recipes": [
    {
      "recipe_title": "Garlic Chicken Stir Fry",
      "ingredients": "['chicken', 'garlic', 'onion', 'soy sauce']",
      "directions": "['Heat oil...', 'Add chicken...']",
      "cuisine": "Asian",
      "difficulty": "easy",
      "est_prep_time_min": 10,
      "est_cook_time_min": 20,
      "dietary_profile": "gluten-free, dairy-free",
      "primary_taste": "savory",
      "description": "a quick weeknight stir fry..."
    }
  ]
}
```

## Running Tests

```bash
python -m pytest AI_nutritionist/tests/ -v
```

Tests cover: health check, single/multiple ingredient queries, dietary filters, multi-filter combinations, time-based filters, response shape validation, missing parameters, and edge cases.

## Architecture

```
User Input
    |
    v
[Streamlit UI] --or-- [FastAPI API]
    |                       |
    +-----------+-----------+
                |
                v
        [recommend.py]
        - Loads model artifacts once (cached via lru_cache)
        - Applies dietary + time filters
        - TF-IDF transforms query
        - Cosine similarity ranking
        - Returns top-N results
                |
                v
        [Model Artifacts]
        - tfidf_vectorizer.pkl (fitted TF-IDF)
        - recipes.pkl (processed dataframe)
```

## Dependencies

- **pandas** — data manipulation
- **scikit-learn** — TF-IDF vectorization and cosine similarity
- **FastAPI** / **uvicorn** — REST API
- **Streamlit** — web UI
- **python-dotenv** — environment variable management
- **httpx** / **pytest** — testing
