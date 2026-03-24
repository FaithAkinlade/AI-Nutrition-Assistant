# AI-Nutrition-Assistant

An AI-powered recipe recommendation system that suggests recipes based on ingredients you have on hand, with support for dietary preferences (vegan, vegetarian, gluten-free, dairy-free).

## Project Structure

```
AI_nutritionist/
  data/               # Dataset files (CSV)
  model/              # ML model files and scripts
    preprocess.py     # Cleans raw recipe data
    train.py          # Trains the recommendation model
    recommend.py      # Generates recipe recommendations
  backend/
    app.py            # FastAPI server
  frontend/
    streamlit_app.py  # Streamlit web interface
image_preprocessing_file.py  # Feature engineering and preprocessing
```

## Prerequisites

- Python 3.10+
- pip

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/AI-Nutrition-Assistant.git
   cd AI-Nutrition-Assistant
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   python -m venv .venv
   ```

   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - Windows (cmd): `.venv\Scripts\activate.bat`
   - macOS/Linux: `source .venv/bin/activate`

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example env file and fill in your paths:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `MODEL_DIR` and `DATA_DIR` to the absolute paths on your machine:

   ```
   MODEL_DIR=C:\Users\yourname\path\to\AI_nutritionist\model
   DATA_DIR=C:\Users\yourname\path\to\AI_nutritionist\data
   ```

5. **Add your dataset**

   Place `recipes_extended.csv` in your `DATA_DIR` folder.

## Usage

Run these steps in order:

### 1. Preprocess the data

Cleans the raw CSV and produces `recipes_cleaned.csv`:

```bash
python AI_nutritionist/model/preprocess.py
```

### 2. Train the model

Builds the TF-IDF vectorizer and Nearest Neighbors model, then saves them as `.pkl` files:

```bash
python AI_nutritionist/model/train.py
```

### 3. Test recommendations locally

Run `recommend.py` directly to verify the model works:

```bash
python AI_nutritionist/model/recommend.py
```

This runs a sample query (`chicken, garlic, butter` with `gluten_free` preference) and prints results.

### 4. Launch the Streamlit interface

> **Important:** Streamlit apps must be launched with the `streamlit run` command, **not** with `python`. Running with `python` directly will produce `missing ScriptRunContext` warnings and the app will not work.

```bash
streamlit run AI_nutritionist/frontend/streamlit_app.py
```

This starts a local server and opens the web UI in your browser (default `http://localhost:8501`), where you can enter ingredients, select a dietary preference, and get recipe recommendations.

### 5. Start the API server (alternative)

```bash
cd AI_nutritionist/backend
uvicorn app:app --reload
```

The server starts at `http://127.0.0.1:8000`.

### 6. Get recommendations (API)

Open your browser or use curl:

```
http://127.0.0.1:8000/recommend?ingredients=chicken,garlic,onion&preference=vegan&top_n=5
```

**Query parameters:**

| Parameter     | Required | Description                                                        |
|---------------|----------|--------------------------------------------------------------------|
| `ingredients` | Yes      | Comma-separated list of ingredients                                |
| `preference`  | No       | Dietary filter: `vegan`, `vegetarian`, `gluten_free`, `dairy_free` |
| `top_n`       | No       | Number of recipes to return (default: 5)                           |

**Example response:**

```json
{
  "recipes": [
    {
      "recipe_title": "Garlic Chicken Stir Fry",
      "ingredients": "['chicken', 'garlic', 'onion', 'soy sauce']",
      "directions": "['Heat oil...', 'Add chicken...']"
    }
  ]
}
```

## Running Tests

```bash
python -m pytest AI_nutritionist/tests/ -v
```

## API Endpoints

| Method | Path         | Description                    |
|--------|--------------|--------------------------------|
| GET    | `/`          | Health check                   |
| GET    | `/recommend` | Get recipe recommendations     |