import os
from flask import Flask, request, jsonify, send_from_directory
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SIGNATURE = """
Sr Mohd Khairul Mohd Yunos
Registered Valuer, Estate Agent & Property Consultant
Ziyad Property Consultants Sdn Bhd
Phone: 013-342 6242
Email: mkhairul@ziyad.my
"""

PROMPTS = {
    "message": lambda d: f"""You are a professional property consultant assistant in Malaysia.
Draft a {d['type']} message in both Bahasa Malaysia and English.
Recipient: {d['recipient']}
Purpose: {d['purpose']}
Tone: {d['tone']}
Always sign off with:{SIGNATURE}
Format with headers: BAHASA MALAYSIA, ENGLISH""",

    "report": lambda d: f"""You are a certified property consultant and valuer in Malaysia.
Generate a professional property report with these details:
Address: {d['address']}
Type: {d['proptype']}
Land Area: {d['area']} sqft
Purpose: {d['purpose']}
Additional notes: {d['notes']}
Include: Executive Summary, Property Description, Market Analysis, Valuation Opinion, Recommendations.
Sign off with:{SIGNATURE}""",

    "followup": lambda d: f"""You are a professional property consultant assistant in Malaysia.
Based on this lead info, provide:
1. WhatsApp follow-up message in Bahasa Malaysia
2. Professional English email follow-up
3. Best next action to close this lead
Lead details:
- Name: {d['name']}
- Looking for: {d['interest']}
- Budget: RM {d['budget']}
- Last contact: {d['last_contact']}
- Status: {d['status']}
Always sign off with:{SIGNATURE}
Format with headers: WHATSAPP, EMAIL, NEXT ACTION""",

    "ask": lambda d: f"""You are a knowledgeable Malaysian property consultant assistant.
Answer this property-related question clearly and professionally:
{d['question']}
If relevant, sign off with:{SIGNATURE}""",

    "tasks": lambda d: f"""You are a personal assistant to a Malaysian property consultant.
Help organize and prioritize these tasks for today:
{d['tasks']}
Suggest a time schedule from 9am to 6pm.
Add reminders and tips where relevant.
Format clearly with: PRIORITY LIST, TIME SCHEDULE, REMINDERS""",

    "summarize": lambda d: f"""You are a professional property consultant assistant.
Summarize this document clearly and concisely:
{d['content']}
Provide: Key Points, Action Items, Important Dates/Deadlines (if any).""",

    "greeting": lambda d: f"""You are the personal assistant to Sr Mohd Khairul, a senior property consultant at Ziyad Property Consultants.
Generate a warm, motivational morning greeting message in Bahasa Malaysia for the property agents team.
Today's focus: {d['focus']}
Number of agents: {d['agents']}
Keep it short, friendly and professional. Include a property tip or motivation for the day.
End with the signature of Sr Mohd Khairul."""
}

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/suria.png")
def avatar():
    return send_from_directory(".", "suria.png")

@app.route("/pa", methods=["POST"])
def pa():
    data = request.json
    feature = data.get("feature")
    prompt = PROMPTS[feature](data)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify({"result": response.content[0].text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)