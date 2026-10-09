
import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --------------------------------------------------
# VERIFIED LBRCE KNOWLEDGE BASE
# Source: https://www.lbrce.ac.in/
# --------------------------------------------------

COLLEGE_KNOWLEDGE = """
COLLEGE NAME:
Lakireddy Bali Reddy College of Engineering (LBRCE).

LOCATION:
L.B. Reddy Nagar, Mylavaram, Krishna District,
Andhra Pradesh, India - 521230.

ABOUT:
The college was founded in 1998 through Lakireddy Bali Reddy
Charitable Trust by Sri Lakireddy Bali Reddy.
It is an autonomous institution approved by AICTE and
affiliated with Jawaharlal Nehru Technological University
Kakinada (JNTUK), according to the college website.

UNDERGRADUATE PROGRAMS:
The official courses page lists these B.Tech programs:
- Computer Science and Engineering (CSE)
- Computer Science and Engineering (Artificial Intelligence
  and Machine Learning)
- Artificial Intelligence and Data Science (AI&DS)
- Information Technology (IT)
- Electronics and Communication Engineering (ECE)
- Electrical and Electronics Engineering (EEE)
- Mechanical Engineering (ME)
- Civil Engineering (CE)
- Aerospace Engineering (ASE)

POSTGRADUATE PROGRAMS:
The official courses page lists:
- M.Tech in Computer Science and Engineering
- M.Tech in Thermal Engineering
- M.Tech in Power Electronics and Drives
- M.Tech in VLSI and Embedded Systems
- Master of Business Administration (MBA)

FACILITIES:
The college website describes a green campus, laboratories,
a digital library, sports facilities, gym, yoga facilities,
hostels, and other student-support facilities.

OFFICIAL LINKS:
College website: https://www.lbrce.ac.in/
Courses offered: https://www.lbrce.ac.in/courses.php
College overview: https://www.lbrce.ac.in/overview.php
Admissions: https://www.lbrce.ac.in/admissions.php
Course structures and syllabus:
https://www.lbrce.ac.in/course_structure.php
Contact information:
https://lbrce.ac.in/quicklinks_pages/contact.php
ERP portal: https://erp.lbrce.ac.in/

GENERAL CONTACT:
The official website lists the college phone number as
08659-222933. Check the official contact page for the
latest department-specific contact details.

IMPORTANT:
This knowledge base contains general information, not live
college announcements. Course offerings and contact details
may change. Direct students to the official website to verify
current details.
"""


# --------------------------------------------------
# CHATBOT INTERFACE
# --------------------------------------------------

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LBRCE AI Assistant</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 20px;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #f1f5f9;
    font-family: Arial, sans-serif;
}

