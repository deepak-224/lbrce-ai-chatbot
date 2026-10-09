
import os
import re
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ==================================================
# 1. VERIFIED LBRCE FAQS
# Sources are official college website pages.
# ==================================================

FAQS = [
    {
        "keywords": ["erp", "student portal", "erp portal"],
        "answer": (
            "The LBRCE ERP portal is:\n"
            "https://erp.lbrce.ac.in/\n\n"
            "Sign in only through the official portal. Never share "
            "your password or OTP with the chatbot."
        )
    },
    {
        "keywords": ["affiliation", "affiliated", "which university"],
        "answer": (
            "According to the LBRCE Overview page, Lakireddy Bali "
            "Reddy College of Engineering is affiliated with "
            "Jawaharlal Nehru Technological University Kakinada "
            "(JNTUK) and is an autonomous institution.\n\n"
            "Official source:\n"
            "https://lbrce.ac.in/overview.php"
        )
    },
    {
        "keywords": ["b.tech courses", "btech courses", "ug courses",
                     "undergraduate courses", "branches offered",
                     "engineering branches", "list the courses",
                     "courses offered"],
        "answer": (
            "The official LBRCE Courses Offered page lists these "
            "B.Tech branches:\n\n"
            "1. Aerospace Engineering (ASE)\n"
            "2. Artificial Intelligence and Data Science (AI&DS)\n"
            "3. Civil Engineering (CE)\n"
            "4. Computer Science and Engineering (CSE)\n"
            "5. CSE (Artificial Intelligence and Machine Learning)\n"
            "6. Electrical and Electronics Engineering (EEE)\n"
            "7. Electronics and Communication Engineering (ECE)\n"
            "8. Information Technology (IT)\n"
            "9. Mechanical Engineering (ME)\n\n"
            "Check the official page for current offerings and intake:\n"
            "https://www.lbrce.ac.in/courses.php"
        )
    },
    {
        "keywords": ["m.tech courses", "mtech courses",
                     "postgraduate courses", "pg courses", "mba course"],
        "answer": (
            "The official LBRCE Courses Offered page lists these "
            "postgraduate programs:\n\n"
            "- M.Tech in Computer Science and Engineering\n"
            "- M.Tech in Thermal Engineering\n"
            "- M.Tech in Power Electronics and Drives\n"
            "- M.Tech in VLSI and Embedded Systems\n"
            "- Master of Business Administration (MBA)\n\n"
            "Program details can change. Check:\n"
            "https://www.lbrce.ac.in/courses.php"
        )
    },
    {
        "keywords": ["admission process", "how to get admission",
                     "admissions", "admission procedure",
                     "eapcet", "ecet", "icet", "pgecet"],
        "answer": (
            "LBRCE publishes its admission procedures and entrance "
            "test information on the official admissions page. "
            "The page describes EAPCET/ECET routes for undergraduate "
            "admissions, ICET for MBA, and PGECET/GATE routes for "
            "M.Tech. Verify the current year's rules before applying.\n\n"
            "Official page:\n"
            "https://lbrce.ac.in/admission_pages/admissions.php\n\n"
            "The college website lists the admission code as LBCE."
        )
    },
    {
        "keywords": ["syllabus", "course structure", "subject list",
                     "academic curriculum"],
        "answer": (
            "You can find LBRCE course structures and syllabus "
            "documents on the official website:\n\n"
            "https://www.lbrce.ac.in/course_structure.php\n\n"
            "Choose your branch and regulation to find the relevant "
            "documents."
        )
    },
    {
        "keywords": ["exam date", "exam schedule", "semester exam",
                     "next exam", "examination timetable",
                     "exam timetable", "when are exams"],
        "answer": (
            "I cannot verify the next semester examination date "
            "from the information available to me. I don't want "
            "to give you an incorrect date.\n\n"
            "Check the latest official college notices:\n"
            "https://www.lbrce.ac.in/\n\n"
            "For examination-related queries, the official contact "
            "page lists the Controller of Examinations at "
            "+91 93919 01585. Please verify the contact details "
            "on the page before calling:\n"
            "https://lbrce.ac.in/quicklinks_pages/contact.php"
        )
    },
    {
        "keywords": ["placement cell contact", "placement contact",
                     "placement phone", "placement officer",
                     "training and placements"],
        "answer": (
            "For placement-related queries, the LBRCE contact page "
            "lists Dr. Sujit Rath, Head of Training & Placements, "
            "with the phone numbers 8919482365 and 812529489.\n\n"
            "Please verify the current contact details on the "
            "official page:\n"
            "https://lbrce.ac.in/quicklinks_pages/contact.php"
        )
    },
    {
        "keywords": ["college contact", "college phone",
                     "contact number", "phone number",
                     "admission contact", "how to contact"],
        "answer": (
            "The official LBRCE website lists these main contact "
            "and admission enquiry numbers:\n\n"
            "- 08659-222933\n"
            "- 08659-222934\n"
            "- 08659-223936\n"
            "- 08659-223937\n"
            "- 7386349999\n"
            "- 9912030759\n\n"
            "For updated details and department contacts, visit:\n"
            "https://lbrce.ac.in/quicklinks_pages/contact.php"
        )
    },
    {
        "keywords": ["where is lbrce", "college location",
                     "college address", "where is the college",
                     "address of lbrce"],
        "answer": (
            "Lakireddy Bali Reddy College of Engineering is located "
            "at L.B. Reddy Nagar, Mylavaram, Krishna District, "
            "Andhra Pradesh, India - 521230.\n\n"
            "For directions and transport information, visit:\n"
            "https://www.lbrce.ac.in/"
        )
    },
    {
        "keywords": ["founded", "established", "started",
                     "when was lbrce"],
        "answer": (
            "According to the official LBRCE website, the college "
            "was founded in 1998 through the Lakireddy Bali Reddy "
            "Charitable Trust.\n\n"
            "Source: https://www.lbrce.ac.in/overview.php"
        )
    },
    {
        "keywords": ["official website", "college website",
                     "lbrce website", "website link"],
        "answer": (
            "The official LBRCE website is:\n"
            "https://www.lbrce.ac.in/"
        )
    }
]

