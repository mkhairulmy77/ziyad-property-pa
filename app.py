import os
import json
from flask import Flask, request, jsonify, send_from_directory, session
import anthropic

app = Flask(__name__, static_folder='/app', static_url_path='')
app.secret_key = os.environ.get("SECRET_KEY", "suria-ziyad-2026")
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Passwords — set in Railway Environment Variables ───
PASSWORDS = {
    "principal": os.environ.get("PW_PRINCIPAL", ""),
    "admin":     os.environ.get("PW_ADMIN", ""),
    "manager":   os.environ.get("PW_MANAGER", ""),
    "agent":     os.environ.get("PW_AGENT", "")
}

SIGNATURE = """
Sr Mohd Khairul Mohd Yunos
Registered Valuer, Estate Agent & Property Consultant
Ziyad Property Consultants Sdn Bhd
Phone: 013-342 6242
Email: mkhairul@ziyad.my
"""

MARKETING_LOG_FILE = "/app/marketing_logs.json"
PROJECTS_FILE      = "/app/projects.json"

def load_logs():
    if os.path.exists(MARKETING_LOG_FILE):
        with open(MARKETING_LOG_FILE) as f:
            return json.load(f)
    return {}

def save_logs(logs):
    with open(MARKETING_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def load_projects():
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE) as f:
            return json.load(f)
    return {"projects": [], "leads": {}}

def save_projects(data):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

PROMPTS = {
    "message": lambda d: f"""You are a professional property consultant assistant in Malaysia.
Draft a {d['type']} message in both Bahasa Malaysia and English.
Recipient: {d['recipient']}
Purpose: {d['purpose']}
Tone: {d['tone']}
Always sign off with:{SIGNATURE}
Format with headers: BAHASA MALAYSIA, ENGLISH""",

    "report": lambda d: f"""You are a certified property consultant and valuer in Malaysia.
Generate a professional property report:
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
Format clearly with: PRIORITY LIST, TIME SCHEDULE, REMINDERS""",

    "summarize": lambda d: f"""You are a professional property consultant assistant.
Summarize this document clearly and concisely:
{d['content']}
Provide: Key Points, Action Items, Important Dates/Deadlines (if any).""",

    "greeting": lambda d: f"""You are the personal assistant to Sr Mohd Khairul at Ziyad Property Consultants.
Generate a warm, motivational morning greeting in Bahasa Malaysia for the agents team.
Today's focus: {d['focus']}
Number of agents: {d['agents']}
Keep it short, friendly and professional. Include a property tip or motivation.
End with the signature of Sr Mohd Khairul.""",

    "listing": lambda d: f"""You are a professional property marketing specialist and copywriter in Malaysia.
Generate compelling property listing content:

Property Type: {d['proptype']}
Tenure: {d['tenure']}
Address: {d['address']}
Built-up Area: {d.get('builtup') or 'Not specified'}
Land Area: {d['landarea']} sqft
Bedrooms: {d['bedrooms']} | Bathrooms: {d['bathrooms']} | Car Park: {d['carpark']}
Furnishing: {d['furnishing']} | Condition: {d['condition']}
Key Features: {d['features']}
Asking Price: RM {d['price']}
Target Buyer: {d['targetbuyer']}
Special Selling Points: {d.get('specialpoints') or 'None'}
Language Output: {d['language']}

Generate:
1. IPROPERTY / MUDAH LISTING (English) — SEO-friendly, 3-4 paragraphs
2. FACEBOOK / WHATSAPP POST — catchy, emojis, max 150 words each, BM and English
3. KEY HIGHLIGHTS — 5-7 bullet points
4. PRICE JUSTIFICATION — 2-3 sentences

Sign off with:{SIGNATURE}""",

    "listing_copy": lambda d: f"""You are a professional property marketing specialist in Malaysia.
Generate social media marketing content for this property:

Property: {d['title']}
Address: {d['address']}
Type: {d['proptype']}
Price: RM {d['price']}
Bedrooms: {d.get('bedrooms','N/A')} | Bathrooms: {d.get('bathrooms','N/A')}
Land: {d.get('land','N/A')} sqft | Built-up: {d.get('builtup','N/A')} sqft
Tenure: {d.get('tenure','N/A')} | Status: {d.get('status','For Sale')}
Days on market: {d.get('days',0)} | Portal views: {d.get('views',0)}
Platform: {d['platform']}

Generate for {d['platform']} in BOTH Bahasa Malaysia AND English.
- Facebook: engaging, emojis, call to action, max 200 words each
- WhatsApp: short, punchy, max 100 words each
- iProperty/Mudah: professional, English only, 150-250 words

End with:{SIGNATURE}
Phone: 013-342 6242""",

    "briefing": lambda d: f"""You are SURIA, the personal AI assistant of Sr Mohd Khairul Mohd Yunos, a Registered Valuer and Estate Agent at Ziyad Property Consultants Sdn Bhd.

He has just said "Hi SURIA" to wake you up. Respond warmly and professionally.

Current time: {d['time']}
Greeting: {d['greeting']}
Listing marketing status: {d['marketing_info']}

Generate a short, warm, personalised daily briefing for Sr Khairul in English. Include:
1. A warm greeting using {d['greeting']} and his name
2. Today's date and day
3. A quick motivational line for a property consultant
4. Marketing reminder based on: {d['marketing_info']}
5. Ask what he needs help with today

Keep it short, friendly and professional — like a real PA greeting her boss. Max 150 words.""",

    "lead_followup": lambda d: f"""You are a professional property consultant assistant in Malaysia.
Generate a follow-up message for this project lead:

Project: {d['project']}
Lead: {d['lead_name']} | Phone: {d['phone']}
Unit: {d.get('unit','N/A')} | Budget: RM {d.get('budget','N/A')}
Status: {d['status']} | Notes: {d.get('notes','None')}

Generate:
1. WhatsApp message in Bahasa Malaysia
2. WhatsApp message in English
3. Suggested next action

Keep messages short and conversational.
Sign off with:{SIGNATURE}
Phone: 013-342 6242"""
}