.chat-container {
    width: 100%;
    max-width: 760px;
    height: 85vh;
    min-height: 500px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 8px 30px #00000018;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.header {
    background: linear-gradient(135deg, #123b75, #1768ac);
    color: white;
    text-align: center;
    padding: 24px 15px;
}

.header h1 { margin: 0 0 8px; font-size: 25px; }
.header p { margin: 0; font-size: 14px; }
.status { margin-top: 10px; font-size: 12px; color: #c9f7d4; }

.messages {
    flex: 1;
    overflow-y: auto;
    padding: 22px;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.message {
    max-width: 88%;
    padding: 13px 16px;
    border-radius: 14px;
    line-height: 1.6;
    font-size: 14px;
    overflow-wrap: anywhere;
    white-space: pre-wrap;
}

.bot { align-self: flex-start; background: #eef3f9; color: #1e293b; }
.user { align-self: flex-end; background: #1768ac; color: white; }

.suggestions {
    padding: 0 16px 12px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.suggestions button {
    border: 1px solid #cbd5e1;
    background: white;
    color: #174477;
    border-radius: 20px;
    padding: 9px 12px;
    cursor: pointer;
}

.suggestions button:hover { background: #eaf3ff; }

.input-area {
    display: flex;
    gap: 10px;
    padding: 16px;
    border-top: 1px solid #e2e8f0;
}

#question {
    flex: 1;
    min-width: 0;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 13px;
    font-size: 14px;
}

#send {
    background: #1768ac;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0 22px;
    cursor: pointer;
    font-weight: bold;
}

#send:disabled { opacity: 0.6; }

.footer {
    padding: 0 12px 12px;
    text-align: center;
    font-size: 11px;
    color: #64748b;
}

@media (max-width: 500px) {
    body { padding: 0; }
    .chat-container { height: 100vh; min-height: 100vh; border-radius: 0; }
    .header h1 { font-size: 21px; }
    .input-area { padding: 12px; }
    #send { padding: 0 16px; }
}
</style>
</head>

<body>
<div class="chat-container">
    <div class="header">
        <h1>🎓 LBRCE AI Assistant</h1>
        <p>Lakireddy Bali Reddy College of Engineering</p>
        <div class="status">● AI Assistant</div>
    </div>

    <div class="messages" id="messages">
        <div class="message bot">Hello! 👋 Welcome to the LBRCE AI Assistant.

I can help with college information, courses, admissions,
placements, ERP navigation, and educational questions.

What would you like to know?</div>
    </div>

    <div class="suggestions">
        <button onclick="askSuggestion('Tell me about LBRCE')">About LBRCE</button>
        <button onclick="askSuggestion('What B.Tech courses are offered?')">Courses</button>
        <button onclick="askSuggestion('How do I open the ERP portal?')">ERP Help</button>
        <button onclick="askSuggestion('How can I prepare for placements?')">Placements</button>
    </div>

    <div class="input-area">
        <input id="question" type="text" maxlength="2000"
               placeholder="Ask your question..." autocomplete="off">
        <button id="send" onclick="sendMessage()">Send</button>
    </div>

    <div class="footer">
        AI-generated answers may need verification.
        Check the official college website for confirmed information.
    </div>
</div>

<script>
const messages = document.getElementById("messages");
const input = document.getElementById("question");
const sendButton = document.getElementById("send");

function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = "message " + sender;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

function askSuggestion(text) {
    input.value = text;
    sendMessage();
}

async function sendMessage() {
    const message = input.value.trim();

    if (!message || sendButton.disabled) return;

    addMessage(message, "user");
    input.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "...";

    const loading = addMessage("Thinking...", "bot");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: message})
        });

        const data = await response.json();
        loading.textContent = data.reply || "No response received.";

        if (!response.ok) console.error("Chat error:", data);
    } catch (error) {
        loading.textContent =
            "Unable to connect. Please check your connection and try again.";
        console.error(error);
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        input.focus();
        messages.scrollTop = messages.scrollHeight;
    }
}

input.addEventListener("keydown", function(event) {
    if (event.key === "Enter") sendMessage();
});
</script>
</body>
</html>
"""


# --------------------------------------------------
# GROQ AI RESPONSE
# --------------------------------------------------

def get_reply(message):
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return "AI service is not configured. Please set GROQ_API_KEY."

    system_prompt = """
You are the LBRCE AI Assistant for Lakireddy Bali Reddy
College of Engineering, Andhra Pradesh.

Use the following college knowledge base when answering
questions about LBRCE.

COLLEGE KNOWLEDGE BASE:
""" + COLLEGE_KNOWLEDGE + """

RULES:
1. Use simple, polite English.
2. Prefer the supplied knowledge base for college-specific facts.
3. Do not invent college information, course details, exam dates,
   fee amounts, results, deadlines, or official notices.
4. The knowledge base is not a live feed. If asked about current
   exam dates, notices, results, or deadlines, say you cannot
   verify them and provide the relevant official website link.
5. For general educational questions, answer normally with examples.
6. The official ERP link is https://erp.lbrce.ac.in/
7. Never ask for or expose passwords, OTPs, or login credentials.
8. Do not claim to access individual student records or the live ERP.
9. You are an AI assistant, not an official college authority.
10. If information is not in the knowledge base, say so clearly.
11. Direct users to official links for confirmation.
"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": 0.2,
        "max_tokens": 800
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=45
        )

        if response.status_code != 200:
            print("Groq API error:", response.status_code, response.text)

            if response.status_code == 401:
                return "The AI API key was rejected. Please check your Groq key."

            if response.status_code == 429:
                return "The AI service usage limit was reached. Please try later."

            return "The AI service returned an error. Please try again."

        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "The AI service took too long to respond. Please try again."

    except requests.exceptions.RequestException as error:
        print("Network error:", error)
        return "Could not connect to the AI service. Please try again."

    except (KeyError, IndexError, ValueError) as error:
        print("Unexpected API response:", error)
        return "The AI service returned an unexpected response."


# --------------------------------------------------
# FLASK ROUTES
# --------------------------------------------------

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str):
        return jsonify({"reply": "Please enter a valid question."}), 400

    message = message.strip()

    if not message:
        return jsonify({"reply": "Please enter a question."}), 400

    if len(message) > 2000:
        return jsonify({"reply": "Please keep your question under 2000 characters."}), 400

    return jsonify({"reply": get_reply(message)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
