import csv
import datetime
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import os

# Set the display for tkinter to avoid errors when running in environments without a display server
# For macOS, this might not be strictly necessary, but it can help in some cases.
# If running in a headless environment, you might need to use a virtual display server like Xvfb.
if os.environ.get('DISPLAY') == '':
    os.environ.__setitem__('DISPLAY', ':0.0')

CSV_FILE = "data.csv"

# --- Functions ---
def load_entries():
    entries = []
    try:
        with open(CSV_FILE, newline="") as f:
            reader = csv.DictReader(f)
            entries = list(reader)
    except FileNotFoundError:
        pass
    return entries

def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    for entry in entries:
        tree.insert("", "end", values=(
            entry["Seq"], entry["Date"], entry["Person"], entry["Type"],
            entry["Amount"], entry["RunningBalance"], entry["Description"]
        ))

def add_entry():
    person = person_var.get().strip()
    entry_type = type_var.get()
    try:
        amount = float(amount_var.get())
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number")
        return
    description = desc_var.get().strip()

    seq = len(entries) + 1
    date = datetime.date.today().strftime("%d-%b-%y")
    balance = float(entries[-1]["RunningBalance"]) if entries else 0
    balance += amount if entry_type == "Contribution" else -amount

    new_entry = {
        "Seq": seq,
        "Date": date,
        "Person": person,
        "Type": entry_type,
        "Amount": amount,
        "RunningBalance": balance,
        "Description": description if entry_type == "Expense" else ""
    }
    entries.append(new_entry)
    refresh_table()

def save_and_push():
    fieldnames = ["Seq","Date","Person","Type","Amount","RunningBalance","Description"]
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)

    try:
        subprocess.run(["git", "add", CSV_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update tracker data"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        messagebox.showinfo("Success", "Data saved and pushed to GitHub")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Git Error", f"Git command failed: {e}")

# --- GUI ---
root = tk.Tk()
root.title("Contribution & Expense Tracker")

frame = tk.Frame(root)
frame.pack(pady=10)

# Input fields
person_var = tk.StringVar()
type_var = tk.StringVar(value="Contribution")
amount_var = tk.StringVar()
desc_var = tk.StringVar()

tk.Label(frame, text="Person/Shop").grid(row=0, column=0)
tk.Entry(frame, textvariable=person_var).grid(row=0, column=1)

tk.Label(frame, text="Type").grid(row=0, column=2)
ttk.Combobox(frame, textvariable=type_var, values=["Contribution","Expense"]).grid(row=0, column=3)

tk.Label(frame, text="Amount").grid(row=1, column=0)
tk.Entry(frame, textvariable=amount_var).grid(row=1, column=1)

tk.Label(frame, text="Description").grid(row=1, column=2)
tk.Entry(frame, textvariable=desc_var).grid(row=1, column=3)

tk.Button(frame, text="Add Entry", command=add_entry).grid(row=2, column=0, columnspan=2, pady=5)
tk.Button(frame, text="Save & Push", command=save_and_push).grid(row=2, column=2, columnspan=2, pady=5)

# Table
cols = ["Seq","Date","Person","Type","Amount","RunningBalance","Description"]
tree = ttk.Treeview(root, columns=cols, show="headings")
for col in cols:
    tree.heading(col, text=col)
    tree.column(col, width=100)
tree.pack(pady=10, fill="x")

# Load initial data
entries = load_entries()
refresh_table()

root.mainloop()