# ==================================================
# 2. FIND A MATCHING FAQ
# ==================================================

def find_faq(message):
    question = re.sub(r"[^a-z0-9\s&]", " ", message.lower())
    question = " ".join(question.split())

    for faq in FAQS:
        for keyword in faq["keywords"]:
            if keyword in question:
                return faq["answer"]

    # Handle short/general college course questions.
    if ("course" in question or "branch" in question) and (
        "lbrce" in question or "college" in question
    ):
        return (
            "For the current list of LBRCE programs, visit:\n"
            "https://www.lbrce.ac.in/courses.php"
        )

    return None


# ==================================================
# 3. AI RESPONSE FOR OTHER QUESTIONS
# ==================================================

SYSTEM_PROMPT = """
You are the LBRCE AI Assistant for Lakireddy Bali Reddy
College of Engineering, Andhra Pradesh.

Use simple, polite English and organize answers clearly.

Official sources:
College: https://www.lbrce.ac.in/
Courses: https://www.lbrce.ac.in/courses.php
Admissions: https://lbrce.ac.in/admission_pages/admissions.php
Syllabus: https://www.lbrce.ac.in/course_structure.php
Contact: https://lbrce.ac.in/quicklinks_pages/contact.php
ERP: https://erp.lbrce.ac.in/

Rules:
1. Do not invent official college information, course details,
   fees, deadlines, results, exam dates, or notices.
2. Current information must be verified through official sources.
3. If you do not know a college-specific answer, say so and
   provide the relevant official website link.
4. For general educational and placement preparation questions,
   provide helpful advice.
5. Never ask for passwords, OTPs, or login credentials.
6. Do not claim to access private student records or the live ERP.
7. You are an AI assistant, not an official college authority.
"""


def get_ai_reply(message):
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return (
            "The AI service is not configured. Please check the "
            "GROQ_API_KEY environment variable in your hosting settings."
        )

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
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
                return "The AI API key was rejected. Please check the hosting settings."

            if response.status_code == 429:
                return "The AI service usage limit was reached. Please try later."

            return "The AI service returned an error. Please try again."

        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as error:
        print("AI connection error:", error)
        return "I could not connect to the AI service. Please try again."

    except (KeyError, IndexError, ValueError) as error:
        print("Unexpected AI response:", error)
        return "The AI service returned an unexpected response."


