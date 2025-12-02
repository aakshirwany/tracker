import csv
import datetime
import subprocess

CSV_FILE = "data.csv"

def load_entries():
    try:
        with open(CSV_FILE, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        return []

def display_entries(entries):
    print("\n=== Current Entries ===")
    if not entries:
        print("No entries yet.")
        return
    print(f"{'Seq':<5}{'Date':<12}{'Person/Shop':<20}{'Type':<15}{'Amount':<10}{'Balance':<12}{'Description'}")
    for e in entries:
        print(f"{e['Seq']:<5}{e['Date']:<12}{e['Person']:<20}{e['Type']:<15}{e['Amount']:<10}{e['RunningBalance']:<12}{e['Description']}")
    # Summary line
    total_contrib = sum(float(e["Amount"]) for e in entries if e["Type"].lower() == "contribution")
    total_exp = sum(float(e["Amount"]) for e in entries if e["Type"].lower() == "expense")
    balance = float(entries[-1]["RunningBalance"]) if entries else 0
    print(f"\nSummary → Contributions: {total_contrib}, Expenses: {total_exp}, Current Balance: {balance}")

def save_entries(entries, silent=False):
    """Save entries to CSV. If silent=True, skip confirmation prompt."""
    if not silent:
        confirm = input("Are you sure you want to save changes? (Y/N): ").strip().lower()
        if confirm != "y":
            print("❌ Save cancelled.")
            return
    fieldnames = ["Seq","Date","Person","Type","Amount","RunningBalance","Description"]
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_NONE,   # ✅ no quotes around description
            escapechar="\\"
        )
        writer.writeheader()
        writer.writerows(entries)
    print("✅ Data saved to data.csv")

def push_to_github(entries):
    confirm = input("Are you sure you want to push changes to GitHub? (Y/N): ").strip().lower()
    if confirm != "y":
        print("❌ Push cancelled.")
        return
    # ✅ Always save automatically before pushing (no prompt)
    save_entries(entries, silent=True)
    try:
        subprocess.run(["git", "add", CSV_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update tracker data"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Changes pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")

def sanitize_description(text: str) -> str:
    """Replace commas with ' - ' (space-dash-space)."""
    return text.replace(",", " - ").strip()

def add_entry(entries):
    print("Select Entry Type:")
    print("1. Contribution")
    print("2. Expense")
    print("C. Cancel")
    choice = input("Enter choice (1/2/C): ").strip().lower()

    if choice == "c":
        print("❌ Entry addition cancelled.")
        return entries

    if choice == "1":
        entry_type = "Contribution"
        person = input("Contributor Name: ").strip()
        amount_input = input("Amount: ").strip()
        try:
            amount = float(amount_input)
        except ValueError:
            print("❌ Amount must be a number")
            return entries
        description = ""
    elif choice == "2":
        entry_type = "Expense"
        person = input("Shop Name: ").strip()
        amount_input = input("Amount: ").strip()
        try:
            amount = float(amount_input)
        except ValueError:
            print("❌ Amount must be a number")
            return entries
        description = sanitize_description(input("Description: "))
    else:
        print("❌ Invalid choice")
        return entries

    seq = len(entries) + 1
    date = datetime.date.today().strftime("%d-%b-%y")
    balance = float(entries[-1]["RunningBalance"]) if entries else 0
    balance += amount if entry_type == "Contribution" else -amount

    new_entry = {
        "Seq": str(seq),
        "Date": date,
        "Person": person,
        "Type": entry_type,
        "Amount": str(amount),
        "RunningBalance": str(balance),
        "Description": description
    }

    # Show preview before committing
    print("\nPreview of new entry:")
    print(f"{new_entry['Seq']:<5}{new_entry['Date']:<12}{new_entry['Person']:<20}{new_entry['Type']:<15}{new_entry['Amount']:<10}{new_entry['RunningBalance']:<12}{new_entry['Description']}")
    confirm = input("Do you want to add this entry? (Y/N): ").strip().lower()
    if confirm != "y":
        print("❌ Entry addition cancelled.")
        return entries

    entries.append(new_entry)
    print("✅ Entry added.")
    display_entries(entries)  # immediate refresh
    return entries

def remove_entry(entries):
    seq_to_remove = input("Enter Seq # to remove (or 'C' to cancel): ").strip()
    if seq_to_remove.lower() == "c":
        print("❌ Removal cancelled.")
        return entries
    new_entries = [e for e in entries if e["Seq"] != seq_to_remove]
    if len(new_entries) == len(entries):
        print("❌ No entry found with that Seq #")
    else:
        # ✅ Properly indented block
        balance = 0
        for i, e in enumerate(new_entries, start=1):
            e["Seq"] = str(i)
            amt = float(e["Amount"])
            balance += amt if e["Type"].lower() == "contribution" else -amt
            e["RunningBalance"] = str(balance)
        print("✅ Entry removed.")
        display_entries(new_entries)  # immediate refresh
    return new_entries

def main():
    entries = load_entries()
    while True:
        display_entries(entries)
        print("\nOptions: [A]dd entry  [R]emove entry  [S]ave  [P]ush to GitHub  [Q]uit")
        choice = input("Choose an option: ").strip().lower()
        if choice == "a":
            entries = add_entry(entries)
        elif choice == "r":
            entries = remove_entry(entries)
        elif choice == "s":
            save_entries(entries)
        elif choice == "p":
            push_to_github(entries)
        elif choice == "q":
            break
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    main()

