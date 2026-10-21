
import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# File paths
BASE_DIR = r"C:\Users\hnssh\Downloads\Kunal"
CSV_PATH = os.path.join(BASE_DIR, "combined_sentiment_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "sentiment_model.joblib")


# Train and save the model only if it does not exist
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("Saved model loaded successfully!")

else:
    print("Training sentiment model...")

    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=["review", "sentiment"])

    X = df["review"].astype(str)
    y = df["sentiment"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english")),
        ("classifier", LogisticRegression(max_iter=1000))
    ])

    model.fit(X_train, y_train)

    # Evaluate model
    predictions = model.predict(X_test)

    print(
        "Accuracy:",
        round(accuracy_score(y_test, predictions) * 100, 2),
        "%"
    )

    print(classification_report(
        y_test,
        predictions,
        target_names=["Negative", "Positive"]
    ))

    # Save trained model
    joblib.dump(model, MODEL_PATH)
    print("Model saved at:", MODEL_PATH)


# Analyze the ENTIRE conversation as one input
def analyze_conversation(messages):
    """
    messages: list of messages from one conversation.
    Returns one overall sentiment for the complete conversation.
    """

    # Remove empty messages
    messages = [
        str(message).strip()
        for message in messages
        if str(message).strip()
    ]

    if not messages:
        return {"error": "Conversation contains no messages."}

    # Combine every message into one conversation
    full_conversation = " ".join(messages)

    # Predict overall conversation sentiment ONCE
    prediction = int(model.predict([full_conversation])[0])
    probabilities = model.predict_proba([full_conversation])[0]

    classes = list(model.classes_)
    positive_probability = float(
        probabilities[classes.index(1)]
    )
    negative_probability = float(
        probabilities[classes.index(0)]
    )

    return {
        "total_messages": len(messages),
        "overall_sentiment": (
            "Positive" if prediction == 1 else "Negative"
        ),
        "positive_probability": round(
            positive_probability * 100, 2
        ),
        "negative_probability": round(
            negative_probability * 100, 2
        )
    }


# Example: an entire conversation with one user
conversation = [
    "Hi, I need help with my order.",
    "The product arrived late.",
    "I am disappointed with the delivery.",
    "However, the product quality is good.",
    "Thank you for helping me resolve this issue."
]

result = analyze_conversation(conversation)

print("\n--- COMPLETE CONVERSATION ANALYSIS ---")
for key, value in result.items():
    print(f"{key}: {value}")
