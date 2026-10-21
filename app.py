
import os
import re
import joblib
import pandas as pd

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "sentiment_model.joblib")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}. "
        "Save your trained model in this project folder first."
    )

# Load model only once
model = joblib.load(MODEL_PATH)

# Supports common WhatsApp exports:
# 12/31/25, 10:30 PM - Rahul: Hello
# 31/12/25, 22:30 - Rahul: Hello
# [31/12/25, 22:30:00] Rahul: Hello
MESSAGE_START = re.compile(
    r"^\[?"
    r"\d{1,4}[/-]\d{1,2}[/-]\d{2,4},?\s+"
    r"\d{1,2}:\d{2}(?::\d{2})?\s*"
    r"(?:AM|PM|am|pm)?"
    r"\]?\s*(?:[-–]\s*)?(.*)$"
)

SYSTEM_TEXTS = [
    "messages and calls are end-to-end encrypted",
    "created group",
    "added ",
    "removed ",
    "left",
    "changed the subject",
    "changed this group's icon",
    "joined using this group's invite link",
]


def parse_whatsapp_chat(text):
    messages = []
    current_sender = None
    current_parts = []

    def save_message():
        if current_sender is not None:
            content = "\n".join(current_parts).strip()

            if content and not re.match(
                r"^(?:this message was deleted|you deleted this message)$",
                content,
                re.IGNORECASE
            ):
                messages.append({
                    "sender": current_sender,
                    "text": content
                })

    for line in text.lstrip("\ufeff").splitlines():
        match = MESSAGE_START.match(line)

        if match:
            save_message()

            remainder = match.group(1)
            current_sender = None
            current_parts = []

            # Split sender from message content.
            sender_match = re.match(
                r"^([^:\n]+):\s?(.*)$",
                remainder
            )

            if sender_match:
                sender = sender_match.group(1).strip()
                content = sender_match.group(2).strip()

                if sender and content:
                    lower_content = content.lower()

                    # Ignore common system notifications.
                    is_system = any(
                        phrase in lower_content
                        for phrase in SYSTEM_TEXTS
                    )

                    if not is_system:
                        current_sender = sender
                        current_parts = [content]

        elif current_sender is not None:
            # Preserve multiline messages.
            current_parts.append(line)

    save_message()
    return messages


def predict_sentiment(text):
    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)

    positive = float(probabilities[classes.index(1)])
    negative = float(probabilities[classes.index(0)])

    prediction = int(model.predict([text])[0])

    return {
        "sentiment": "Positive" if prediction == 1 else "Negative",
        "positive_probability": round(positive * 100, 2),
        "negative_probability": round(negative * 100, 2)
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    uploaded_file = request.files.get("chatFile")

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "Please select a WhatsApp .txt file."}), 400

    if not uploaded_file.filename.lower().endswith(".txt"):
        return jsonify({"error": "Please upload a .txt chat export."}), 400

    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        uploaded_file.stream.seek(0)
        text = uploaded_file.read().decode("utf-8", errors="replace")

    messages = parse_whatsapp_chat(text)

    if not messages:
        return jsonify({
            "error": (
                "No messages were detected. "
                "Please check the WhatsApp export format."
            )
        }), 400

    # Group complete messages by participant.
    participant_messages = {}

    for message in messages:
        participant_messages.setdefault(
            message["sender"], []
        ).append(message["text"])

    # Overall conversation sentiment:
    # Combine all messages and predict once for the entire chat.
    full_conversation = "\n".join(
        message["text"] for message in messages
    )

    overall = predict_sentiment(full_conversation)

    # Additional counts: classify messages for aggregate statistics only.
    message_predictions = model.predict([
        message["text"] for message in messages
    ])

    positive_count = int((message_predictions == 1).sum())
    negative_count = int((message_predictions == 0).sum())

    # Analyze each participant's entire collection of messages.
    user_stats = []

    for name, user_messages in participant_messages.items():
        combined_user_text = "\n".join(user_messages)

        user_sentiment = predict_sentiment(combined_user_text)

        user_stats.append({
            "name": name,
            "count": len(user_messages),
            **user_sentiment
        })

    user_stats.sort(key=lambda item: item["count"], reverse=True)

    return jsonify({
        "total_messages": len(messages),
        "total_users": len(participant_messages),
        "top_user": user_stats[0]["name"],
        "overall": overall,
        "positive_messages": positive_count,
        "negative_messages": negative_count,
        "user_stats": user_stats
    })


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "File is too large. Maximum file size is 16 MB."
    }), 413


if __name__ == "__main__":
    app.run(debug=True)
