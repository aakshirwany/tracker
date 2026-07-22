import csv
import datetime
import subprocess

from flask import Flask, jsonify, request, render_template

app = Flask(__name__, template_folder='.')

CSV_FILE = "data.csv"

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def load_entries():
    try:
        with open(CSV_FILE, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []

def save_entries_to_csv(entries):
    fieldnames = ["Seq", "Date", "Person", "Type", "Amount", "RunningBalance", "Description"]
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_NONE, escapechar="\\")
        writer.writeheader()
        writer.writerows(entries)

# -------------------------------------------------------------------
# Main View & Data Routes
# -------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    return jsonify(load_entries())

@app.route('/api/entries', methods=['POST'])
def add_entry():
    data = request.json or {}
    entries = load_entries()
    
    entry_type = data.get("type")
    person = data.get("person")
    try:
        amount = float(data.get("amount"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid amount"}), 400
        
    description = data.get("description", "").replace(",", " - ").strip()
    
    seq = len(entries) + 1
    date = datetime.date.today().strftime("%d-%b-%y")
    balance = float(entries[-1]["RunningBalance"]) if entries else 0
    balance += amount if entry_type.lower() == "contribution" else -amount

    new_entry = {
        "Seq": str(seq),
        "Date": date,
        "Person": person,
        "Type": entry_type.capitalize(),
        "Amount": str(amount),
        "RunningBalance": str(balance),
        "Description": description
    }
    
    entries.append(new_entry)
    save_entries_to_csv(entries)
    return jsonify({"success": True, "entries": entries})

@app.route('/api/entries/<seq>', methods=['DELETE'])
def delete_entry(seq):
    entries = load_entries()
    
    new_entries = [e for e in entries if e["Seq"] != seq]
    
    if len(new_entries) == len(entries):
        return jsonify({"success": False, "error": "Entry not found"}), 404

    balance = 0
    for i, e in enumerate(new_entries, start=1):
        e["Seq"] = str(i)
        amt = float(e["Amount"])
        balance += amt if e["Type"].lower() == "contribution" else -amt
        e["RunningBalance"] = str(balance)

    save_entries_to_csv(new_entries)
    return jsonify({"success": True, "entries": new_entries})

@app.route('/api/git-push', methods=['POST'])
def git_push():
    try:
        subprocess.run(["git", "add", CSV_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update tracker data via Web UI"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        return jsonify({"success": True, "message": "Pushed to GitHub successfully!"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