# ── Auth ───────────────────────────────────────────────

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    role = data.get("role","").lower()
    password = data.get("password","")
    name = data.get("name","").strip()
    if role not in PASSWORDS:
        return jsonify({"success": False, "message": "Invalid role."})
    if password != PASSWORDS[role]:
        return jsonify({"success": False, "message": "Wrong password. Please try again."})
    if role == "agent" and not name:
        return jsonify({"success": False, "message": "Please enter your name."})
    session["role"] = role
    session["name"] = name if role == "agent" else role.capitalize()
    return jsonify({"success": True, "role": role, "name": session["name"]})

@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/auth/check", methods=["GET"])
def auth_check():
    if "role" in session:
        return jsonify({"logged_in": True, "role": session["role"], "name": session["name"]})
    return jsonify({"logged_in": False})

# ── Static ─────────────────────────────────────────────

@app.route("/")
def home():
    return send_from_directory("/app", "index.html")

@app.route("/listings")
def listings_page():
    return send_from_directory("/app", "listings.html")

@app.route("/suria.png")
def avatar():
    return send_from_directory("/app", "suria.png")

# ── AI ─────────────────────────────────────────────────

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

# ── Marketing logs ─────────────────────────────────────

@app.route("/marketing/log", methods=["POST"])
def add_marketing_log():
    data = request.json
    pid = str(data.get("property_id"))
    logs = load_logs()
    if pid not in logs:
        logs[pid] = []
    logs[pid].append({
        "date": data.get("date"), "platform": data.get("platform"),
        "action": data.get("action"), "notes": data.get("notes","")
    })
    save_logs(logs)
    return jsonify({"success": True})

@app.route("/marketing/logs", methods=["GET"])
def get_all_logs():
    return jsonify({"logs": load_logs()})

