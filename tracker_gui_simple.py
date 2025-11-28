import csv
import datetime
import subprocess
import PySimpleGUI as sg

CSV_FILE = "data.csv"

def load_entries():
    try:
        with open(CSV_FILE, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        return []

def save_entries(entries):
    fieldnames = ["Seq","Date","Person","Type","Amount","RunningBalance","Description"]
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)

def push_to_github():
    try:
        subprocess.run(["git", "add", CSV_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update tracker data"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        sg.popup("✅ Data saved and pushed to GitHub")
    except subprocess.CalledProcessError as e:
        sg.popup_error(f"Git command failed: {e}")

# Load initial data
entries = load_entries()

# Define layout
layout = [
    [sg.Text("Person/Shop"), sg.Input(key="person"),
     sg.Text("Type"), sg.Combo(["Contribution","Expense"], default_value="Contribution", key="type")],
    [sg.Text("Amount"), sg.Input(key="amount"),
     sg.Text("Description"), sg.Input(key="desc")],
    [sg.Button("Add Entry"), sg.Button("Save & Push")],
    [sg.Table(values=[[e["Seq"], e["Date"], e["Person"], e["Type"], e["Amount"], e["RunningBalance"], e["Description"]] for e in entries],
              headings=["Seq","Date","Person","Type","Amount","Balance","Description"],
              key="table", auto_size_columns=True, justification="center", expand_x=True, expand_y=True)]
]

window = sg.Window("Contribution & Expense Tracker", layout, resizable=True)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    elif event == "Add Entry":
        try:
            amount = float(values["amount"])
        except ValueError:
            sg.popup_error("Amount must be a number")
            continue

        seq = len(entries) + 1
        date = datetime.date.today().strftime("%d-%b-%y")
        balance = float(entries[-1]["RunningBalance"]) if entries else 0
        balance += amount if values["type"] == "Contribution" else -amount

        new_entry = {
            "Seq": seq,
            "Date": date,
            "Person": values["person"],
            "Type": values["type"],
            "Amount": amount,
            "RunningBalance": balance,
            "Description": values["desc"] if values["type"] == "Expense" else ""
        }
        entries.append(new_entry)
        window["table"].update(values=[[e["Seq"], e["Date"], e["Person"], e["Type"], e["Amount"], e["RunningBalance"], e["Description"]] for e in entries])
    elif event == "Save & Push":
        save_entries(entries)
        push_to_github()

window.close()

