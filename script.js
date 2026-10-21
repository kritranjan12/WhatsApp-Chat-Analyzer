
const fileInput = document.getElementById("chatFile");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusText = document.getElementById("status");
const results = document.getElementById("results");

analyzeBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];

    if (!file) {
        statusText.textContent = "Pehle WhatsApp chat ki .txt file select karo.";
        results.hidden = true;
        return;
    }

    try {
        const text = await file.text();
        const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/);

        // WhatsApp exported chat formats:
        // 12/31/25, 10:30 PM - Rahul: Hello
        // [31/12/25, 22:30:00] Rahul: Hello
        
        const messageStart =
            /^\[?\d{1,4}[/-]\d{1,2}[/-]\d{1,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\]?\s*(?:[-–]\s*)?/;

        const users = {};
        let totalMessages = 0;
        let currentMessageIsUserMessage = false;

        for (const line of lines) {
            if (messageStart.test(line)) {
                const message = line.replace(messageStart, "");
                const separator = message.indexOf(": ");

                currentMessageIsUserMessage = false;

                if (separator > 0) {
                    const user = message.slice(0, separator).trim();
                    const content = message.slice(separator + 2).trim();

                    // Exclude common system notifications.
                    const systemMessages = [
                        "Messages and calls are end-to-end encrypted",
                        "created group",
                        "added",
                        "left",
                        "changed the subject",
                        "changed this group's icon",
                        "joined using this group's invite link"
                    ];

                    const isSystemMessage = systemMessages.some(item =>
                        content.toLowerCase().includes(item.toLowerCase())
                    );

                    if (
                        user &&
                        !user.includes("‎") &&
                        !isSystemMessage &&
                        !/^(?:This message was deleted|You deleted this message)$/i.test(content)
                    ) {
                        users[user] = (users[user] || 0) + 1;
                        totalMessages++;
                        currentMessageIsUserMessage = true;
                    }
                }
            } else if (line.trim() && !currentMessageIsUserMessage) {
                // Ignore unrelated lines; multiline message handling is limited.
                continue;
            }
        }

        const sortedUsers = Object.entries(users)
            .sort((a, b) => b[1] - a[1]);

        document.getElementById("totalMessages").textContent =
            totalMessages.toLocaleString();

        document.getElementById("totalUsers").textContent =
            sortedUsers.length.toLocaleString();

        document.getElementById("topUser").textContent =
            sortedUsers.length ? sortedUsers[0][0] : "Not found";

        const userStats = document.getElementById("userStats");
        userStats.replaceChildren();

        for (const [name, count] of sortedUsers) {
            const item = document.createElement("li");
            item.textContent = `${name}: ${count} messages`;
            userStats.appendChild(item);
        }

        results.hidden = false;

        statusText.textContent = totalMessages
            ? "Chat analysis complete!"
            : "Messages nahi mile. Exported chat ka format check karo.";
    } catch (error) {
        results.hidden = true;
        statusText.textContent =
            "File read nahi ho saki. Kripya valid .txt file select karo.";
    }
});
