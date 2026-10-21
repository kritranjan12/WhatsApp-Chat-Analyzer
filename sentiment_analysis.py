
import pandas as pd
import urllib.request
import zipfile
import io

# Download dataset directly from UCI
url = "https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip"

response = urllib.request.urlopen(url)
zip_data = io.BytesIO(response.read())

# Read dataset files
dataframes = []

with zipfile.ZipFile(zip_data, "r") as z:
    for filename in [
        "amazon_cells_labelled.txt",
        "imdb_labelled.txt",
        "yelp_labelled.txt"
    ]:
        file_path = next(
            f for f in z.namelist()
            if f.endswith(filename)
        )

        with z.open(file_path) as file:
            temp_df = pd.read_csv(
                file,
                sep="\t",
                header=None,
                names=["review", "sentiment"]
            )
            dataframes.append(temp_df)

# Combine all datasets
df = pd.concat(dataframes, ignore_index=True)

# Ensure correct data types
df["review"] = df["review"].astype(str)
df["sentiment"] = df["sentiment"].astype(int)

# Display results
print(df.head())
print("\nDataset shape:", df.shape)
print("\nSentiment counts:")
print(df["sentiment"].value_counts())