def get_reply(message):
    # Known FAQs use fixed answers rather than AI-generated facts.
    faq_answer = find_faq(message)

    if faq_answer:
        return faq_answer

    # Other questions go to the AI model.
    return get_ai_reply(message)


# ==================================================
# 4. CHATBOT WEB PAGE
# ==================================================

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
    margin: 0; padding: 20px; min-height: 100vh;
    display: flex; justify-content: center; align-items: center;
    background: #f1f5f9; font-family: Arial, sans-serif;
}
.chat-container {
    width: 100%; max-width: 760px; height: 85vh; min-height: 500px;
    background: white; border-radius: 18px;
    box-shadow: 0 8px 30px #00000018;
    display: flex; flex-direction: column; overflow: hidden;
}
.header {
    background: linear-gradient(135deg, #123b75, #1768ac);
    color: white; text-align: center; padding: 24px 15px;
}
.header h1 { margin: 0 0 8px; font-size: 25px; }
.header p { margin: 0; font-size: 14px; }
.messages {
    flex: 1; overflow-y: auto; padding: 22px;
    display: flex; flex-direction: column; gap: 15px;
}
.message {
    max-width: 88%; padding: 13px 16px; border-radius: 14px;
    line-height: 1.6; font-size: 14px;
    overflow-wrap: anywhere; white-space: pre-wrap;
}
.bot { align-self: flex-start; background: #eef3f9; color: #1e293b; }
.user { align-self: flex-end; background: #1768ac; color: white; }
.suggestions {
    padding: 0 16px 12px; display: flex; flex-wrap: wrap; gap: 8px;
}
.suggestions button {
    border: 1px solid #cbd5e1; background: white; color: #174477;
    border-radius: 20px; padding: 9px 12px; cursor: pointer;
}
.suggestions button:hover { background: #eaf3ff; }
.input-area {
    display: flex; gap: 10px; padding: 16px;
    border-top: 1px solid #e2e8f0;
}
#question {
    flex: 1; min-width: 0; border: 1px solid #cbd5e1;
    border-radius: 12px; padding: 13px; font-size: 14px;
}
#send {
    background: #1768ac; color: white; border: none;
    border-radius: 12px; padding: 0 22px; cursor: pointer;
}
#send:disabled { opacity: 0.6; }
.footer {
    padding: 0 12px 12px; text-align: center;
    font-size: 11px; color: #64748b;
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
    </div>

    <div class="messages" id="messages">
        <div class="message bot">Hello! 👋 Welcome to the LBRCE AI Assistant.

I can help with college FAQs, courses, admissions, ERP navigation,
placements, and educational questions.

What would you like to know?</div>
    </div>

    <div class="suggestions">
        <button onclick="askSuggestion('Tell me about LBRCE')">About LBRCE</button>
        <button onclick="askSuggestion('What B.Tech courses are offered?')">Courses</button>
        <button onclick="askSuggestion('What is the ERP portal?')">ERP Help</button>
        <button onclick="askSuggestion('How do I contact the placement cell?')">Placement Contact</button>
    </div>

    <div class="input-area">
        <input id="question" type="text" maxlength="2000"
               placeholder="Ask your question..." autocomplete="off">
        <button id="send" onclick="sendMessage()">Send</button>
    </div>

    <div class="footer">
        Verify changing information through the official college website.
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
            body: JSON.stringify({message})
        });
        const data = await response.json();
        loading.textContent = data.reply || "No response received.";
    } catch (error) {
        loading.textContent = "Unable to connect. Please try again.";
        console.error(error);
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        input.focus();
        messages.scrollTop = messages.scrollHeight;
    }
}

input.addEventListener("keydown", event => {
    if (event.key === "Enter") sendMessage();
});
</script>
</body>
</html>
"""


# ==================================================
# 5. FLASK ROUTES
# ==================================================

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
