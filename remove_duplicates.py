import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.environ["DATA_DIR"]

# Load data
input_file = os.path.join(DATA_DIR, "recipes_cleaned.csv")
output_file = os.path.join(DATA_DIR, "recipes_cleaned_no_dups.csv")

df = pd.read_csv(input_file)
print(f"Loaded {len(df)} rows from recipes_cleaned.csv")

# Remove duplicate rows
df_no_dups = df.drop_duplicates()
removed = len(df) - len(df_no_dups)
print(f"Removed {removed} duplicate rows")
print(f"Remaining: {len(df_no_dups)} rows")

# Save deduplicated data
df_no_dups.to_csv(output_file, index=False)
print(f"Saved to {output_file}")