@app.route("/marketing/delete", methods=["POST"])
def delete_marketing_log():
    data = request.json
    pid = str(data.get("property_id"))
    index = data.get("index")
    logs = load_logs()
    if pid in logs and 0 <= index < len(logs[pid]):
        logs[pid].pop(index)
        save_logs(logs)
    return jsonify({"success": True})

# ── CRM ────────────────────────────────────────────────

@app.route("/crm/projects", methods=["GET"])
def get_projects():
    return jsonify(load_projects())

@app.route("/crm/project/add", methods=["POST"])
def add_project():
    import time
    req = request.json
    data = load_projects()
    project = {
        "id": str(int(time.time())),
        "name": req.get("name"), "developer": req.get("developer"),
        "location": req.get("location"), "type": req.get("type"),
        "price_min": req.get("price_min"), "price_max": req.get("price_max"),
        "launch_date": req.get("launch_date"), "completion_date": req.get("completion_date"),
        "commission": req.get("commission"), "status": req.get("status","Active"),
        "created": req.get("date","")
    }
    data["projects"].append(project)
    save_projects(data)
    return jsonify({"success": True, "project": project})

@app.route("/crm/project/update", methods=["POST"])
def update_project():
    req = request.json
    pid = req.get("id")
    data = load_projects()
    for project in data["projects"]:
        if project["id"] == pid:
            project["name"]            = req.get("name",            project["name"])
            project["developer"]       = req.get("developer",       project["developer"])
            project["location"]        = req.get("location",        project["location"])
            project["type"]            = req.get("type",            project["type"])
            project["status"]          = req.get("status",          project["status"])
            project["price_min"]       = req.get("price_min",       project["price_min"])
            project["price_max"]       = req.get("price_max",       project["price_max"])
            project["launch_date"]     = req.get("launch_date",     project["launch_date"])
            project["completion_date"] = req.get("completion_date", project["completion_date"])
            project["commission"]      = req.get("commission",      project["commission"])
            break
    save_projects(data)
    return jsonify({"success": True})

@app.route("/crm/project/delete", methods=["POST"])
def delete_project():
    req = request.json
    pid = req.get("id")
    data = load_projects()
    data["projects"] = [p for p in data["projects"] if p["id"] != pid]
    if pid in data["leads"]:
        del data["leads"][pid]
    save_projects(data)
    return jsonify({"success": True})

@app.route("/crm/lead/add", methods=["POST"])
def add_lead():
    import time
    req = request.json
    pid = req.get("project_id")
    data = load_projects()
    if pid not in data["leads"]:
        data["leads"][pid] = []
    lead = {
        "id": str(int(time.time())),
        "name": req.get("name"), "phone": req.get("phone"),
        "source": req.get("source"), "agent": req.get("agent"),
        "unit": req.get("unit",""), "budget": req.get("budget",""),
        "status": req.get("status","New"),
        "follow_up_date": req.get("follow_up_date",""),
        "notes": req.get("notes",""), "created": req.get("date","")
    }
    data["leads"][pid].append(lead)
    save_projects(data)
    return jsonify({"success": True, "lead": lead})

@app.route("/crm/lead/update", methods=["POST"])
def update_lead():
    req = request.json
    pid = req.get("project_id")
    lid = req.get("lead_id")
    data = load_projects()
    for lead in data["leads"].get(pid,[]):
        if lead["id"] == lid:
            lead["status"]         = req.get("status",         lead["status"])
            lead["notes"]          = req.get("notes",          lead["notes"])
            lead["follow_up_date"] = req.get("follow_up_date", lead["follow_up_date"])
            lead["unit"]           = req.get("unit",           lead["unit"])
            lead["budget"]         = req.get("budget",         lead["budget"])
            break
    save_projects(data)
    return jsonify({"success": True})

@app.route("/crm/lead/delete", methods=["POST"])
def delete_lead():
    req = request.json
    pid = req.get("project_id")
    lid = req.get("lead_id")
    data = load_projects()
    if pid in data["leads"]:
        data["leads"][pid] = [l for l in data["leads"][pid] if l["id"] != lid]
    save_projects(data)
    return jsonify({"success": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)
