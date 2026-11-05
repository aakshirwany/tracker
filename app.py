import csv
import datetime
import os
import subprocess

from flask import Flask, jsonify, request, render_template

app = Flask(__name__, template_folder='.')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "data.csv")

# Helper to parse dates like "15-Jul-26" or "15.07.2026" for proper sorting
def parse_entry_date(date_str):
    if not date_str:
        return datetime.date.min
    for fmt in ("%d-%b-%y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    return datetime.date.min

def load_entries():
    try:
        with open(CSV_FILE, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []

def process_and_save_entries(entries):
    """
    1. Sorts entries chronologically (oldest first) to compute correct running balance & seq.
    2. Sorts entries with newest first for CSV output.
    3. Saves to data.csv.
    """
    if not entries:
        save_entries_to_csv([])
        return []

    # Sort entries by date ascending (oldest first) to accurately calculate sequence and running balance
    entries_sorted_asc = sorted(entries, key=lambda e: parse_entry_date(e.get("Date", "")))

    balance = 0.0
    for i, e in enumerate(entries_sorted_asc, start=1):
        e["Seq"] = str(i)
        amt = float(e["Amount"])
        balance += amt if e["Type"].lower() == "contribution" else -amt
        e["RunningBalance"] = f"{balance:.2f}"

    # Sort entries by date descending (newest first) for saving to CSV
    entries_sorted_desc = sorted(entries_sorted_asc, key=lambda e: parse_entry_date(e.get("Date", "")), reverse=True)

    save_entries_to_csv(entries_sorted_desc)
    return entries_sorted_desc

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
    
    entry_type = data.get("type", "Expense").capitalize()
    person = data.get("person", "")
    try:
        amount = float(data.get("amount"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid amount"}), 400
        
    description = data.get("description", "").replace(",", " - ").strip()
    date = data.get("date") or datetime.date.today().strftime("%d-%b-%y")

    new_entry = {
        "Seq": "0",
        "Date": date,
        "Person": person,
        "Type": entry_type,
        "Amount": str(amount),
        "RunningBalance": "0",
        "Description": description
    }
    
    entries.append(new_entry)
    updated_entries = process_and_save_entries(entries)
    return jsonify({"success": True, "entries": updated_entries})

@app.route('/api/entries/<seq>', methods=['PUT'])
def update_entry(seq):
    data = request.json or {}
    entries = load_entries()
    
    found = False
    for e in entries:
        if e["Seq"] == seq:
            found = True
            if "date" in data:
                e["Date"] = data["date"]
            if "type" in data:
                e["Type"] = data["type"].capitalize()
            if "person" in data:
                e["Person"] = data["person"]
            if "amount" in data:
                try:
                    e["Amount"] = str(float(data["amount"]))
                except (ValueError, TypeError):
                    return jsonify({"success": False, "error": "Invalid amount"}), 400
            if "description" in data:
                e["Description"] = data["description"].replace(",", " - ").strip()
            break

    if not found:
        return jsonify({"success": False, "error": "Entry not found"}), 404

    updated_entries = process_and_save_entries(entries)
    return jsonify({"success": True, "entries": updated_entries})

@app.route('/api/entries/<seq>', methods=['DELETE'])
def delete_entry(seq):
    entries = load_entries()
    
    new_entries = [e for e in entries if e["Seq"] != seq]
    
    if len(new_entries) == len(entries):
        return jsonify({"success": False, "error": "Entry not found"}), 404

    updated_entries = process_and_save_entries(new_entries)
    return jsonify({"success": True, "entries": updated_entries})

@app.route('/api/git-push', methods=['POST'])
def git_push():
    try:
        subprocess.run(["git", "add", CSV_FILE], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Update tracker data via Web UI"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=True)
        return jsonify({"success": True, "message": "Pushed to GitHub successfully!"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

