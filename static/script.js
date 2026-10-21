
const fileInput = document.getElementById("chatFile");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusText = document.getElementById("status");
const results = document.getElementById("results");

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

function setBar(id, percentage) {
    document.getElementById(id).style.width =
        `${Math.max(0, Math.min(100, percentage))}%`;
}

analyzeBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];

    if (!file) {
        statusText.textContent = "Please select a WhatsApp .txt file.";
        results.hidden = true;
        return;
    }

    const formData = new FormData();
    formData.append("chatFile", file);

    analyzeBtn.disabled = true;
    statusText.textContent = "Analyzing the complete conversation...";
    results.hidden = true;

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to analyze chat.");
        }

        setText("totalMessages", data.total_messages.toLocaleString());
        setText("totalUsers", data.total_users.toLocaleString());
        setText("topUser", data.top_user);

        // Overall conversation sentiment
        setText("overallSentiment", data.overall.sentiment);

        setText(
            "overallDescription",
            "Sentiment prediction for the entire combined conversation."
        );

        setText(
            "overallPositive",
            `${data.overall.positive_probability}%`
        );

        setText(
            "overallNegative",
            `${data.overall.negative_probability}%`
        );

        setBar(
            "overallPositiveBar",
            data.overall.positive_probability
        );

        setBar(
            "overallNegativeBar",
            data.overall.negative_probability
        );

        // Per-message counts are supplementary statistics.
        setText("positiveMessages", data.positive_messages);
        setText("negativeMessages", data.negative_messages);

        // Each participant's full conversation sentiment
        const userStats = document.getElementById("userStats");
        userStats.replaceChildren();

        data.user_stats.forEach(user => {
            const card = document.createElement("div");
            card.className = "card user-card";

            const title = document.createElement("h3");
            title.textContent = user.name;

            const count = document.createElement("p");
            count.textContent = `Messages: ${user.count}`;

            const sentiment = document.createElement("p");
            sentiment.textContent =
                `Overall sentiment: ${user.sentiment}`;

            const positive = document.createElement("p");
            positive.textContent =
                `Positive score: ${user.positive_probability}%`;

            const negative = document.createElement("p");
            negative.textContent =
                `Negative score: ${user.negative_probability}%`;

            card.append(title, count, sentiment, positive, negative);
            userStats.appendChild(card);
        });

        results.hidden = false;
        statusText.textContent = "Chat analysis completed successfully!";

    } catch (error) {
        statusText.textContent = error.message;
    } finally {
        analyzeBtn.disabled = false;
    }
});
