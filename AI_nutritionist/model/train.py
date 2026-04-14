import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import pickle
from dotenv import load_dotenv

load_dotenv()

MODEL_DIR = os.environ["MODEL_DIR"]
DATA_DIR = os.environ["DATA_DIR"]

# -------------------------------
# Step 1: Load cleaned CSV
# -------------------------------
csv_path = os.path.join(DATA_DIR, "recipes_cleaned.csv")

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"{csv_path} does not exist. Run preprocess.py first.")

df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} recipes.")

# -------------------------------
# Step 2: TF-IDF Vectorization
# -------------------------------
# IMPORTANT: use combined_text (not 'combined')
vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df['combined_text'])

print("TF-IDF matrix created:", tfidf_matrix.shape)

# -------------------------------
# Step 3: Save vectorizer & data
# -------------------------------
vectorizer_path = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')
data_path = os.path.join(MODEL_DIR, 'recipes.pkl')

with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

# Save dataframe for later use (VERY IMPORTANT)
df.to_pickle(data_path)

print(f"Vectorizer saved at {vectorizer_path}")
print(f"Data saved at {data_path}")

print("✅ Training complete! Use recommend.py to generate recommendations.")