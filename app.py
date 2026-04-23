import os
import json
from flask import Flask, request, jsonify, send_from_directory
import anthropic

app = Flask(__name__, static_folder='/app', static_url_path='')
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SIGNATURE = """
Sr Mohd Khairul Mohd Yunos
Registered Valuer, Estate Agent & Property Consultant
Ziyad Property Consultants Sdn Bhd
Phone: 013-342 6242
Email: mkhairul@ziyad.my
"""

MARKETING_LOG_FILE = "/app/marketing_logs.json"

def load_logs():
    if os.path.exists(MARKETING_LOG_FILE):
        with open(MARKETING_LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_logs(logs):
    with open(MARKETING_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

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
End with the signature of Sr Mohd Khairul.""",

    "listing": lambda d: f"""You are a professional property marketing specialist and copywriter in Malaysia.
Generate compelling property listing content based on these details:

Property Type: {d['proptype']}
Tenure: {d['tenure']}
Address / Location: {d['address']}
Built-up Area: {d.get('builtup') or 'Not specified'}
Land Area: {d['landarea']} sqft
Bedrooms: {d['bedrooms']}
Bathrooms: {d['bathrooms']}
Car Park: {d['carpark']}
Furnishing: {d['furnishing']}
Condition: {d['condition']}
Key Features: {d['features']}
Asking Price: RM {d['price']}
Target Buyer: {d['targetbuyer']}
Special Selling Points: {d.get('specialpoints') or 'None'}
Language Output: {d['language']}

Please generate ALL of the following sections:

1. IPROPERTY / MUDAH LISTING (English)
Write a professional, SEO-friendly listing with headline, full description (3-4 paragraphs), and key property details.

2. FACEBOOK / WHATSAPP POST
Write a short, catchy and engaging post in Bahasa Malaysia and English. Use emojis. Max 150 words per version.

3. KEY HIGHLIGHTS
List 5-7 bullet points of the property's strongest selling points.

4. PRICE JUSTIFICATION
Write 2-3 sentences explaining why the asking price is reasonable.

Sign off with:{SIGNATURE}""",

    "listing_copy": lambda d: f"""You are a professional property marketing specialist in Malaysia.
Generate social media marketing content for this property:

Property: {d['title']}
Address: {d['address']}
Type: {d['proptype']}
Price: RM {d['price']}
Bedrooms: {d.get('bedrooms', 'N/A')} | Bathrooms: {d.get('bathrooms', 'N/A')}
Land Area: {d.get('land', 'N/A')} sqft | Built-up: {d.get('builtup', 'N/A')} sqft
Tenure: {d.get('tenure', 'N/A')} | Status: {d.get('status', 'For Sale')}
Days on market: {d.get('days', 0)} days | Portal views: {d.get('views', 0)}
Platform: {d['platform']}

Generate compelling copy for {d['platform']} in BOTH Bahasa Malaysia AND English.

- Facebook post: Engaging, with emojis, highlights, strong call to action. Max 200 words each.
- WhatsApp broadcast: Short, punchy, key details + contact. Max 100 words each.
- iProperty/Mudah: Professional listing description with headline. English only, 150-250 words.

Always end with:{SIGNATURE}
Include phone: 013-342 6242"""
}

@app.route("/")
def home():
    return send_from_directory("/app", "index.html")

@app.route("/listings")
def listings_page():
    return send_from_directory("/app", "listings.html")

@app.route("/suria.png")
def avatar():
    return send_from_directory("/app", "suria.png")

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

@app.route("/marketing/log", methods=["POST"])
def add_marketing_log():
    data = request.json
    property_id = str(data.get("property_id"))
    logs = load_logs()
    if property_id not in logs:
        logs[property_id] = []
    logs[property_id].append({
        "date": data.get("date"),
        "platform": data.get("platform"),
        "action": data.get("action"),
        "notes": data.get("notes", ""),
        "result": data.get("result", "")
    })
    save_logs(logs)
    return jsonify({"success": True, "logs": logs[property_id]})

@app.route("/marketing/logs/<property_id>", methods=["GET"])
def get_marketing_logs(property_id):
    logs = load_logs()
    return jsonify({"logs": logs.get(str(property_id), [])})

@app.route("/marketing/logs", methods=["GET"])
def get_all_logs():
    return jsonify({"logs": load_logs()})

@app.route("/marketing/delete", methods=["POST"])
def delete_marketing_log():
    data = request.json
    property_id = str(data.get("property_id"))
    index = data.get("index")
    logs = load_logs()
    if property_id in logs and 0 <= index < len(logs[property_id]):
        logs[property_id].pop(index)
        save_logs(logs)
    return jsonify({"success": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)